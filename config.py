import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    _has_dotenv = True
except ImportError:
    _has_dotenv = False

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables if .env exists
env_path = BASE_DIR / ".env"
if _has_dotenv and env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "health_supply_ai")
SQLITE_PATH = BASE_DIR / "database" / "health_supply.db"

if DB_TYPE == "mysql" and DB_USER:
    # MySQL connection string using pymysql
    DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    # SQLite connection string fallback
    DATABASE_URI = f"sqlite:///{SQLITE_PATH.as_posix()}"

# Machine Learning Configuration
ML_DIR = BASE_DIR / "models"
MODEL_PATH = ML_DIR / "random_forest_demand_model.joblib"
METRICS_PATH = ML_DIR / "model_metrics.json"
FEATURE_NAMES_PATH = ML_DIR / "feature_names.json"

# Data paths
DATA_DIR = BASE_DIR / "data"
SYNTHETIC_DATA_PATH = DATA_DIR / "synthetic_pharmacy_sales.csv"

# App Metadata
APP_TITLE = "Health Supply AI"
APP_SUBTITLE = "Medicine Demand Prediction & Smart Restocking"
ACADEMIC_BATCH = "Batch 24MPCSD-B07 | Vardhaman College of Engineering"
