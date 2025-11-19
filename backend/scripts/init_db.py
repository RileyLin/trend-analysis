"""Initialize database tables."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import init_db, engine
from sqlalchemy import text


def create_pgvector_extension():
    """Create pgvector extension if it doesn't exist."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("✓ pgvector extension created/verified")
    except Exception as e:
        print(f"Warning: Could not create pgvector extension: {e}")
        print("  (This is OK if you're using SQLite for testing)")


def main():
    """Initialize database."""
    print("Initializing database...")

    # Create pgvector extension
    create_pgvector_extension()

    # Create all tables
    init_db()

    print("\n✓ Database initialized successfully!")
    print("\nNext steps:")
    print("  1. Run seed scripts to populate initial data:")
    print("     python scripts/seed_glossary.py")
    print("     python scripts/seed_instruments.py")
    print("  2. Start the API server:")
    print("     uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
