"""SQLAlchemy engine and request-session helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a future FastAPI request dependency."""
    database_session = SessionLocal()
    try:
        yield database_session
    finally:
        database_session.close()
