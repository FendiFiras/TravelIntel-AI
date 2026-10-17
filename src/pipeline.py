
import csv
import math
from pathlib import Path


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_DIR / "data" / "supplier_offers.csv"
OUTPUT_DIR = PROJECT_DIR / "output"

VALID_FILE = OUTPUT_DIR / "valid_offers.csv"
REJECTED_FILE = OUTPUT_DIR / "rejected_offers.csv"

# Columns expected in the supplier's CSV file.
REQUIRED_COLUMNS = [
    "offer_id",
    "provider",
    "country",
    "data_gb",
    "validity_days",
    "price_eur",
]


# --------------------------------------------------
# 2. Validate one offer
# --------------------------------------------------

def validate_offer(offer):
    """Return a list of validation errors for one offer."""
    errors = []

    # Required text fields
    for field in ["offer_id", "provider", "country"]:
        value = str(offer.get(field) or "").strip()

        if not value:
            errors.append(f"Missing required field: {field}")

    # Data allowance must be a finite, positive number.
    try:
        data_gb = float(offer.get("data_gb", ""))

        if not math.isfinite(data_gb) or data_gb <= 0:
            errors.append(
                "data_gb must be a finite number greater than zero"
            )
    except (ValueError, TypeError):
        errors.append("data_gb must be a valid number")

    # Validity must be a positive whole number.
    try:
        validity_days = int(offer.get("validity_days", ""))

        if validity_days <= 0:
            errors.append("validity_days must be greater than zero")
    except (ValueError, TypeError):
        errors.append("validity_days must be a valid integer")

    # Price must be a finite, positive number.
    try:
        price_eur = float(offer.get("price_eur", ""))

        if not math.isfinite(price_eur) or price_eur <= 0:
            errors.append(
                "price_eur must be a finite number greater than zero"
            )
    except (ValueError, TypeError):
        errors.append("price_eur must be a valid number")

    return errors


# --------------------------------------------------
# 3. Identify duplicate commercial offers
# --------------------------------------------------

def create_duplicate_key(offer):
    """Identify offers with the same commercial details."""
    return (
        offer["provider"].strip().lower(),
        offer["country"].strip().lower(),
        float(offer["data_gb"]),
        int(offer["validity_days"]),
        round(float(offer["price_eur"]), 2),
    )


# --------------------------------------------------
# 4. Write results to CSV
# --------------------------------------------------

def write_csv(file_path, rows, fieldnames):
    """Write rows to a CSV file."""
    with file_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------
# 5. Run the data pipeline
# --------------------------------------------------

def run_pipeline():
    """Read, validate, deduplicate, and export supplier offers."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    valid_offers = []
    rejected_offers = []

    seen_offers = set()
    seen_ids = set()

    rows_processed = 0

    # Read the supplier's CSV file.
    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        # Check that the expected columns exist.
        if not reader.fieldnames or not set(REQUIRED_COLUMNS).issubset(
            reader.fieldnames
        ):
            raise ValueError(
                "CSV must contain these columns: "
                + ", ".join(REQUIRED_COLUMNS)
            )

        # Process each offer.
        for row in reader:
            rows_processed += 1

            offer_id = str(row.get("offer_id") or "").strip()
            normalized_id = offer_id.lower()

            # Validate the offer's fields.
            errors = validate_offer(row)

            # Detect duplicate IDs, even if an earlier row was invalid.
            if normalized_id and normalized_id in seen_ids:
                errors.append("Duplicate offer_id")

            if normalized_id:
                seen_ids.add(normalized_id)

            # Reject offers with invalid data.
            if errors:
                row["errors"] = "; ".join(errors)
                rejected_offers.append(row)
                continue

            # Reject duplicate commercial offers.
            duplicate_key = create_duplicate_key(row)

            if duplicate_key in seen_offers:
                row["errors"] = "Duplicate commercial offer"
                rejected_offers.append(row)
                continue

            # Keep the valid, unique offer.
            seen_offers.add(duplicate_key)
            valid_offers.append(row)

    # Export valid and rejected offers.
    write_csv(VALID_FILE, valid_offers, REQUIRED_COLUMNS)

    write_csv(
        REJECTED_FILE,
        rejected_offers,
        REQUIRED_COLUMNS + ["errors"],
    )

    # Display a summary.
    print("\n--- Pipeline Summary ---")
    print(f"Rows processed: {rows_processed}")
    print(f"Valid offers: {len(valid_offers)}")
    print(f"Rejected offers: {len(rejected_offers)}")
    print(f"Clean data saved to: {VALID_FILE}")
    print(f"Rejected data saved to: {REJECTED_FILE}")
    print("Pipeline completed successfully!")


# --------------------------------------------------
# 6. Entry point
# --------------------------------------------------

if __name__ == "__main__":
    run_pipeline()
