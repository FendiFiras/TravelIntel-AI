
import os
import hmac

from decimal import Decimal
from typing import Annotated
from src.logger import logger
from fastapi import FastAPI, HTTPException, Query, Header
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.database import engine
from src.pipeline import run_pipeline
from src.import_offers import import_offers
from src.recommender import recommend_offers


# ============================================
# 1. FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title="TravelIntel AI API",
    description="API for managing validated eSIM offers.",
    version="1.2.0",
)


# ============================================
# 2. PYDANTIC MODELS
# ============================================

class Offer(BaseModel):
    offer_id: str
    provider: str
    country: str
    data_gb: float
    validity_days: int
    price_eur: Decimal


class SupplierOffer(BaseModel):
    offer_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    country: str = Field(min_length=1)
    data_gb: float = Field(gt=0, allow_inf_nan=False)
    validity_days: int = Field(gt=0, strict=True)
    price_eur: Decimal = Field(gt=0, allow_inf_nan=False)


# ============================================
# 3. AUTHENTICATION HELPER
# ============================================

def verify_import_api_key(api_key: str | None):
    """Verify the API key for protected import endpoints."""

    expected_key = os.getenv("IMPORT_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Import API key is not configured.",
        )

    if not api_key or not hmac.compare_digest(
        api_key, expected_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )


# ============================================
# 4. HEALTH CHECK
# ============================================

@app.get("/health")
def health_check():
    return {"status": "ok"}


# ============================================
# 5. GET ALL OFFERS
# ============================================

@app.get("/offers", response_model=list[Offer])
def get_offers(
    country: str | None = Query(default=None, min_length=1)
):
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

            return [
                Offer(**dict(row))
                for row in result.mappings().all()
            ]

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database is currently unavailable.",
        ) from error



    
@app.get("/offers/recommend")
def get_recommendations(
    country: str = Query(min_length=1),
    min_data_gb: float = Query(gt=0),
    trip_days: int = Query(gt=0),
    max_budget: Decimal = Query(gt=0),
):
    # Retrieve existing offers from PostgreSQL
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    offer_id,
                    provider,
                    country,
                    data_gb,
                    validity_days,
                    price_eur
                FROM offers
            """)
        ).mappings().all()

    offers = [dict(row) for row in rows]

    # Apply our tested recommendation logic
    recommendations = recommend_offers(
        offers=offers,
        country=country,
        min_data_gb=min_data_gb,
        trip_days=trip_days,
        max_budget=max_budget,
    )

    return {
        "country": country,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
    }


# ============================================
# 6. GET OFFER BY ID
# ============================================

@app.get("/offers/{offer_id}", response_model=Offer)
def get_offer_by_id(offer_id: str):
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


# ============================================
# 7. IMPORT EXISTING CSV
# ============================================

@app.post("/imports/supplier")
def trigger_supplier_import(
    x_api_key: Annotated[str | None, Header()] = None,
):
    """
    Run the existing CSV validation pipeline
    and import valid offers into PostgreSQL.
    """

    verify_import_api_key(x_api_key)

    try:
        run_pipeline()
        imported_count = import_offers()

        return {
            "status": "success",
            "imported_offers": imported_count,
        }

    except (OSError, ValueError, SQLAlchemyError) as error:
        raise HTTPException(
            status_code=500,
            detail="Supplier import failed.",
        ) from error



# ============================================
# 8. IMPORT NEW JSON OFFERS
# ============================================

@app.post("/offers/import")
def import_supplier_offers(
    offers: list[SupplierOffer],
    x_api_key: Annotated[str | None, Header()] = None,
):
    """
    Accept new supplier offers as JSON,
    validate them, and insert/update the database.
    """

    # Step 1: Verify authentication
    verify_import_api_key(x_api_key)

    # Step 2: Log the start of the import
    logger.info(
        "Supplier import started: %s offers received",
        len(offers),
    )

    # Step 3: Check that the batch is not empty
    if not offers:
        raise HTTPException(
            status_code=400,
            detail="At least one offer is required.",
        )

    # Step 4: Reject duplicate offer IDs
    offer_ids = [offer.offer_id for offer in offers]

    if len(offer_ids) != len(set(offer_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate offer IDs in request.",
        )

    # Step 5: Prepare the SQL query
    sql = text("""
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
    """)

    # Step 6: Insert or update offers
    try:
        with engine.begin() as connection:
            for offer in offers:

                offer_data = offer.model_dump()

                # Convert Decimal to a DB-compatible value
                offer_data["price_eur"] = str(offer.price_eur)

                connection.execute(
                    sql,
                    offer_data,
                )

    except SQLAlchemyError as error:
        logger.exception("Supplier import failed")

        raise HTTPException(
            status_code=503,
            detail="Database import failed.",
        ) from error

    # Step 7: Log successful completion
    logger.info(
        "Supplier import completed: %s offers processed",
        len(offers),
    )

    # Step 8: Return the API response
    return {
        "status": "success",
        "processed_offers": len(offers),
    }



@app.get("/offers/recommend")
def get_recommendations(
    country: str = Query(min_length=1),
    min_data_gb: float = Query(gt=0),
    trip_days: int = Query(gt=0),
    max_budget: Decimal = Query(gt=0),
):
    # Retrieve existing offers from PostgreSQL
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    offer_id,
                    provider,
                    country,
                    data_gb,
                    validity_days,
                    price_eur
                FROM offers
            """)
        ).mappings().all()

    offers = [dict(row) for row in rows]

    # Apply our tested recommendation logic
    recommendations = recommend_offers(
        offers=offers,
        country=country,
        min_data_gb=min_data_gb,
        trip_days=trip_days,
        max_budget=max_budget,
    )

    return {
        "country": country,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
    }
