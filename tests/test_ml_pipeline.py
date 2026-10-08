import os
import sys
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from config import MODEL_PATH, METRICS_PATH
from ml.feature_engineering import create_demand_features
from ml.predictor import predictor
from ml.train_model import train_demand_forecasting_model


def test_feature_engineering():
    # Create mini sample dataframe
    dates = pd.date_range(start="2026-01-01", periods=45, freq="D")
    sample_sales = pd.DataFrame({
        "sales_id": range(1, 46),
        "medicine_id": [1] * 45,
        "sale_date": dates,
        "quantity_sold": [20 + (i % 7) for i in range(45)]
    })

    feat_df, cols = create_demand_features(sample_sales)
    assert not feat_df.empty, "Feature dataframe should not be empty"
    assert "lag_1" in cols, "lag_1 should be in feature columns"
    assert "rolling_mean_7" in cols, "rolling_mean_7 should be in feature columns"
    assert not feat_df[cols].isnull().any().any(), "Features should not contain NaN values"
    print("✓ test_feature_engineering PASSED")


def test_model_training_and_metrics():
    metrics = train_demand_forecasting_model(test_days=30)
    assert MODEL_PATH.exists(), "Model file should exist after training"
    assert METRICS_PATH.exists(), "Metrics file should exist after training"

    rf_metrics = metrics["random_forest"]
    assert rf_metrics["mae"] > 0, "MAE must be positive"
    assert rf_metrics["rmse"] > 0, "RMSE must be positive"
    assert rf_metrics["r2_score"] is not None, "R2 must be calculated"
    print(f"✓ test_model_training_and_metrics PASSED (MAE={rf_metrics['mae']:.2f}, RMSE={rf_metrics['rmse']:.2f}, R2={rf_metrics['r2_score']:.3f})")


def test_predictor_forecast():
    res_7 = predictor.predict_demand(medicine_id=1, forecast_days=7)
    assert res_7["total_predicted_demand"] > 0, "Predicted demand should be positive"
    assert len(res_7["daily_forecasts"]) == 7, "Should return 7 daily forecasts"

    res_14 = predictor.predict_demand(medicine_id=1, forecast_days=14)
    assert len(res_14["daily_forecasts"]) == 14, "Should return 14 daily forecasts"

    print("✓ test_predictor_forecast PASSED")


if __name__ == "__main__":
    test_feature_engineering()
    test_model_training_and_metrics()
    test_predictor_forecast()
