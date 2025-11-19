"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/thesis_ticker_engine")

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for development
    echo=True if os.getenv("API_DEBUG", "True") == "True" else False
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    # Import models to register them
    from app.models import thesis, instrument, alert, portfolio, glossary

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped!")
