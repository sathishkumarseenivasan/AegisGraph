"""
Database configuration and session management.
"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from config import settings


# Create engine with SQLite-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=settings.DEBUG,
)


def create_db_and_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
