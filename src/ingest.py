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
    return expect(frame[ORDER_COLUMNS], 1900, "web orders")


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
        "GIFT_VOUCHER": "gift_voucher",
    }
    rows = []
    for call in calls:
        order = call["order"]
        line = order["line"]
        rows.append(
            {
                "order_id": order["ref"],
                "order_date": call["logged_at"].split("T", 1)[0],
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
    return expect(pd.DataFrame(rows, columns=ORDER_COLUMNS), 96, "phone orders")


def read_crm() -> pd.DataFrame:
    raw = pd.read_excel(SOURCES / "crm_customers.xlsx", skiprows=2)
    expect(raw, 1088, "CRM source")
    region_map = {
        "london": "London",
        "midlands": "Midlands",
        "north": "North",
        "south": "South",
        "scotland": "Scotland",
        "wales": "Wales",
        "ni": "NI",
    }
    frame = pd.DataFrame(
        {
            "customer_id": raw["Customer ID"].astype("int64"),
            "customer_region": raw["Region"].str.strip().str.lower().map(region_map),
            "customer_tenure_days": raw["Tenure (days)"].astype("int64"),
            "marketing_opt_in": raw["Marketing Opt-In"].map(
                {"Yes": True, "No": False}
            ),
        }
    )
    return expect(frame, 1088, "CRM customers")


def main() -> None:
    web = read_web()
    phone = read_phone()
    orders = pd.concat([web, phone], ignore_index=True)
    orders = expect(orders, 1996, "combined orders")
    crm = read_crm()
    duplicated_ids = crm.loc[
        crm["customer_id"].duplicated(keep=False), "customer_id"
    ].nunique()
    duplicated_orders = int(orders["customer_id"].isin(
        crm.loc[crm["customer_id"].duplicated(keep=False), "customer_id"]
    ).sum())
    if duplicated_ids != 27:
        raise RowCountError(
            f"CRM duplicated customers: expected 27, got {duplicated_ids}"
        )
    if duplicated_orders != 34:
        raise RowCountError(f"orders for duplicated customers: expected 34, got {duplicated_orders}")

    try:
        orders.merge(crm, on="customer_id", how="left", validate="many_to_one")
    except pd.errors.MergeError:
        pass
    else:
        raise RowCountError("CRM duplicate check: many_to_one unexpectedly succeeded")

    # Keep the first CRM row for each customer so the join remains many-to-one.
    one_each = crm.drop_duplicates("customer_id", keep="first")
    joined = orders.merge(one_each, on="customer_id", how="left", validate="many_to_one")
    joined = expect(joined, 1996, "join")

    operations_join = orders.merge(crm, on="customer_id", how="left")
    operations_join = expect(operations_join, 2030, "operations join")

    week1 = pd.read_csv(
        WEEK1,
        parse_dates=["order_date"],
    )
    week1["order_date"] = week1["order_date"].dt.date
    operations_join["order_date"] = pd.to_datetime(
        operations_join["order_date"]
    ).dt.date
    shared = [column for column in week1.columns if column in operations_join.columns]
    differing = {}
    for column in shared:
        left = operations_join.sort_values("order_id", kind="stable")[column].reset_index(drop=True)
        right = week1.sort_values("order_id", kind="stable")[column].reset_index(drop=True)
        if pd.api.types.is_float_dtype(left) or pd.api.types.is_float_dtype(right):
            matches = np.isclose(left, right, equal_nan=True)
        else:
            matches = left.eq(right) | (left.isna() & right.isna())
        mismatch_count = int((~matches).sum())
        if mismatch_count:
            differing[column] = mismatch_count
    matching_columns = len(shared) - len(differing)
    print(f"join {len(joined)}")
    print(f"as operations ran it {len(operations_join)}")
    print(
        f"against Week 1: {matching_columns} of {len(shared)} columns match, "
        f"differing {differing}"
    )

    OUT.mkdir(exist_ok=True)
    report = {
        "web": {"rows": 1900},
        "phone": {"rows": 96},
        "orders": {"rows": len(orders)},
        "crm": {
            "rows": len(crm),
            "customers": int(crm["customer_id"].nunique()),
            "duplicated_customers": duplicated_ids,
        },
        "duplicated_customer_orders": duplicated_orders,
        "join": {"rows": len(joined)},
        "operations_join": {"rows": len(operations_join)},
        "week1_comparison": {
            "matching_columns": matching_columns,
            "shared_columns": len(shared),
            "differing": differing,
        },
    }
    (OUT / "ingest_report.json").write_text(json.dumps(report, indent=2) + "\n")
    joined.to_csv(OUT / "orders_joined.csv", index=False)
    print(f"web {len(web)} phone {len(phone)} orders {len(orders)} crm {len(crm)}")


if __name__ == "__main__":
    main()
