"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app
from app.models.glossary import Glossary
from app.models.instrument import Instrument


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed test data
    _seed_test_data(db)

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _seed_test_data(db):
    """Seed test database with minimal data."""
    # Add glossary terms
    glossary_terms = [
        Glossary(key='margin', cn='保证金', en='margin', pinned=True),
        Glossary(key='rating', cn='评级', en='rating', pinned=True),
        Glossary(key='subsidy', cn='补贴', en='subsidy', pinned=True),
    ]

    for term in glossary_terms:
        db.add(term)

    # Add instruments
    instruments = [
        Instrument(
            id='IONQ:NASDAQ',
            symbol='IONQ',
            venue='NASDAQ',
            asset_class='equity',
            display_name_en='IonQ Inc',
            display_name_cn='艾恩Q',
            meta={'themes': ['quantum'], 'geo': 'US'}
        ),
        Instrument(
            id='MP:NYSE',
            symbol='MP',
            venue='NYSE',
            asset_class='equity',
            display_name_en='MP Materials',
            display_name_cn='MP材料',
            meta={'themes': ['rare_earths'], 'geo': 'US'}
        ),
    ]

    for inst in instruments:
        db.add(inst)

    db.commit()
