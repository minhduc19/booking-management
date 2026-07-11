from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _ensure_sqlite_parent_directory(database_url: str) -> None:
    """Create the parent directory for file-based SQLite databases."""
    url = make_url(database_url)

    if url.drivername.split("+")[0] != "sqlite":
        return

    database = url.database
    # In-memory SQLite databases do not have a parent directory to create.
    if database in (None, "", ":memory:"):
        return

    Path(database).expanduser().parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
