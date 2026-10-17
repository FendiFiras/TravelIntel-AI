
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.database import engine


# --------------------------------------------
# 1. Create the API application
# --------------------------------------------

app = FastAPI(
    title="TravelIntel AI API",
    description="API for retrieving validated eSIM offers.",
    version="1.1.0",
)


# --------------------------------------------
# 2. Define the response model
# --------------------------------------------

class Offer(BaseModel):
    offer_id: str
    provider: str
    country: str
    data_gb: float
    validity_days: int
    price_eur: Decimal


# --------------------------------------------
# 3. Health endpoint
# --------------------------------------------

@app.get("/health")
def health_check():
    """Check whether the API is running."""
    return {"status": "ok"}


# --------------------------------------------
# 4. Retrieve offers from PostgreSQL
# --------------------------------------------

@app.get("/offers", response_model=list[Offer])
def get_offers(
    country: str | None = Query(default=None, min_length=1)
):
    """Return offers from PostgreSQL, optionally filtered by country."""

    sql = """
        SELECT
            offer_id,
            provider,
            country,
            data_gb,
            validity_days,
            price_eur
        FROM offers
    """

    parameters = {}

    if country is not None:
        sql += " WHERE LOWER(country) = LOWER(:country)"
        parameters["country"] = country.strip()

    sql += " ORDER BY offer_id"

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(sql),
                parameters,
            )

            offers = [
                Offer(**dict(row))
                for row in result.mappings().all()
            ]

            return offers

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database is currently unavailable.",
        ) from error


@app.get("/offers/{offer_id}", response_model=Offer)
def get_offer_by_id(offer_id: str):
    """Retrieve one offer by its unique ID."""

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT
                        offer_id,
                        provider,
                        country,
                        data_gb,
                        validity_days,
                        price_eur
                    FROM offers
                    WHERE offer_id = :offer_id
                """),
                {"offer_id": offer_id},
            )

            row = result.mappings().first()

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Offer not found.",
                )

            return Offer(**dict(row))

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database is currently unavailable.",
        ) from error
