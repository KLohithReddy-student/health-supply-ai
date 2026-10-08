import json
import logging
from datetime import date, timedelta
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from config import MODEL_PATH, FEATURE_NAMES_PATH, METRICS_PATH
from database.connection import get_db
from database.models import Medicine, SalesRecord
from ml.feature_engineering import create_demand_features

logger = logging.getLogger(__name__)


class DemandPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = None
        self.metrics = None
        self._load_model()

    def _load_model(self):
        """Loads trained Random Forest model and feature column names."""
        if MODEL_PATH.exists() and FEATURE_NAMES_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                with open(FEATURE_NAMES_PATH, "r") as f:
                    self.feature_names = json.load(f)
                if METRICS_PATH.exists():
                    with open(METRICS_PATH, "r") as f:
                        self.metrics = json.load(f)
                logger.info("Random Forest Demand Predictor loaded successfully.")
            except Exception as e:
                logger.warning(f"Error loading model artifacts: {e}. Will fallback to dynamic training.")
                self.model = None
        else:
            logger.info("Model artifacts not yet found on disk.")

    def is_model_ready(self) -> bool:
        return self.model is not None and self.feature_names is not None

    def get_model_metrics(self) -> dict:
        if self.metrics:
            return self.metrics
        if METRICS_PATH.exists():
            with open(METRICS_PATH, "r") as f:
                self.metrics = json.load(f)
            return self.metrics
        return {}

    def predict_demand(self, medicine_id: int, forecast_days: int = 7) -> dict:
        """
        Generates day-by-day demand forecasts for a specific medicine over the given horizon.
        Uses recursive time-series forecasting with the Random Forest model.
        """
        if not self.is_model_ready():
            # Attempt to reload or train
            self._load_model()
            if not self.is_model_ready():
                from ml.train_model import train_demand_forecasting_model
                logger.info("Training model on-demand...")
                train_demand_forecasting_model()
                self._load_model()

        with get_db() as session:
            med = session.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
            if not med:
                raise ValueError(f"Medicine with ID {medicine_id} not found.")

            # Fetch recent sales history (at least 45 days)
            recent_sales = (
                session.query(SalesRecord)
                .filter(SalesRecord.medicine_id == medicine_id)
                .order_by(SalesRecord.sale_date.desc())
                .limit(60)
                .all()
            )

            if not recent_sales:
                daily_estimate = max(1.0, float(med.reorder_level) / 7.0)
                return {
                    "medicine_id": med.medicine_id,
                    "medicine_name": med.medicine_name,
                    "forecast_period": forecast_days,
                    "total_predicted_demand": int(round(daily_estimate * forecast_days)),
                    "daily_forecasts": [
                        {"date": (date.today() + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                         "predicted_demand": round(daily_estimate, 1)}
                        for i in range(forecast_days)
                    ],
                    "model_used": "Cold-Start Baseline (Insufficient History)"
                }

            # Extract sales data before session closes
            sales_data = [
                {
                    "medicine_id": s.medicine_id,
                    "sale_date": pd.to_datetime(s.sale_date),
                    "quantity_sold": s.quantity_sold
                }
                for s in reversed(recent_sales)
            ]
            med_id = med.medicine_id
            med_name = med.medicine_name
            med_cat = med.category
            med_stock = med.current_stock
            med_reorder = med.reorder_level
            med_lead = med.lead_time

        # Format history as DataFrame
        history_df = pd.DataFrame(sales_data)

        # Recursive Multi-Step Forecast
        daily_forecasts = []
        last_date = history_df["sale_date"].max()

        working_df = history_df.copy()

        for step in range(1, forecast_days + 1):
            future_date = last_date + pd.Timedelta(days=step)

            # Build feature vector for future_date using working_df
            temp_record = pd.DataFrame([{
                "medicine_id": medicine_id,
                "sale_date": future_date,
                "quantity_sold": np.nan  # Target to predict
            }])

            combined_df = pd.concat([working_df, temp_record], ignore_index=True)
            feat_df, cols = create_demand_features(combined_df)

            if feat_df.empty:
                # Fallback to rolling average if feature window has NaN
                pred_val = float(working_df["quantity_sold"].tail(7).mean())
            else:
                last_row = feat_df[cols].iloc[[-1]]
                pred_val = float(self.model.predict(last_row)[0])
                pred_val = max(0.0, pred_val)

            daily_forecasts.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_demand": round(pred_val, 1)
            })

            # Update working_df with predicted value for subsequent steps
            temp_record["quantity_sold"] = round(pred_val, 1)
            working_df = pd.concat([working_df, temp_record], ignore_index=True)

        total_predicted = int(round(sum(d["predicted_demand"] for d in daily_forecasts)))

        return {
            "medicine_id": med_id,
            "medicine_name": med_name,
            "category": med_cat,
            "current_stock": med_stock,
            "reorder_level": med_reorder,
            "lead_time": med_lead,
            "forecast_period": forecast_days,
            "total_predicted_demand": total_predicted,
            "average_daily_demand": round(total_predicted / forecast_days, 1),
            "daily_forecasts": daily_forecasts,
            "model_used": "Random Forest Regressor"
        }


# Singleton instance
predictor = DemandPredictor()
