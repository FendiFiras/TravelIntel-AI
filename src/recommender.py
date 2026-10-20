
from decimal import Decimal


def recommend_offers(
    offers: list[dict],
    country: str,
    min_data_gb: float,
    trip_days: int,
    max_budget: Decimal,
) -> list[dict]:
    """Return eligible eSIM offers, cheapest first."""

    recommendations = []

    for offer in offers:
        if offer["country"].casefold() != country.casefold():
            continue

        if float(offer["data_gb"]) < min_data_gb:
            continue

        if int(offer["validity_days"]) < trip_days:
            continue

        if Decimal(str(offer["price_eur"])) > max_budget:
            continue

        recommendations.append(offer)

    return sorted(
        recommendations,
        key=lambda offer: Decimal(str(offer["price_eur"]))
    )
