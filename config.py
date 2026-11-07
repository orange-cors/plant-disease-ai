import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_MODE = os.getenv("DB_MODE", "auto").lower()
MSSQL_SERVER = os.getenv("MSSQL_SERVER", "localhost")
MSSQL_DATABASE = os.getenv("MSSQL_DATABASE", "TramXanhDB")
MSSQL_DRIVER = os.getenv("MSSQL_DRIVER", "SQL Server")
DATABASE_URL_ENV = os.getenv("DATABASE_URL", "")
SQLITE_PATH = BASE_DIR / os.getenv("SQLITE_PATH", "tramxanh.db")

MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "resnet18_phase2_best.pth"))
if not os.path.isabs(MODEL_PATH):
    MODEL_PATH = str(BASE_DIR / MODEL_PATH)

IMAGE_SIZE_INT = int(os.getenv("IMAGE_SIZE", "224"))
IMAGE_SIZE = (IMAGE_SIZE_INT, IMAGE_SIZE_INT)
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.50"))

SECRET_KEY = os.getenv("SECRET_KEY", "tramxanh-secret-key-2026-dong-bang-song-hong")
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

