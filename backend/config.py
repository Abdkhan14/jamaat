import os
from zoneinfo import ZoneInfo

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

EASTERN = ZoneInfo("America/Toronto")

class Config:
    DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "prayer_times.db"))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
