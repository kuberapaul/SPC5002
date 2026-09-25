from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "retail_orders_week1.csv"
SKIP_COLUMNS = {"order_id", "order_date", "customer_id", "returned"}


def model_for_column(column: str, is_numeric: bool) -> Pipeline:
    if is_numeric:
        preprocessor = ColumnTransformer(
            [("numeric", StandardScaler(), [column])]
        )
    else:
        preprocessor = ColumnTransformer(
            [
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore"),
                    [column],
                )
            ]
        )

    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=2000)),
        ]
    )


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    y = df["returned"]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
    results = []

    for column in df.columns:
        if column in SKIP_COLUMNS:
            continue

        is_numeric = pd.api.types.is_numeric_dtype(df[column]) and not pd.api.types.is_bool_dtype(df[column])
        model = model_for_column(column, is_numeric)
        scores = cross_val_score(
            model,
            df[[column]],
            y,
            cv=folds,
            scoring="roc_auc",
        )
        results.append((column, scores.mean(), scores.std()))

    results_table = pd.DataFrame(
        results, columns=["column", "roc_auc_cv", "std"]
    ).sort_values("roc_auc_cv", ascending=False)
    print(results_table[["column", "roc_auc_cv"]].to_string(index=False))


if __name__ == "__main__":
    main()
