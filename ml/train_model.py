import json
import logging
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import ML_DIR, MODEL_PATH, METRICS_PATH, FEATURE_NAMES_PATH
from database.connection import get_db
from database.models import SalesRecord, Medicine
from ml.feature_engineering import create_demand_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_sales_data_from_db() -> pd.DataFrame:
    """Loads all sales history joined with medicine metadata from database."""
    with get_db() as session:
        records = (
            session.query(
                SalesRecord.sales_id,
                SalesRecord.medicine_id,
                SalesRecord.sale_date,
                SalesRecord.quantity_sold,
                Medicine.medicine_name,
                Medicine.category,
                Medicine.unit_price,
                Medicine.lead_time,
                Medicine.reorder_level
            )
            .join(Medicine, SalesRecord.medicine_id == Medicine.medicine_id)
            .order_by(SalesRecord.medicine_id, SalesRecord.sale_date)
            .all()
        )

        data = [
            {
                "sales_id": r.sales_id,
                "medicine_id": r.medicine_id,
                "sale_date": r.sale_date,
                "quantity_sold": r.quantity_sold,
                "medicine_name": r.medicine_name,
                "category": r.category,
                "unit_price": r.unit_price,
                "lead_time": r.lead_time,
                "reorder_level": r.reorder_level
            }
            for r in records
        ]

    df = pd.DataFrame(data)
    return df


def train_demand_forecasting_model(test_days: int = 60) -> dict:
    """
    Trains the Random Forest Demand Prediction Model using a temporal train/test split.
    Calculates MAE, RMSE, and feature importances, and persists the model artifacts.
    """
    logger.info("Loading sales data for model training...")
    raw_df = load_sales_data_from_db()
    if raw_df.empty:
        raise ValueError("No sales records found in database. Seed or import data first.")

    # 1. Feature Engineering
    feature_df, feature_cols = create_demand_features(raw_df)
    logger.info(f"Engineered {len(feature_cols)} features across {len(feature_df)} samples.")

    # 2. Temporal Train/Test Split (Avoid Data Leakage)
    max_date = feature_df["sale_date"].max()
    split_date = max_date - pd.Timedelta(days=test_days)

    train_mask = feature_df["sale_date"] <= split_date
    test_mask = feature_df["sale_date"] > split_date

    train_data = feature_df[train_mask]
    test_data = feature_df[test_mask]

    X_train = train_data[feature_cols]
    y_train = train_data["quantity_sold"]

    X_test = test_data[feature_cols]
    y_test = test_data["quantity_sold"]

    logger.info(f"Temporal Split: Train shape={X_train.shape} (up to {split_date.strftime('%Y-%m-%d')}), "
                f"Test shape={X_test.shape} (after {split_date.strftime('%Y-%m-%d')})")

    # 3. Fit Random Forest Regressor (Primary Proposed Model)
    rf_model = RandomForestRegressor(
        n_estimators=120,
        max_depth=14,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    # 4. Fit Baseline Linear Regression for comparison
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)

    # 5. Evaluate Predictions on Test Set
    rf_preds = rf_model.predict(X_test)
    lr_preds = lr_model.predict(X_test)

    rf_mae = float(mean_absolute_error(y_test, rf_preds))
    rf_mse = float(mean_squared_error(y_test, rf_preds))
    rf_rmse = float(np.sqrt(rf_mse))
    rf_r2 = float(r2_score(y_test, rf_preds))

    lr_mae = float(mean_absolute_error(y_test, lr_preds))
    lr_rmse = float(np.sqrt(mean_squared_error(y_test, lr_preds)))
    lr_r2 = float(r2_score(y_test, lr_preds))

    # 6. Feature Importances
    importances = rf_model.feature_importances_
    feature_importance_list = sorted(
        [{"feature": col, "importance": round(float(imp), 4)} for col, imp in zip(feature_cols, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )

    # 7. Sample Actual vs Predicted records for dashboard visualization
    test_eval_df = test_data[["sale_date", "medicine_id", "quantity_sold"]].copy()
    test_eval_df["predicted_sold"] = np.round(rf_preds, 1)
    test_eval_df["baseline_predicted"] = np.round(lr_preds, 1)

    eval_samples = test_eval_df.tail(120).to_dict(orient="records")
    for s in eval_samples:
        s["sale_date"] = s["sale_date"].strftime("%Y-%m-%d")

    # 8. Save Artifacts
    ML_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rf_model, MODEL_PATH)

    metrics = {
        "model_type": "Random Forest Regressor",
        "trained_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "training_samples": len(train_data),
        "test_samples": len(test_data),
        "split_date": split_date.strftime("%Y-%m-%d"),
        "random_forest": {
            "mae": round(rf_mae, 3),
            "rmse": round(rf_rmse, 3),
            "r2_score": round(rf_r2, 3)
        },
        "baseline_linear_regression": {
            "mae": round(lr_mae, 3),
            "rmse": round(lr_rmse, 3),
            "r2_score": round(lr_r2, 3)
        },
        "feature_importances": feature_importance_list,
        "sample_evaluations": eval_samples
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    with open(FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_cols, f, indent=2)

    logger.info(f"Model saved successfully to {MODEL_PATH}")
    logger.info(f"Evaluation Metrics: Random Forest MAE={rf_mae:.2f}, RMSE={rf_rmse:.2f}, R2={rf_r2:.3f}")
    logger.info(f"Comparison: Linear Regression MAE={lr_mae:.2f}, RMSE={lr_rmse:.2f}, R2={lr_r2:.3f}")

    return metrics


if __name__ == "__main__":
    train_demand_forecasting_model()
