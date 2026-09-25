from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "retail_orders_week1.csv"
OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


def main() -> None:
    seed = 7

    df = pd.read_csv(DATA_PATH)

    features = [
        "item_price",
        "discount_pct",
        "customer_prior_orders",
        "category",
        "channel",
        "payment_method",
    ]
    numeric_features = ["item_price", "discount_pct", "customer_prior_orders"]
    categorical_features = ["category", "channel", "payment_method"]

    X = df[features]
    y = df["returned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=seed,
        stratify=y,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=2000)),
        ]
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    metrics = {
        "seed": seed,
        "n_rows": int(len(df)),
        "base_rate": float(y.mean()),
        "features": features,
        "roc_auc": float(auc),
    }

    output_path = OUTPUTS_DIR / "metrics.json"
    output_path.write_text(json.dumps(metrics, indent=2) + "\n")

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
