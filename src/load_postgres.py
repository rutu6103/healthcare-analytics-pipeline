import os
import re
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "fhir"
load_dotenv(PROJECT_ROOT / ".env")

TABLES = {
    "raw_patient": PROCESSED_DIR / "patient.csv",
    "raw_encounter": PROCESSED_DIR / "encounter.csv",
    "raw_condition": PROCESSED_DIR / "condition.csv",
}

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "healthcare_analytics")
DB_SCHEMA = os.getenv("DB_SCHEMA", "healthcare")


def validate_schema_name():
    """Reject unsafe schema names before inserting one into SQL statements."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", DB_SCHEMA):
        raise ValueError(
            "DB_SCHEMA must start with a letter or underscore and contain only "
            "letters, numbers, and underscores."
        )


def build_engine():
    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is not set. Copy .env.example to .env or define the "
            "database environment variables before running the loader."
        )

    encoded_password = quote_plus(DB_PASSWORD)
    connection_url = (
        f"postgresql+psycopg2://{DB_USER}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return create_engine(connection_url, pool_pre_ping=True)


def initialize_database(engine):
    validate_schema_name()

    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS "{DB_SCHEMA}".etl_log (
                    load_id BIGSERIAL PRIMARY KEY,
                    load_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    table_name VARCHAR(100) NOT NULL,
                    records_loaded INTEGER NOT NULL
                )
                """
            )
        )


def load_table(engine, csv_path, table_name):
    if not csv_path.exists():
        raise FileNotFoundError(f"Generated input not found: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    print(f"Loading {len(dataframe):,} rows into {DB_SCHEMA}.{table_name}")

    dataframe.to_sql(
        table_name,
        engine,
        schema=DB_SCHEMA,
        if_exists="replace",
        index=False,
        chunksize=1_000,
        method="multi",
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO "{DB_SCHEMA}".etl_log (table_name, records_loaded)
                VALUES (:table_name, :records_loaded)
                """
            ),
            {"table_name": table_name, "records_loaded": len(dataframe)},
        )


def main():
    engine = build_engine()
    initialize_database(engine)

    for table_name, csv_path in TABLES.items():
        load_table(engine, csv_path, table_name)

    print("All generated tables loaded successfully.")


if __name__ == "__main__":
    main()
