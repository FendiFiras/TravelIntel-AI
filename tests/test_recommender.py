
from decimal import Decimal

from src.recommender import recommend_offers


OFFERS = [
    {
        "offer_id": "JP001",
        "provider": "GlobalConnect",
        "country": "Japan",
        "data_gb": 15,
        "validity_days": 30,
        "price_eur": "18.99",
    },
    {
        "offer_id": "JP002",
        "provider": "TravelNet",
        "country": "Japan",
        "data_gb": 20,
        "validity_days": 15,
        "price_eur": "24.00",
    },
    {
        "offer_id": "JP003",
        "provider": "BudgetSIM",
        "country": "Japan",
        "data_gb": 5,
        "validity_days": 30,
        "price_eur": "9.99",
    },
    {
        "offer_id": "FR001",
        "provider": "EuroSIM",
        "country": "France",
        "data_gb": 20,
        "validity_days": 30,
        "price_eur": "12.00",
    },
]


def test_recommendation_filters_and_sorts():
    results = recommend_offers(
        offers=OFFERS,
        country="Japan",
        min_data_gb=10,
        trip_days=10,
        max_budget=Decimal("25"),
    )

    assert [offer["offer_id"] for offer in results] == [
        "JP001",
        "JP002",
    ]


def test_recommendation_respects_budget():
    results = recommend_offers(
        offers=OFFERS,
        country="Japan",
        min_data_gb=10,
        trip_days=10,
        max_budget=Decimal("20"),
    )

    assert len(results) == 1
    assert results[0]["offer_id"] == "JP001"


def test_recommendation_returns_empty_when_no_match():
    results = recommend_offers(
        offers=OFFERS,
        country="Japan",
        min_data_gb=50,
        trip_days=10,
        max_budget=Decimal("25"),
    )

    assert results == []


def test_recommendation_country_is_case_insensitive():
    results = recommend_offers(
        offers=OFFERS,
        country="jApAn",
        min_data_gb=10,
        trip_days=10,
        max_budget=Decimal("25"),
    )

    assert len(results) == 2


def test_recommendation_rejects_short_validity():
    results = recommend_offers(
        offers=OFFERS,
        country="Japan",
        min_data_gb=10,
        trip_days=20,
        max_budget=Decimal("25"),
    )

    assert [offer["offer_id"] for offer in results] == ["JP001"]
