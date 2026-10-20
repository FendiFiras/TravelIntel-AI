
from decimal import Decimal

from fastapi.testclient import TestClient

from src import api


def test_recommendation_endpoint(monkeypatch):
    """Check that the recommendation route works through FastAPI."""

    class FakeResult:
        def mappings(self):
            return self

        def all(self):
            return [
                {
                    "offer_id": "JP001",
                    "provider": "GlobalConnect",
                    "country": "Japan",
                    "data_gb": 15,
                    "validity_days": 30,
                    "price_eur": Decimal("18.99"),
                }
            ]

    class FakeConnection:
        def execute(self, statement):
            return FakeResult()

    class FakeConnectionContext:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConnectionContext()

    monkeypatch.setattr(api, "engine", FakeEngine())

    client = TestClient(api.app)

    response = client.get(
        "/offers/recommend",
        params={
            "country": "Japan",
            "min_data_gb": 10,
            "trip_days": 10,
            "max_budget": 25,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_recommendations"] == 1
    assert data["recommendations"][0]["offer_id"] == "JP001"


def test_recommendation_rejects_invalid_parameters():
    client = TestClient(api.app)

    response = client.get(
        "/offers/recommend",
        params={
            "country": "Japan",
            "min_data_gb": -5,
            "trip_days": 0,
            "max_budget": -10,
        },
    )

    assert response.status_code == 422
