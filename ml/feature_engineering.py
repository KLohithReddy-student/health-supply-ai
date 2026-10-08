import numpy as np
import pandas as pd


def create_demand_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Transforms raw sales records into supervised learning feature vectors for demand forecasting.
    Includes lag features, rolling statistics, calendar indicators, and medicine attributes.
    Strictly avoids future data leakage by only using past information (shift >= 1).
    """
    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df = df.sort_values(by=["medicine_id", "sale_date"]).reset_index(drop=True)

    # 1. Calendar & Temporal Features
    df["dayofweek"] = df["sale_date"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["day"] = df["sale_date"].dt.day
    df["month"] = df["sale_date"].dt.month
    df["quarter"] = df["sale_date"].dt.quarter
    df["dayofyear"] = df["sale_date"].dt.dayofyear
    df["is_month_start"] = (df["day"] <= 5).astype(int)
    df["is_month_end"] = (df["day"] >= 27).astype(int)

    # 2. Cyclical seasonality features (sin/cos encoding)
    df["sin_dayofyear"] = np.sin(2 * np.pi * df["dayofyear"] / 365.25)
    df["cos_dayofyear"] = np.cos(2 * np.pi * df["dayofyear"] / 365.25)
    df["sin_month"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * df["month"] / 12.0)

    # 3. Lag Features (per medicine) - shifted by at least 1 day to prevent leakage
    grouped = df.groupby("medicine_id")["quantity_sold"]

    df["lag_1"] = grouped.shift(1)
    df["lag_2"] = grouped.shift(2)
    df["lag_3"] = grouped.shift(3)
    df["lag_7"] = grouped.shift(7)
    df["lag_14"] = grouped.shift(14)
    df["lag_30"] = grouped.shift(30)

    # 4. Rolling Statistics (per medicine) over historical windows (shifted by 1)
    df["rolling_mean_7"] = grouped.transform(lambda x: x.shift(1).rolling(7, min_periods=3).mean())
    df["rolling_std_7"] = grouped.transform(lambda x: x.shift(1).rolling(7, min_periods=3).std().fillna(0))
    df["rolling_mean_14"] = grouped.transform(lambda x: x.shift(1).rolling(14, min_periods=7).mean())
    df["rolling_mean_30"] = grouped.transform(lambda x: x.shift(1).rolling(30, min_periods=14).mean())
    df["rolling_max_7"] = grouped.transform(lambda x: x.shift(1).rolling(7, min_periods=3).max())
    df["rolling_min_7"] = grouped.transform(lambda x: x.shift(1).rolling(7, min_periods=3).min())

    # 5. Short-term Trend Indicator (Ratio of 7-day to 30-day demand)
    df["demand_momentum"] = (df["rolling_mean_7"] + 1.0) / (df["rolling_mean_30"] + 1.0)

    # Drop early rows with NaN from 30-day lags
    clean_df = df.dropna().reset_index(drop=True)

    feature_cols = [
        "medicine_id",
        "dayofweek",
        "is_weekend",
        "day",
        "month",
        "quarter",
        "is_month_start",
        "is_month_end",
        "sin_dayofyear",
        "cos_dayofyear",
        "sin_month",
        "cos_month",
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_std_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_max_7",
        "rolling_min_7",
        "demand_momentum"
    ]

    return clean_df, feature_cols
