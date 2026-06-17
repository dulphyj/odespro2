from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import DATABASE_URL

_engine_url = DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
engine = create_engine(_engine_url, echo=False)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
