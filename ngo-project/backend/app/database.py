"""Database configuration: one SQLite file, one engine, one session factory."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# The database file lives next to the "app" folder: backend/ngo.db
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'ngo.db'}"

# check_same_thread=False is needed because FastAPI may use a SQLite
# connection from a different thread than the one that created it.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """All SQLAlchemy models inherit from this class."""


def get_db():
    """FastAPI dependency: gives each request its own session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
