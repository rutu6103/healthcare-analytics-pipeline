# SQL Interview Notes

*Personal preparation notes for discussing this project in a data-engineering or
BI-analyst interview. These notes assume the reader has already read
[`SQL_WALKTHROUGH.md`](SQL_WALKTHROUGH.md), which explains what each query does.*

The goal of this file is to make sure every design decision in the SQL layer is
defensible under questioning.

---

## 1. Quick facts to have ready

| Question | Answer |
|---|---|
| What is the source? | Public SMART Health IT R4 FHIR test server — synthetic data |
| Is the data real? | No. Synthetic test data only |
| How many patients? | 621 |
| How many encounters? | 19,811 (all dates), ~15,620 (2000+) |
| How many conditions? | 4,701 (all dates), ~3,040 (2000+) |
| Average encounters per patient? | 31.9 (all dates), 25 (2000+) |
| Repeat-patient rate? | 100% (all dates), ~91.6% (2000+) |
| Duplicate IDs? | Zero |
| Orphan relationships? | Zero |
| Missing required fields? | Zero |

The dashboard filters to 2000+ because the synthetic server contains sparse
historical encounters back to 1914. This is documented in the README.

---

## 2. Why each query is written the way it is

### Why `LAG` instead of a self-join for the previous month?

`LAG` is a window function that reads the previous row without a second
reference to the same table. A self-join would work but requires a correlated
subquery or a join key like `month = previous_month`. `LAG` is cleaner, runs in
one pass, and makes the intent obvious.

### Why `ROW_NUMBER` for latest encounter but `DENSE_RANK` for top conditions?

`ROW_NUMBER` gives a unique number per row. It is exactly what you want when
you only need one row per partition.

`DENSE_RANK` gives a rank with ties allowed. It is exactly what you want when
two conditions have the same frequency and should share a rank.

Using `ROW_NUMBER` for top conditions would arbitrarily break ties, which
misrepresents the data.

### Why a rolling average of three months, not twelve?

Three months is a compromise:
- Shorter windows (2 months) barely smooth the noise.
- Longer windows (12 months) hide recent changes and lag the signal.
- Three months is a common choice for monthly operational metrics.

### Why `NULLIF(y, 0)` for the month-over-month percentage?

Because `NULLIF` protects against division by zero. If a previous month had zero
encounters (which can happen in sparse months like 1914-05), `x / 0` would
raise an error. `NULLIF(y, 0)` returns `NULL` in that case, and `NULL` propagates
gracefully through arithmetic.

### Why `COUNT(DISTINCT ...)` in `vw_patient_summary`?

Because the view joins `dim_patient` to both `fact_encounter` and
`fact_condition`. Without `DISTINCT`, a patient with 3 encounters and 5
conditions would produce 15 joined rows, and `COUNT(*)` would be wrong.

`COUNT(DISTINCT ...)` fixes the multiplication, but the cleaner fix is
pre-aggregated CTEs. This is on the future-enhancements list.

### Why filter to 2000+ in the dashboard but not in the SQL?

The SQL layer exposes the full history. It is the analyst's job to see the whole
data and decide what to filter.

The semantic model (Power BI) applies a business filter so that time-based
visuals are readable. The filter is a semantic-model decision, not a data-layer
decision.

---

## 3. Follow-up questions an interviewer might ask

### "Why is `vw_patient_summary` called a view and not a table?"

Because it is a derived result, not stored data. A view always reflects the
current state of `dim_patient`, `fact_encounter`, and `fact_condition` without
needing a rebuild. A materialized view would be faster but would need
refreshing.

### "What would you change if the data volume were 100× larger?"

- Add indexes on `fact_encounter(patient_id, start_date)` and
  `fact_condition(patient_id, condition_code)`.
- Replace the `COUNT(DISTINCT ...)` view with pre-aggregated CTEs to avoid the
  join multiplication at scale.
- Partition `fact_encounter` by year.
- Consider a materialized view for `vw_patient_summary`.

### "How would you handle the mutable source server?"

The current approach downloads a fresh snapshot each time. For reproducibility,
we would:
- Store the raw bundles in an immutable data lake (S3, local filesystem).
- Add a snapshot date to the warehouse (e.g., `snapshot_id` column).
- Use FHIR `lastUpdated` timestamps to support incremental extraction.

### "What does the repeat-patient rate mean?"

It means: of all patients in the dataset, what percentage have more than one
recorded encounter. It is a purely operational metric. It is not the same as a
clinical follow-up rate, readmission rate, or continuity-of-care metric.

### "Why isn't this a star schema?"

A star schema has fact tables that join only to dimension tables, never to other
fact tables. In this project, `fact_condition.encounter_id` references
`fact_encounter.encounter_id`. That is a fact-to-fact join, which makes the
model a **snowflake** or a **galaxy schema**, not a strict star.

The choice is deliberate: it lets us express "this condition was recorded during
this encounter" without adding a bridge table. It is documented as such in the
README.

### "What's the difference between prevalence and a condition count?"

Prevalence requires a denominator that represents the full population. A
condition count has a denominator of "records that happen to mention this
condition." The two are not the same. This project reports condition counts, not
prevalence.

---

## 4. Deeper questions to be ready for

### "Walk me through what happens when `analytics_queries.sql` runs."

Reads from `healthcare.fact_encounter`, `healthcare.fact_condition`,
`healthcare.dim_patient`, and `healthcare.vw_patient_summary`. Uses window
functions (`LAG`, `ROW_NUMBER`, `DENSE_RANK`, rolling `AVG`), CTEs, and
conditional aggregation. Returns 6 result sets for the analyst to inspect.

### "What's a window function, in your own words?"

A function that looks at a group of related rows and returns a value per row,
without collapsing those rows into one. It's like adding a column that says
"here's what the row above me was" or "here's my rank within my group."

### "What's the difference between `ROW_NUMBER`, `RANK`, and `DENSE_RANK`?"

- `ROW_NUMBER`: 1, 2, 3, 4 — never ties, always sequential.
- `RANK`: 1, 2, 2, 4 — ties share a rank, and the next rank skips.
- `DENSE_RANK`: 1, 2, 2, 3 — ties share a rank, and the next rank does not skip.

### "How would you test these queries?"

- Small unit tests: hand-crafted input rows → expected output.
- Integration tests: run against the full warehouse, assert known invariants
  (e.g., no duplicate IDs, no orphans, totals match source).
- dbt-style data tests if the warehouse is migrated to dbt: `unique`,
  `not_null`, `relationships`, `accepted_values`.

### "If the pipeline reruns tomorrow and produces different counts, does that break anything?"

No — the pipeline is designed to handle a mutable source. The README documents
that the numbers come from one snapshot. The `.gitignore` excludes the raw and
processed data files, so the repo does not carry a specific snapshot as
canonical.

### "What's the difference between a fact table and a dimension table?"

- A **fact table** stores measurable events — one row per event (encounter,
  condition, transaction). It usually has foreign keys to dimensions and
  numeric measures.
- A **dimension table** stores descriptive attributes about an entity — one row
  per entity (patient, product, geography). It is what you filter and group by.

---

## 5. Phrases to use (and avoid)

**Use:**
- "This is a descriptive count, not prevalence."
- "This is a utilization screen, not a readmission measure."
- "The source is public synthetic test data."
- "The dashboard filters to 2000+ because of sparse historical backfill."
- "It is close to a star schema but has one fact-to-fact relationship."

**Avoid:**
- "Real-time"
- "Production-ready"
- "Scalable"
- "Clinically validated"
- "Prevalence" (unless you mean it precisely)
- "Readmission rate" (unless you mean it precisely)
- "AI" or "machine learning"
- "Enterprise-grade"

Those phrases are easy to defend when they're accurate and easy to get caught
on when they're not.

---

## 6. Last-minute checklist before an interview

- [ ] I can describe the pipeline end to end in 60 seconds.
- [ ] I can explain each of the 6 analytical queries without reading them.
- [ ] I can explain why the dashboard filters to 2000+.
- [ ] I can explain why `vw_patient_summary` uses `COUNT(DISTINCT ...)` and
      what I would change.
- [ ] I can explain the difference between `ROW_NUMBER`, `RANK`, and `DENSE_RANK`.
- [ ] I can explain why this is close to but not strictly a star schema.
- [ ] I can explain what the data quality checks look for.
- [ ] I know the numbers: 621 patients, 19,811 encounters, 4,701 conditions.
- [ ] I can name three limitations of the project without prompting.
- [ ] I can name three future enhancements without prompting.

If you can tick all ten, you are ready.