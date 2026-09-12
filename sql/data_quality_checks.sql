/*
Data-quality checks for the healthcare warehouse.
Each query should return zero rows or zero exceptions unless noted otherwise.
*/

-- 1. Duplicate primary identifiers.
SELECT 'patient' AS entity, patient_id AS duplicate_id, COUNT(*) AS row_count
FROM healthcare.dim_patient
GROUP BY patient_id
HAVING COUNT(*) > 1

UNION ALL

SELECT 'encounter', encounter_id, COUNT(*)
FROM healthcare.fact_encounter
GROUP BY encounter_id
HAVING COUNT(*) > 1

UNION ALL

SELECT 'condition', condition_id, COUNT(*)
FROM healthcare.fact_condition
GROUP BY condition_id
HAVING COUNT(*) > 1;


-- 2. Encounters whose patient does not exist in the patient dimension.
SELECT
    e.encounter_id,
    e.patient_id
FROM healthcare.fact_encounter AS e
LEFT JOIN healthcare.dim_patient AS p
    ON e.patient_id = p.patient_id
WHERE p.patient_id IS NULL;


-- 3. Conditions whose patient does not exist in the patient dimension.
SELECT
    c.condition_id,
    c.patient_id
FROM healthcare.fact_condition AS c
LEFT JOIN healthcare.dim_patient AS p
    ON c.patient_id = p.patient_id
WHERE p.patient_id IS NULL;


-- 4. Encounter date exceptions.
SELECT
    encounter_id,
    start_date,
    end_date
FROM healthcare.fact_encounter
WHERE start_date IS NULL
   OR (end_date IS NOT NULL AND end_date::timestamptz < start_date::timestamptz);


-- 5. Completeness summary. Null counts are reviewed rather than assumed to be
-- errors because optional fields are expected in FHIR data.
SELECT
    COUNT(*) AS patient_rows,
    COUNT(*) FILTER (WHERE gender IS NULL) AS missing_gender,
    COUNT(*) FILTER (WHERE birth_date IS NULL) AS missing_birth_date,
    COUNT(*) FILTER (WHERE state IS NULL) AS missing_state
FROM healthcare.dim_patient;

SELECT
    COUNT(*) AS condition_rows,
    COUNT(*) FILTER (WHERE condition_name IS NULL) AS missing_condition_name,
    COUNT(*) FILTER (WHERE onset_date IS NULL) AS missing_onset_date
FROM healthcare.fact_condition;
