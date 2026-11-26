import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import create_app
from app.modules.network.service import seed_network


@pytest.fixture()
def engine():
    """SQLite in memory by default. Set KTI_TEST_DATABASE_URL to test on PostgreSQL."""
    url = os.environ.get("KTI_TEST_DATABASE_URL")
    if url:
        eng = create_engine(url)
    else:
        eng = create_engine(
            "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture()
def seeded_db(db):
    seed_network(db)
    db.commit()
    return db


@pytest.fixture()
def client(engine):
    app = create_app()

    def override_get_db():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
