
import csv

import pytest
from fastapi.testclient import TestClient

from src.api import app
import src.api as api_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create a test client with its own sample CSV."""

    test_csv = tmp_path / "valid_offers.csv"

    rows = [
        {
            "offer_id": "OFF001",
            "provider": "TravelConnect",
            "country": "Japan",
            "data_gb": "5",
            "validity_days": "7",
            "price_eur": "8.99",
        },
        {
            "offer_id": "OFF002",
            "provider": "GlobeLink",
            "country": "France",
            "data_gb": "10",
            "validity_days": "30",
            "price_eur": "12.50",
        },
    ]

    with test_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    # Make the API use our temporary test CSV.
    monkeypatch.setattr(api_module, "VALID_FILE", test_csv)

    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_all_offers(client):
    response = client.get("/offers")

    assert response.status_code == 200
    assert len(response.json()) == 2


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


def test_missing_csv_returns_503(client, tmp_path, monkeypatch):
    missing_file = tmp_path / "missing.csv"
    monkeypatch.setattr(api_module, "VALID_FILE", missing_file)

    response = client.get("/offers")

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
