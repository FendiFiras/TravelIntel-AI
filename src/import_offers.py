
import csv

from sqlalchemy import text

from src.database import engine
from src.pipeline import VALID_FILE


def import_offers():
    """Import validated CSV offers into PostgreSQL."""

    if not VALID_FILE.exists():
        raise FileNotFoundError(
            "Cleaned offers CSV not found. Run the pipeline first."
        )

    with VALID_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        offers = list(csv.DictReader(file))

    imported_count = 0

    # Begin a transaction: commit on success, roll back on failure.
    with engine.begin() as connection:
        for offer in offers:
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
                    ON CONFLICT (offer_id)
                    DO UPDATE SET
                        provider = EXCLUDED.provider,
                        country = EXCLUDED.country,
                        data_gb = EXCLUDED.data_gb,
                        validity_days = EXCLUDED.validity_days,
                        price_eur = EXCLUDED.price_eur
                """),
                {
                    "offer_id": offer["offer_id"],
                    "provider": offer["provider"],
                    "country": offer["country"],
                    "data_gb": float(offer["data_gb"]),
                    "validity_days": int(offer["validity_days"]),
                    "price_eur": offer["price_eur"],
                },
            )

            imported_count += 1

    print(f"Successfully processed {imported_count} offers!")
    return imported_count

if __name__ == "__main__":
    import_offers()
