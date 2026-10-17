
from src.pipeline import validate_offer, create_duplicate_key

import csv

import pytest

from src.pipeline import (
    run_pipeline,
    REQUIRED_COLUMNS,
)

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

    assert "price_eur must be a finite number greater than zero" in errors


def test_zero_data_allowance_is_rejected():
    offer = make_offer(data_gb="0")

    errors = validate_offer(offer)


    assert "data_gb must be a finite number greater than zero" in errors


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


def test_nan_price_is_rejected():
    offer = make_offer(price_eur="nan")

    errors = validate_offer(offer)

    assert "price_eur must be a finite number greater than zero" in errors


def test_infinite_data_allowance_is_rejected():
    offer = make_offer(data_gb="inf")

    errors = validate_offer(offer)

    assert "data_gb must be a finite number greater than zero" in errors


def test_missing_country_value_does_not_crash():
    offer = make_offer(country=None)

    errors = validate_offer(offer)

    assert "Missing required field: country" in errors


def test_validity_must_be_a_whole_number():
    offer = make_offer(validity_days="7.5")

    errors = validate_offer(offer)

    assert "validity_days must be a valid integer" in errors






def test_pipeline_creates_valid_and_rejected_files(tmp_path):
    """The pipeline should process a CSV and create both outputs."""

    input_file = tmp_path / "supplier_offers.csv"
    valid_file = tmp_path / "output" / "valid_offers.csv"
    rejected_file = tmp_path / "output" / "rejected_offers.csv"

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
            "data_gb": "0",
            "validity_days": "30",
            "price_eur": "12.50",
        },
    ]

    with input_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    run_pipeline(input_file, valid_file, rejected_file)

    assert valid_file.exists()
    assert rejected_file.exists()

    with valid_file.open(newline="", encoding="utf-8") as file:
        valid_rows = list(csv.DictReader(file))

    with rejected_file.open(newline="", encoding="utf-8") as file:
        rejected_rows = list(csv.DictReader(file))

    assert len(valid_rows) == 1
    assert valid_rows[0]["offer_id"] == "OFF001"

    assert len(rejected_rows) == 1
    assert rejected_rows[0]["offer_id"] == "OFF002"
    assert "data_gb" in rejected_rows[0]["errors"]


def test_pipeline_raises_error_when_input_is_missing(tmp_path):
    """A missing input file should produce a clear error."""

    missing_file = tmp_path / "does_not_exist.csv"

    with pytest.raises(FileNotFoundError, match="Input CSV file not found"):
        run_pipeline(
            input_file=missing_file,
            valid_file=tmp_path / "valid.csv",
            rejected_file=tmp_path / "rejected.csv",
        )


def test_pipeline_rejects_csv_with_missing_columns(tmp_path):
    """A CSV without required headers should be rejected."""

    input_file = tmp_path / "incorrect.csv"

    input_file.write_text(
        "offer_id,provider,country\n"
        "OFF001,TravelConnect,Japan\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CSV must contain these columns"):
        run_pipeline(
            input_file=input_file,
            valid_file=tmp_path / "valid.csv",
            rejected_file=tmp_path / "rejected.csv",
        )
