CREATE TABLE IF NOT EXISTS healthcare.etl_log (
    load_id BIGSERIAL PRIMARY KEY,
    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    table_name VARCHAR(100) NOT NULL,
    records_loaded INTEGER NOT NULL
);
