DROP TABLE IF EXISTS healthcare.fact_condition CASCADE;

CREATE TABLE healthcare.fact_condition (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES healthcare.dim_patient(patient_id),
    encounter_id TEXT REFERENCES healthcare.fact_encounter(encounter_id),
    clinical_status TEXT,
    verification_status TEXT,
    condition_code TEXT,
    condition_name TEXT,
    onset_date TIMESTAMPTZ,
    etl_load_time TIMESTAMPTZ
);

INSERT INTO healthcare.fact_condition (
    condition_id,
    patient_id,
    encounter_id,
    clinical_status,
    verification_status,
    condition_code,
    condition_name,
    onset_date,
    etl_load_time
)
SELECT
    condition_id,
    patient_id,
    encounter_id,
    clinical_status,
    verification_status,
    condition_code,
    condition_name,
    onset_date::timestamptz,
    etl_load_time::timestamptz
FROM healthcare.raw_condition;

CREATE INDEX idx_fact_condition_patient
    ON healthcare.fact_condition(patient_id);

CREATE INDEX idx_fact_condition_encounter
    ON healthcare.fact_condition(encounter_id);
