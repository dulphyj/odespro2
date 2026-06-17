import os

STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./docapp.db"
)
