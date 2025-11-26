"""
Database Core
Handles database connection, session management, and base model
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions
    Used with FastAPI's Depends()

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database
    Creates all tables defined in models
    Call this on application startup
    """
    # Import all models here so they're registered with Base
    from app.models import database  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("[+] Database initialized successfully")


def drop_db():
    """
    Drop all tables
    USE WITH CAUTION - Only for development/testing
    """
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped")


def reset_db():
    """
    Reset database - drop all tables and recreate
    USE WITH CAUTION - Only for development/testing
    """
    drop_db()
    init_db()
    print("✓ Database reset complete")
