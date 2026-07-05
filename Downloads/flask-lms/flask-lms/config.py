"""
config.py
---------
Central configuration. Reads sensitive values from environment variables
(with sensible defaults for local development).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # load .env if present

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    # --- Database (SQLite) ---
    DB_DIR = BASE_DIR / "database"
    DB_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_DIR / 'lms.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB
    ALLOWED_EXTENSIONS = {"pdf"}

    # --- AI (OpenAI-compatible endpoint) ---
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    # --- Default admin (seeded on first run) ---
    DEFAULT_ADMIN_EMAIL = "admin@gmail.com"
    DEFAULT_ADMIN_PASSWORD = "admin123"
    DEFAULT_ADMIN_NAME = "Administrator"
