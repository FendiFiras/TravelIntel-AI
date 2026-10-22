
-- TravelIntel AI database initialization

CREATE TABLE IF NOT EXISTS offers (
    offer_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    country TEXT NOT NULL,
    data_gb NUMERIC NOT NULL CHECK (data_gb > 0),
    validity_days INTEGER NOT NULL CHECK (validity_days > 0),
    price_eur NUMERIC(10, 2) NOT NULL CHECK (price_eur > 0)
);

CREATE TABLE IF NOT EXISTS workflow_errors (
    id BIGSERIAL PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    error_message TEXT NOT NULL,
    error_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
