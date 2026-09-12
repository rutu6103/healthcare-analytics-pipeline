/*
Healthcare BI analysis queries (PostgreSQL)

Run these after the raw tables, dimensional tables, and patient-summary view have
been created. Each section answers a practical utilization or population question.
*/

-- 1. Monthly encounter trend, month-over-month change, and rolling average.
-- Business use: separates a sustained utilization shift from a one-month spike.
WITH monthly_encounters AS (
    SELECT
        DATE_TRUNC('month', start_date::timestamptz)::date AS encounter_month,
        COUNT(*) AS encounter_count
    FROM healthcare.fact_encounter
    WHERE start_date IS NOT NULL
    GROUP BY 1
),
trend AS (
    SELECT
        encounter_month,
        encounter_count,
        LAG(encounter_count) OVER (ORDER BY encounter_month) AS previous_month_count,
        ROUND(
            AVG(encounter_count) OVER (
                ORDER BY encounter_month
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ),
            1
        ) AS three_month_rolling_average
    FROM monthly_encounters
)
SELECT
    encounter_month,
    encounter_count,
    previous_month_count,
    ROUND(
        100.0 * (encounter_count - previous_month_count)
        / NULLIF(previous_month_count, 0),
        1
    ) AS month_over_month_pct,
    three_month_rolling_average
FROM trend
ORDER BY encounter_month;


-- 2. Latest encounter for every patient.
-- Business use: creates one current utilization record per patient for follow-up.
WITH ranked_encounters AS (
    SELECT
        encounter_id,
        patient_id,
        encounter_class,
        status,
        start_date,
        ROW_NUMBER() OVER (
            PARTITION BY patient_id
            ORDER BY start_date::timestamptz DESC, encounter_id
        ) AS encounter_rank
    FROM healthcare.fact_encounter
)
SELECT
    encounter_id,
    patient_id,
    encounter_class,
    status,
    start_date
FROM ranked_encounters
WHERE encounter_rank = 1
ORDER BY start_date::timestamptz DESC;


-- 3. Repeat-patient utilization distribution.
-- Business use: shows how much workload is associated with returning patients.
WITH patient_utilization AS (
    SELECT
        patient_id,
        COUNT(*) AS encounter_count
    FROM healthcare.fact_encounter
    GROUP BY patient_id
)
SELECT
    CASE
        WHEN encounter_count = 1 THEN '1 encounter'
        WHEN encounter_count BETWEEN 2 AND 5 THEN '2-5 encounters'
        WHEN encounter_count BETWEEN 6 AND 20 THEN '6-20 encounters'
        ELSE '21+ encounters'
    END AS utilization_band,
    COUNT(*) AS patient_count,
    SUM(encounter_count) AS total_encounters,
    ROUND(AVG(encounter_count), 1) AS average_encounters_per_patient
FROM patient_utilization
GROUP BY 1
ORDER BY MIN(encounter_count);


-- 4. Encounters occurring within 30 days of a patient's previous encounter.
-- Business use: provides a screening metric for short-interval repeat utilization;
-- it is not a clinical readmission measure because encounter context is limited.
WITH sequenced_encounters AS (
    SELECT
        encounter_id,
        patient_id,
        encounter_class,
        start_date::timestamptz AS start_timestamp,
        LAG(start_date::timestamptz) OVER (
            PARTITION BY patient_id
            ORDER BY start_date::timestamptz, encounter_id
        ) AS previous_start_timestamp
    FROM healthcare.fact_encounter
    WHERE start_date IS NOT NULL
)
SELECT
    encounter_id,
    patient_id,
    encounter_class,
    previous_start_timestamp,
    start_timestamp,
    EXTRACT(DAY FROM start_timestamp - previous_start_timestamp)::integer
        AS days_since_previous_encounter
FROM sequenced_encounters
WHERE start_timestamp - previous_start_timestamp <= INTERVAL '30 days'
ORDER BY patient_id, start_timestamp;


-- 5. Top five recorded conditions within each state.
-- Business use: supports geographically targeted investigation and reporting.
WITH condition_counts AS (
    SELECT
        COALESCE(p.state, 'Unknown') AS state,
        COALESCE(c.condition_name, 'Unspecified') AS condition_name,
        COUNT(*) AS condition_count
    FROM healthcare.fact_condition AS c
    INNER JOIN healthcare.dim_patient AS p
        ON c.patient_id = p.patient_id
    GROUP BY 1, 2
),
ranked_conditions AS (
    SELECT
        state,
        condition_name,
        condition_count,
        DENSE_RANK() OVER (
            PARTITION BY state
            ORDER BY condition_count DESC
        ) AS condition_rank
    FROM condition_counts
)
SELECT
    state,
    condition_rank,
    condition_name,
    condition_count
FROM ranked_conditions
WHERE condition_rank <= 5
ORDER BY state, condition_rank, condition_name;


-- 6. Executive patient summary.
-- Business use: provides headline population and utilization KPIs.
SELECT
    COUNT(*) AS patient_count,
    SUM(encounters) AS encounter_count,
    SUM(conditions) AS condition_count,
    ROUND(AVG(encounters), 1) AS average_encounters_per_patient,
    COUNT(*) FILTER (WHERE encounters > 1) AS repeat_patient_count
FROM healthcare.vw_patient_summary;
