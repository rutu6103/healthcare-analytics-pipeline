CREATE OR REPLACE VIEW healthcare.vw_patient_summary AS

SELECT

p.patient_id,
p.gender,
p.state,

COUNT(DISTINCT e.encounter_id) encounters,

COUNT(DISTINCT c.condition_id) conditions

FROM healthcare.dim_patient p

LEFT JOIN healthcare.fact_encounter e
ON p.patient_id = e.patient_id

LEFT JOIN healthcare.fact_condition c
ON p.patient_id = c.patient_id

GROUP BY

p.patient_id,
p.gender,
p.state;