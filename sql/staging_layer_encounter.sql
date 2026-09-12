DROP TABLE IF EXISTS healthcare.fact_encounter CASCADE;

CREATE TABLE healthcare.fact_encounter (
    encounter_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES healthcare.dim_patient(patient_id),
    encounter_class TEXT,
    status TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    service_provider_id TEXT,
    etl_load_time TIMESTAMPTZ,
    CONSTRAINT valid_encounter_period CHECK (
        end_date IS NULL OR start_date IS NULL OR end_date >= start_date
    )
);

INSERT INTO healthcare.fact_encounter (
    encounter_id,
    patient_id,
    encounter_class,
    status,
    start_date,
    end_date,
    service_provider_id,
    etl_load_time
)
SELECT
    encounter_id,
    patient_id,
    encounter_class,
    status,
    start_date::timestamptz,
    end_date::timestamptz,
    service_provider_id,
    etl_load_time::timestamptz
FROM healthcare.raw_encounter;

CREATE INDEX idx_fact_encounter_patient
    ON healthcare.fact_encounter(patient_id);

CREATE INDEX idx_fact_encounter_start_date
    ON healthcare.fact_encounter(start_date);
