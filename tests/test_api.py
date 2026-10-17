
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

import src.api as api_module


@pytest.fixture
def client(monkeypatch):
    """Create an isolated test database and API client."""

    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create the test table.
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

        # Insert sample offers.
        connection.execute(
            text("""
                INSERT INTO offers (
                    offer_id,
                    provider,
                    country,
                    data_gb,
                    validity_days,
                    price_eur
                )
                VALUES (
                    :offer_id,
                    :provider,
                    :country,
                    :data_gb,
                    :validity_days,
                    :price_eur
                )
            """),
            [
                {
                    "offer_id": "OFF001",
                    "provider": "TravelConnect",
                    "country": "Japan",
                    "data_gb": 5,
                    "validity_days": 7,
                    "price_eur": 8.99,
                },
                {
                    "offer_id": "OFF002",
                    "provider": "GlobeLink",
                    "country": "France",
                    "data_gb": 10,
                    "validity_days": 30,
                    "price_eur": 12.50,
                },
            ],
        )

    # Replace the real PostgreSQL engine with the test engine.
    monkeypatch.setattr(api_module, "engine", test_engine)

    with TestClient(api_module.app) as test_client:
        yield test_client

    test_engine.dispose()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_all_offers(client):
    response = client.get("/offers")

    assert response.status_code == 200

    offers = response.json()
    assert len(offers) == 2
    assert offers[0]["offer_id"] == "OFF001"


def test_filter_offers_by_country(client):
    response = client.get("/offers?country=Japan")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["country"] == "Japan"


def test_country_filter_is_case_insensitive(client):
    response = client.get("/offers?country=japan")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_unknown_country_returns_empty_list(client):
    response = client.get("/offers?country=Brazil")

    assert response.status_code == 200
    assert response.json() == []


def test_empty_country_parameter_is_rejected(client):
    response = client.get("/offers?country=")

    assert response.status_code == 422

def test_get_offer_by_id(client):
    response = client.get("/offers/OFF001")

    assert response.status_code == 200
    assert response.json()["offer_id"] == "OFF001"


def test_get_unknown_offer_returns_404(client):
    response = client.get("/offers/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found."