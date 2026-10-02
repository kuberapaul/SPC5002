from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
WEEK1 = ROOT / "data" / "retail_orders_week1.csv"
OUT = ROOT / "outputs"

ORDER_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "channel",
    "category",
    "item_price",
    "quantity",
    "discount_pct",
    "order_value",
    "payment_method",
    "delivery_days",
    "customer_prior_orders",
    "returned",
]


class RowCountError(AssertionError):
    pass


def expect(frame: pd.DataFrame, n: int, what: str) -> pd.DataFrame:
    if len(frame) != n:
        raise RowCountError(f"{what}: expected {n}, got {len(frame)}")
    return frame


def read_web() -> pd.DataFrame:
    raw = pd.read_csv(SOURCES / "web_orders_2025.csv")
    expect(raw, 1900, "web source")
    frame = pd.DataFrame(
        {
            "order_id": raw["Order ID"],
            "order_date": pd.to_datetime(
                raw["Order Date"], format="%d/%m/%Y"
            ).dt.strftime("%Y-%m-%d"),
            "customer_id": raw["Customer ID"].astype("int64"),
            "channel": "web",
            "category": raw["Item Category"].str.strip().str.lower(),
            "item_price": raw["Unit Price (GBP)"].astype("float64"),
            "quantity": raw["Qty"].astype("int64"),
            "discount_pct": raw["Discount %"].astype("int64"),
            "order_value": raw["Order Total (GBP)"].astype("float64"),
            "payment_method": raw["Payment"].str.lower(),
            "delivery_days": raw["Delivery (days)"].astype("int64"),
            "customer_prior_orders": raw["Prior Orders"].astype("int64"),
            "returned": raw["Returned"].map({"Y": 1, "N": 0}).astype("int64"),
        }
    )
    return frame[ORDER_COLUMNS]


def read_phone() -> pd.DataFrame:
    payload = json.loads((SOURCES / "phone_orders_2025.json").read_text())
    calls = payload["calls"]
    expect(pd.DataFrame(calls), 96, "phone source")

    category_map = {
        "Apparel": "apparel",
        "Electronics": "electronics",
        "Home & Garden": "home",
        "Footwear": "footwear",
        "Sports/Outdoor": "sports",
        "Health & Beauty": "beauty",
    }
    payment_map = {
        "CARD": "card",
        "PAYPAL": "paypal",
        "BNPL": "bnpl",
        "GIFT_VOUCHER": "gift_card",
    }
    rows = []
    for call in calls:
        order = call["order"]
        line = order["line"]
        rows.append(
            {
                "order_id": order["ref"],
                "order_date": call["logged_at"],
                "customer_id": int(call["customer"]["crm_id"]),
                "channel": "phone",
                "category": category_map[line["category"].strip()],
                "item_price": int(line["unit_price_pence"]) / 100,
                "quantity": int(line["qty"]),
                "discount_pct": int(order["discount_percent"]),
                "order_value": int(order["total_pence"]) / 100,
                "payment_method": payment_map[order["tender"]],
                "delivery_days": int(order["delivery_days"]),
                "customer_prior_orders": int(call["customer"]["prior_orders"]),
                "returned": int(order["returned"]),
            }
        )
    return pd.DataFrame(rows, columns=ORDER_COLUMNS)


def read_crm() -> pd.DataFrame:
    raw = pd.read_excel(SOURCES / "crm_customers.xlsx", skiprows=2)
    expect(raw, 1088, "CRM source")
    if raw["Customer ID"].duplicated(keep=False).sum() != 54:
        raise RowCountError("CRM source: expected 27 duplicated customer records")

    frame = pd.DataFrame(
        {
            "customer_id": raw["Customer ID"].astype("int64"),
            "customer_region": raw["Region"].str.strip(),
            "customer_tenure_days": raw["Tenure (days)"].astype("int64"),
            "marketing_opt_in": raw["Marketing Opt-In"].map(
                {"Yes": True, "No": False}
            ),
        }
    )
    return expect(
        frame.drop_duplicates("customer_id", keep="first"),
        1061,
        "CRM customers after duplicate resolution",
    )


def main() -> None:
    web = read_web()
    phone = read_phone()
    orders = pd.concat([web, phone], ignore_index=True)
    orders = expect(orders, 1996, "combined orders")

    crm = read_crm()
    if crm["customer_id"].nunique() != 1061:
        raise RowCountError("CRM source: expected 1061 unique customers")

    # The 1,996 source orders each have one CRM record after duplicate resolution.
    joined = orders.merge(crm, on="customer_id", how="left", validate="many_to_one")
    joined = expect(joined, 1996, "joined orders")
    if joined["customer_region"].isna().any():
        raise RowCountError("joined orders: customer records are missing")

    OUT.mkdir(exist_ok=True)
    report = {
        "web": {"rows": len(web), "action": "read and standardised storefront orders"},
        "phone": {"rows": len(phone), "action": "read and standardised call-centre orders"},
        "combined": {"rows": len(orders), "action": "concatenated both order sources"},
        "crm": {
            "rows_read": 1088,
            "unique_customers": len(crm),
            "action": "read spreadsheet, checked duplicates, kept first record",
        },
        "join": {
            "rows": len(joined),
            "missing_customers": int(joined["customer_region"].isna().sum()),
            "action": "many-to-one left join on customer_id",
        },
    }
    (OUT / "ingest_report.json").write_text(json.dumps(report, indent=2) + "\n")
    joined.to_csv(OUT / "orders_joined.csv", index=False)


if __name__ == "__main__":
    main()
