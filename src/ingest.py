from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "sources"
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


def _check_rows(frame: pd.DataFrame, expected: int, source: str) -> None:
    if len(frame) != expected:
        raise ValueError(f"{source}: expected {expected} rows, found {len(frame)}")


def read_web() -> pd.DataFrame:
    raw = pd.read_csv(SOURCES / "web_orders_2025.csv")
    _check_rows(raw, 1900, "web source")
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
    _check_rows(pd.DataFrame(calls), 96, "phone source")

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
    _check_rows(raw, 1088, "CRM source")
    if raw["Customer ID"].duplicated(keep=False).sum() != 54:
        raise ValueError("CRM source: expected 27 duplicated customer records")

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
    return frame.drop_duplicates("customer_id", keep="first")


def main() -> None:
    web = read_web()
    phone = read_phone()
    orders = pd.concat([web, phone], ignore_index=True)
    _check_rows(orders, 1996, "combined orders")

    crm = read_crm()
    if crm["customer_id"].nunique() != 1061:
        raise ValueError("CRM source: expected 1061 unique customers")

    # The 1,996 source orders each have one CRM record after duplicate resolution.
    joined = orders.merge(crm, on="customer_id", how="left", validate="many_to_one")
    _check_rows(joined, 1996, "joined orders")
    if joined["customer_region"].isna().any():
        raise ValueError("joined orders: customer records are missing")

    OUT.mkdir(exist_ok=True)
    report = {
        "web": {"rows": len(web)},
        "phone": {"rows": len(phone)},
        "crm": {"rows_read": 1088, "unique_customers": len(crm)},
        "join": {"rows": len(joined), "missing_customers": int(joined["customer_region"].isna().sum())},
    }
    (OUT / "ingest_report.json").write_text(json.dumps(report, indent=2) + "\n")
    joined.to_csv(OUT / "orders_joined.csv", index=False)


if __name__ == "__main__":
    main()
