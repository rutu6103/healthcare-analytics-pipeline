DROP TABLE IF EXISTS healthcare.dim_patient CASCADE;

CREATE TABLE healthcare.dim_patient (
    patient_id TEXT PRIMARY KEY,
    gender TEXT,
    birth_date DATE,
    city TEXT,
    state TEXT,
    country TEXT,
    deceased_flag BOOLEAN NOT NULL DEFAULT FALSE,
    patient_age INTEGER,
    etl_load_time TIMESTAMPTZ
);

INSERT INTO healthcare.dim_patient (
    patient_id,
    gender,
    birth_date,
    city,
    state,
    country,
    deceased_flag,
    patient_age,
    etl_load_time
)
SELECT
    patient_id,
    gender,
    birth_date::date,
    city,
    state,
    country,
    COALESCE(deceased_flag::boolean, FALSE),
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date::date))::integer,
    etl_load_time::timestamptz
FROM healthcare.raw_patient;
