
from src.pipeline import validate_offer, create_duplicate_key


def make_offer(**overrides):
    """Create a valid offer, with optional changes for testing."""
    offer = {
        "offer_id": "OFF001",
        "provider": "TravelConnect",
        "country": "Japan",
        "data_gb": "5",
        "validity_days": "7",
        "price_eur": "8.99",
    }
    offer.update(overrides)
    return offer


def test_valid_offer_has_no_errors():
    offer = make_offer()

    assert validate_offer(offer) == []


def test_missing_country_is_rejected():
    offer = make_offer(country="")

    errors = validate_offer(offer)

    assert "Missing required field: country" in errors


def test_negative_price_is_rejected():
    offer = make_offer(price_eur="-3.00")

    errors = validate_offer(offer)

    assert "price_eur must be greater than zero" in errors


def test_zero_data_allowance_is_rejected():
    offer = make_offer(data_gb="0")

    errors = validate_offer(offer)

    assert "data_gb must be greater than zero" in errors


def test_zero_validity_is_rejected():
    offer = make_offer(validity_days="0")

    errors = validate_offer(offer)

    assert "validity_days must be greater than zero" in errors


def test_duplicate_commercial_details_have_same_key():
    first = make_offer(offer_id="OFF001")
    second = make_offer(offer_id="OFF999")

    assert create_duplicate_key(first) == create_duplicate_key(second)


def test_different_prices_have_different_keys():
    first = make_offer(price_eur="8.99")
    second = make_offer(price_eur="9.99")

    assert create_duplicate_key(first) != create_duplicate_key(second)
