import math
import random
from datetime import datetime, date, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from config import SYNTHETIC_DATA_PATH, DATA_DIR

# Define realistic pharmacy catalog
MEDICINE_CATALOG = [
    {
        "medicine_id": 1,
        "medicine_name": "Paracetamol 650mg (Dolo)",
        "category": "Analgesic / Antipyretic",
        "current_stock": 45,
        "reorder_level": 80,
        "unit_price": 32.50,
        "lead_time": 2,
        "expiry_months_ahead": 14,
        "base_daily_demand": 38,
        "seasonality_type": "flu_winter_monsoon",
        "supplier": "Apex Pharma Distributors"
    },
    {
        "medicine_id": 2,
        "medicine_name": "Amoxicillin 500mg",
        "category": "Antibiotic",
        "current_stock": 18,
        "reorder_level": 50,
        "unit_price": 78.00,
        "lead_time": 3,
        "expiry_months_ahead": 8,
        "base_daily_demand": 22,
        "seasonality_type": "bacterial_infection",
        "supplier": "Cipla Logistics Hub"
    },
    {
        "medicine_id": 3,
        "medicine_name": "Metformin 500mg",
        "category": "Antidiabetic",
        "current_stock": 120,
        "reorder_level": 70,
        "unit_price": 45.00,
        "lead_time": 4,
        "expiry_months_ahead": 18,
        "base_daily_demand": 30,
        "seasonality_type": "chronic_steady",
        "supplier": "Sun Pharma Wholesale"
    },
    {
        "medicine_id": 4,
        "medicine_name": "Cetirizine 10mg",
        "category": "Antihistamine / Allergy",
        "current_stock": 15,  # Low stock test case
        "reorder_level": 40,
        "unit_price": 25.00,
        "lead_time": 2,
        "expiry_months_ahead": 2,  # Expiry risk test case! (expiring within ~60 days)
        "base_daily_demand": 18,
        "seasonality_type": "allergy_spring_monsoon",
        "supplier": "Apex Pharma Distributors"
    },
    {
        "medicine_id": 5,
        "medicine_name": "Azithromycin 500mg",
        "category": "Antibiotic",
        "current_stock": 35,
        "reorder_level": 40,
        "unit_price": 115.00,
        "lead_time": 3,
        "expiry_months_ahead": 12,
        "base_daily_demand": 16,
        "seasonality_type": "respiratory_winter",
        "supplier": "Cipla Logistics Hub"
    },
    {
        "medicine_id": 6,
        "medicine_name": "Atorvastatin 20mg",
        "category": "Cardiovascular",
        "current_stock": 90,
        "reorder_level": 50,
        "unit_price": 85.00,
        "lead_time": 4,
        "expiry_months_ahead": 20,
        "base_daily_demand": 24,
        "seasonality_type": "chronic_steady",
        "supplier": "Lupin Meds Direct"
    },
    {
        "medicine_id": 7,
        "medicine_name": "Pantoprazole 40mg",
        "category": "Antacid / Gastrointestinal",
        "current_stock": 65,
        "reorder_level": 60,
        "unit_price": 55.00,
        "lead_time": 3,
        "expiry_months_ahead": 15,
        "base_daily_demand": 28,
        "seasonality_type": "steady_slight_holiday",
        "supplier": "Sun Pharma Wholesale"
    },
    {
        "medicine_id": 8,
        "medicine_name": "Cough Syrup 100ml (Ascoril)",
        "category": "Respiratory / Antitussive",
        "current_stock": 12,  # Low stock!
        "reorder_level": 45,
        "unit_price": 105.00,
        "lead_time": 3,
        "expiry_months_ahead": 10,
        "base_daily_demand": 20,
        "seasonality_type": "flu_winter_monsoon",
        "supplier": "Glenmark Supply Care"
    },
    {
        "medicine_id": 9,
        "medicine_name": "Insulin Glargine 100IU/ml",
        "category": "Antidiabetic / Injectable",
        "current_stock": 8,  # Critical low stock!
        "reorder_level": 25,
        "unit_price": 480.00,
        "lead_time": 5,
        "expiry_months_ahead": 5,
        "base_daily_demand": 7,
        "seasonality_type": "chronic_steady",
        "supplier": "Biocon Bio-Logistics"
    },
    {
        "medicine_id": 10,
        "medicine_name": "ORS Electrolyte Powder Sachets",
        "category": "Hydration / Gastrointestinal",
        "current_stock": 140,
        "reorder_level": 80,
        "unit_price": 18.00,
        "lead_time": 2,
        "expiry_months_ahead": 24,
        "base_daily_demand": 35,
        "seasonality_type": "summer_heatwave",
        "supplier": "Apex Pharma Distributors"
    },
    {
        "medicine_id": 11,
        "medicine_name": "Ibuprofen 400mg",
        "category": "Analgesic / NSAID",
        "current_stock": 70,
        "reorder_level": 50,
        "unit_price": 28.00,
        "lead_time": 2,
        "expiry_months_ahead": 16,
        "base_daily_demand": 19,
        "seasonality_type": "chronic_steady",
        "supplier": "Lupin Meds Direct"
    },
    {
        "medicine_id": 12,
        "medicine_name": "Amlodipine 5mg",
        "category": "Antihypertensive",
        "current_stock": 85,
        "reorder_level": 45,
        "unit_price": 22.00,
        "lead_time": 3,
        "expiry_months_ahead": 22,
        "base_daily_demand": 25,
        "seasonality_type": "chronic_steady",
        "supplier": "Sun Pharma Wholesale"
    }
]


def calculate_seasonal_factor(current_date: date, seasonality_type: str) -> float:
    """
    Computes a realistic seasonal demand multiplier based on day of year.
    """
    day_of_year = current_date.timetuple().tm_yday
    month = current_date.month

    if seasonality_type == "flu_winter_monsoon":
        # Spikes in monsoon (July-Sept: months 7-9) and winter (Nov-Jan: months 11, 12, 1)
        monsoon_peak = math.exp(-((month - 8) ** 2) / 2.0) * 0.45
        winter_peak = (math.exp(-((month - 12) ** 2) / 1.5) + math.exp(-((month - 1) ** 2) / 1.5)) * 0.40
        return 1.0 + monsoon_peak + winter_peak

    elif seasonality_type == "bacterial_infection":
        # Moderate spikes during weather change (monsoon and winter)
        return 1.0 + 0.25 * math.sin(2 * math.pi * (day_of_year - 60) / 182.5)

    elif seasonality_type == "allergy_spring_monsoon":
        # Peaks in spring (Feb-March) and onset of monsoon (July)
        spring_peak = math.exp(-((month - 3) ** 2) / 1.2) * 0.55
        monsoon_peak = math.exp(-((month - 7) ** 2) / 1.2) * 0.40
        return 1.0 + spring_peak + monsoon_peak

    elif seasonality_type == "respiratory_winter":
        # Sharp surge in cold weather (Nov-Feb)
        if month in (11, 12, 1, 2):
            return 1.45 + random.uniform(-0.1, 0.15)
        return 0.85 + random.uniform(-0.05, 0.05)

    elif seasonality_type == "summer_heatwave":
        # ORS and hydration demand peaks in summer (April-June: months 4-6)
        summer_peak = math.exp(-((month - 5) ** 2) / 1.8) * 0.85
        return 0.70 + summer_peak

    elif seasonality_type == "steady_slight_holiday":
        # Slight spike on weekends and festival months (Oct-Nov)
        if month in (10, 11):
            return 1.15
        return 1.0

    else:  # chronic_steady
        # Chronic meds (diabetes, blood pressure) have very stable demand year round, slight refill surge at month start
        if current_date.day <= 5 or current_date.day >= 27:
            return 1.15  # monthly pension/payday refill
        return 1.0


def generate_synthetic_data(num_days: int = 365, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates a realistic 1-year synthetic pharmacy dataset for demonstration and training.
    Returns:
        medicines_df: DataFrame of medicine metadata and stock levels
        sales_df: DataFrame of historical daily sales
    """
    np.random.seed(seed)
    random.seed(seed)

    end_date = date.today()
    start_date = end_date - timedelta(days=num_days - 1)

    date_range = [start_date + timedelta(days=i) for i in range(num_days)]

    # 1. Prepare Medicines DataFrame
    medicines_list = []
    for med in MEDICINE_CATALOG:
        expiry = end_date + timedelta(days=med["expiry_months_ahead"] * 30)
        medicines_list.append({
            "medicine_id": med["medicine_id"],
            "medicine_name": med["medicine_name"],
            "category": med["category"],
            "current_stock": med["current_stock"],
            "reorder_level": med["reorder_level"],
            "unit_price": med["unit_price"],
            "expiry_date": expiry,
            "supplier": med["supplier"],
            "lead_time": med["lead_time"]
        })
    medicines_df = pd.DataFrame(medicines_list)

    # 2. Prepare Sales Records DataFrame
    sales_records = []
    sales_id_counter = 1

    for single_date in date_range:
        day_of_week = single_date.weekday()  # 0=Monday, 6=Sunday
        # Weekend multiplier: pharmacies typically have 15-20% higher traffic on Saturdays
        dow_factor = 1.18 if day_of_week == 5 else (0.85 if day_of_week == 6 else 1.02)

        for med in MEDICINE_CATALOG:
            base = med["base_daily_demand"]
            seasonal_factor = calculate_seasonal_factor(single_date, med["seasonality_type"])

            # Occasional localized demand surge / outbreak spike (2% chance)
            surge_multiplier = 1.65 if random.random() < 0.02 else 1.0

            # Poisson/Normal realistic noise
            mean_demand = base * seasonal_factor * dow_factor * surge_multiplier
            daily_qty = int(max(0, np.random.normal(loc=mean_demand, scale=max(2.0, mean_demand * 0.18))))

            sales_records.append({
                "sales_id": sales_id_counter,
                "medicine_id": med["medicine_id"],
                "medicine_name": med["medicine_name"],
                "category": med["category"],
                "sale_date": single_date,
                "quantity_sold": daily_qty
            })
            sales_id_counter += 1

    sales_df = pd.DataFrame(sales_records)

    # Save to CSV for convenience and transparency
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sales_df.to_csv(SYNTHETIC_DATA_PATH, index=False)

    return medicines_df, sales_df


if __name__ == "__main__":
    med_df, s_df = generate_synthetic_data()
    print(f"Synthetic dataset generated successfully!")
    print(f"Medicines: {len(med_df)} items")
    print(f"Sales records: {len(s_df)} days across all medicines (from {s_df['sale_date'].min()} to {s_df['sale_date'].max()})")
    print(f"Saved to: {SYNTHETIC_DATA_PATH}")
