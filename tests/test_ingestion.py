
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import src.api as api_module


TEST_API_KEY = "test-secret-key-only"


@pytest.fixture
def ingestion_client(monkeypatch):
    # Use an isolated, in-memory SQLite database.
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with test_engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE offers (
                offer_id VARCHAR(50) PRIMARY KEY,
                provider VARCHAR(100) NOT NULL,
                country VARCHAR(100) NOT NULL,
                data_gb FLOAT NOT NULL,
                validity_days INTEGER NOT NULL,
                price_eur NUMERIC(10, 2) NOT NULL
            )
        """))

    # Replace the production database engine.
    monkeypatch.setattr(api_module, "engine", test_engine)

    # Set a safe test-only API key.
    monkeypatch.setenv("IMPORT_API_KEY", TEST_API_KEY)

    with TestClient(api_module.app) as client:
        yield client, test_engine

    test_engine.dispose()


@pytest.fixture
def sample_offer():
    return {
        "offer_id": "TEST001",
        "provider": "GlobalSIM",
        "country": "Italy",
        "data_gb": 10,
        "validity_days": 30,
        "price_eur": 14.99,
    }


def send_import(client, offers, key=TEST_API_KEY):
    return client.post(
        "/offers/import",
        json=offers,
        headers={"x-api-key": key},
    )


def test_successful_import(ingestion_client, sample_offer):
    client, engine = ingestion_client

    response = send_import(client, [sample_offer])

    assert response.status_code == 200
    assert response.json()["processed_offers"] == 1

    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM offers")
        ).scalar_one()

    assert count == 1


def test_invalid_api_key(ingestion_client, sample_offer):
    client, _ = ingestion_client

    response = send_import(
        client,
        [sample_offer],
        key="wrong-key",
    )

    assert response.status_code == 401


def test_missing_api_key(ingestion_client, sample_offer):
    client, _ = ingestion_client

    response = client.post(
        "/offers/import",
        json=[sample_offer],
    )

    assert response.status_code == 401


def test_negative_data_rejected(
    ingestion_client, sample_offer
):
    client, _ = ingestion_client

    invalid_offer = {
        **sample_offer,
        "data_gb": -5,
    }

    response = send_import(client, [invalid_offer])

    assert response.status_code == 422


def test_duplicate_ids_rejected(
    ingestion_client, sample_offer
):
    client, _ = ingestion_client

    response = send_import(
        client,
        [sample_offer, sample_offer],
    )

    assert response.status_code == 400


def test_empty_batch_rejected(ingestion_client):
    client, _ = ingestion_client

    response = send_import(client, [])

    assert response.status_code == 400


def test_upsert_updates_existing_offer(
    ingestion_client, sample_offer
):
    client, engine = ingestion_client

    first_response = send_import(client, [sample_offer])
    assert first_response.status_code == 200

    updated_offer = {
        **sample_offer,
        "price_eur": 9.99,
    }

    second_response = send_import(
        client,
        [updated_offer],
    )
    assert second_response.status_code == 200

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT price_eur
                FROM offers
                WHERE offer_id = 'TEST001'
            """)
        ).all()

    assert len(rows) == 1
    assert float(rows[0][0]) == pytest.approx(9.99)


def test_multiple_offers_imported(
    ingestion_client, sample_offer
):
    client, engine = ingestion_client

    second_offer = {
        **sample_offer,
        "offer_id": "TEST002",
        "country": "Spain",
    }

    response = send_import(
        client,
        [sample_offer, second_offer],
    )

    assert response.status_code == 200
    assert response.json()["processed_offers"] == 2

    with engine.connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM offers")
        ).scalar_one()

    assert count == 2
