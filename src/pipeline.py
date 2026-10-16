
import csv
from pathlib import Path


# Find the project folder, regardless of where the command is run.
PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_DIR / "data" / "supplier_offers.csv"
OUTPUT_DIR = PROJECT_DIR / "output"

VALID_FILE = OUTPUT_DIR / "valid_offers.csv"
REJECTED_FILE = OUTPUT_DIR / "rejected_offers.csv"


def validate_offer(offer):
    """Return a list of validation errors for one offer."""
    errors = []

    # Check required text fields.
    for field in ["offer_id", "provider", "country"]:
        if not offer.get(field, "").strip():
            errors.append(f"Missing required field: {field}")

    # Check that data allowance is a positive number.
    try:
        data_gb = float(offer["data_gb"])
        if data_gb <= 0:
            errors.append("data_gb must be greater than zero")
    except (ValueError, KeyError):
        errors.append("data_gb must be a valid number")

    # Check that validity is a positive whole number.
    try:
        validity_days = int(offer["validity_days"])
        if validity_days <= 0:
            errors.append("validity_days must be greater than zero")
    except (ValueError, KeyError):
        errors.append("validity_days must be a valid integer")

    # Check that the price is positive.
    try:
        price_eur = float(offer["price_eur"])
        if price_eur <= 0:
            errors.append("price_eur must be greater than zero")
    except (ValueError, KeyError):
        errors.append("price_eur must be a valid number")

    return errors


def create_duplicate_key(offer):
    """Identify offers with the same commercial details."""
    return (
        offer["provider"].strip().lower(),
        offer["country"].strip().lower(),
        float(offer["data_gb"]),
        int(offer["validity_days"]),
        round(float(offer["price_eur"]), 2),
    )


def write_csv(file_path, rows, fieldnames):
    """Write rows to a CSV file."""
    with file_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    valid_offers = []
    rejected_offers = []
    seen_offers = set()

    with INPUT_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "offer_id",
            "provider",
            "country",
            "data_gb",
            "validity_days",
            "price_eur",
        }

        if not reader.fieldnames or not required_columns.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                f"CSV must contain these columns: "
                f"{', '.join(sorted(required_columns))}"
            )

        for row in reader:
            errors = validate_offer(row)

            if errors:
                row["errors"] = "; ".join(errors)
                rejected_offers.append(row)
                continue

            duplicate_key = create_duplicate_key(row)

            if duplicate_key in seen_offers:
                row["errors"] = "Duplicate commercial offer"
                rejected_offers.append(row)
                continue

            seen_offers.add(duplicate_key)
            valid_offers.append(row)

    original_columns = [
        "offer_id",
        "provider",
        "country",
        "data_gb",
        "validity_days",
        "price_eur",
    ]

    write_csv(VALID_FILE, valid_offers, original_columns)

    write_csv(
        REJECTED_FILE,
        rejected_offers,
        original_columns + ["errors"],
    )

    print("Pipeline completed!")
    print(f"Valid offers: {len(valid_offers)}")
    print(f"Rejected offers: {len(rejected_offers)}")
    print(f"Clean data saved to: {VALID_FILE}")
    print(f"Rejected data saved to: {REJECTED_FILE}")


if __name__ == "__main__":
    run_pipeline()
