
import csv
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
VALID_FILE = PROJECT_DIR / "output" / "valid_offers.csv"

app = FastAPI(
    title="TravelIntel AI API",
    description="API for retrieving validated eSIM offers.",
    version="1.0.0",
)


# --------------------------------------------------
# 2. Define the structure of an offer
# --------------------------------------------------

class Offer(BaseModel):
    offer_id: str
    provider: str
    country: str
    data_gb: float
    validity_days: int
    price_eur: float


# --------------------------------------------------
# 3. Load offers from the cleaned CSV
# --------------------------------------------------

def load_offers() -> list[Offer]:
    """Read validated offers from the output CSV."""

    if not VALID_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Cleaned offers are unavailable. "
                "Run the data pipeline first."
            ),
        )

    try:
        with VALID_FILE.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            reader = csv.DictReader(file)

            return [
                Offer(
                    offer_id=row["offer_id"],
                    provider=row["provider"],
                    country=row["country"],
                    data_gb=float(row["data_gb"]),
                    validity_days=int(row["validity_days"]),
                    price_eur=float(row["price_eur"]),
                )
                for row in reader
            ]

    except (ValueError, KeyError, csv.Error) as error:
        raise HTTPException(
            status_code=500,
            detail="Could not read the cleaned offers CSV.",
        ) from error


# --------------------------------------------------
# 4. API endpoints
# --------------------------------------------------

@app.get("/health")
def health_check():
    """Check whether the API is running."""

    return {"status": "ok"}


@app.get("/offers", response_model=list[Offer])
def get_offers(
    country: str | None = Query(default=None, min_length=1)
):
    """Return all valid offers, optionally filtered by country."""

    offers = load_offers()

    if country is not None:
        offers = [
            offer
            for offer in offers
            if offer.country.casefold() == country.strip().casefold()
        ]

    return offers
