# SQL Walkthrough

*A guided explanation of the SQL layer of this project. Written for reviewers
who want to understand how the queries work and why they are structured the way
they are, and for non-technical readers who want to know what the queries
reveal without reading SQL.*

Every query discussed here lives in `sql/analytics_queries.sql` or
`sql/data_quality_checks.sql`. The warehouse tables those queries read from are
created by the scripts in `sql/staging_layer_*.sql`.

---

## 1. Concepts used throughout

### What is a CTE?

A **CTE** (Common Table Expression) is a named block of SQL that starts with
`WITH`. It lets you break a long query into smaller, readable steps instead of
nesting subqueries inside each other.

```sql
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', start_date) AS month,
        COUNT(*) AS n
    FROM healthcare.fact_encounter
    GROUP BY 1
)
SELECT * FROM monthly;
```

Think of it as "define an intermediate result, then query from it." CTEs make
logic easier to test one step at a time and easier to explain to someone else.

### What is a window function?

A **window function** compares each row to other rows *without collapsing them
into a single aggregate row*. Where `GROUP BY` reduces many rows into one, a
window function keeps every row and adds information about its neighbors.

Functions used in this project:

| Function | What it does |
|---|---|
| `LAG(...)` | Looks at the previous row within the same partition |
| `ROW_NUMBER()` | Assigns a unique sequential rank to each row |
| `DENSE_RANK()` | Assigns a rank with no gaps for ties |
| `AVG(...) OVER (ROWS BETWEEN ...)` | Rolling average over a sliding window |

### `NULLIF(value, 0)`

A safety measure. `100.0 * x / NULLIF(y, 0)` returns `NULL` when `y = 0` instead
of raising a division-by-zero error. This matters when a previous-month count
might be zero.

### `FILTER` clause

`COUNT(*) FILTER (WHERE condition)` counts only the rows that match the
condition inside a single aggregation. It is a compact alternative to summing a
`CASE WHEN` expression.

---

## 2. Analytical queries

The full list lives in `sql/analytics_queries.sql`. Each query below is explained
with: the business question it answers, the SQL concepts it demonstrates, how to
read the output, and what it does *not* claim to prove.

### 2.1 Monthly encounter trend

**Business question:** How does encounter volume change month over month, and
is a change sustained or just a one-month spike?

**SQL concepts:** CTE, `LAG`, rolling `AVG` window, `NULLIF`.

**How it works:**

1. The first CTE (`monthly_encounters`) groups encounters by calendar month and
   counts them.
2. The second CTE (`trend`) uses `LAG` to bring the previous month's count next
   to the current month, and a rolling `AVG` over the current and previous two
   months.
3. The final `SELECT` calculates the month-over-month percentage change using
   `NULLIF` to protect against division by zero.

**How to read it:** a positive month-over-month percentage means recorded
encounters increased. The three-month rolling average is smoother than the raw
monthly count and helps separate a sustained trend from a one-month spike.

**Caution:** the dataset includes sparse historical encounters back to 1914. The
Power BI semantic model filters encounters to `Start Date > 2000-01-01` so the
dashboard reflects recent utilization rather than scattered historical records.
This SQL query does *not* apply that filter — it exposes the full history on
purpose so an analyst can inspect the raw shape of the data.

### 2.2 Latest encounter per patient

**Business question:** What is the most recent encounter record for each patient?

**SQL concepts:** `ROW_NUMBER()` partitioned by patient.

**How it works:** every patient's encounters are ranked newest-first. Keeping
rank 1 produces exactly one latest encounter per patient.

**How to read it:** each output row identifies the most recent utilization record
available for one patient. An operations team could use it as an input to a
recency analysis or a follow-up workflow.

**What it does not do:** it does not decide whether a patient needs outreach. It
only surfaces the most recent encounter date on file.

### 2.3 Repeat-utilization bands

**Business question:** How is encounter volume distributed across patients, and
is a small group responsible for most of the activity?

**SQL concepts:** CTE with `CASE` bucketing, `SUM`, `AVG`.

**How it works:** the CTE counts encounters per patient; the outer query places
each patient into a band (1, 2–5, 6–20, 21+ encounters) and aggregates.

**How to read it:** the patient count shows how many people fall in each band,
and the encounter total shows how much activity that band contributes. In this
project's snapshot, 342 of 621 patients fall in the 21+ band, and that band
contributes roughly 80% of total encounters — a typical high-utilization tail.

**What it does not do:** it says nothing about *why* those patients return or
whether the utilization is clinically appropriate. It is an operational
observation, not a clinical judgement.

### 2.4 Encounters within 30 days

**Business question:** How often do patients return within 30 days of a prior
encounter?

**SQL concepts:** `LAG` to retrieve the previous encounter timestamp per patient.

**How it works:** encounters are sequenced per patient by start time. `LAG`
brings the previous start time; the query keeps rows where the gap is 30 days or
less.

**How to read it:** the day difference measures how quickly a patient returned
in the available data. It is a short-interval utilization screen.

**Caution:** this is **not** a clinically validated readmission measure. A
defensible readmission metric would require rules for setting (inpatient vs
outpatient), discharge status, planned vs unplanned visits, and an eligible
population. This query is a first-pass operational signal, not a
quality-of-care metric.

### 2.5 Top five conditions by state

**Business question:** Within each state, which conditions are recorded most
frequently?

**SQL concepts:** CTE, `DENSE_RANK()` partitioned by state, `COALESCE` for
missing values.

**How it works:** conditions are counted per (state, condition) pair, ranked
inside each state with `DENSE_RANK`, and filtered to ranks 1–5.

**How to read it:** rank 1 is the most frequently recorded condition in that
state. Equal counts receive the same rank.

**Caution:** in the current snapshot the only populated state is Massachusetts,
so the query demonstrates reusable SQL logic rather than a meaningful
multi-state comparison. Additionally, "most frequently recorded" describes
documentation frequency, not disease prevalence.

### 2.6 Executive patient summary

**Business question:** What are the headline population and utilization KPIs?

**SQL concepts:** aggregation over a view (`healthcare.vw_patient_summary`),
`FILTER` for conditional counts.

**How it works:** totals and averages are computed over the patient-summary view,
which has one row per patient.

**How to read it:** these are the dashboard-level KPIs. They answer "how many?"
before a user drills into time, location, encounter class, or condition.

---

## 3. Data-quality checks

The full list lives in `sql/data_quality_checks.sql`. Each check is designed so
that **zero rows returned means the check passed**. A non-empty result is the
list of offending rows.

### 3.1 Duplicate primary identifiers

Patient, encounter, and condition IDs are grouped and counted. Any returned row
is an exception because an identifier is expected to be unique inside its
entity.

**Passes when:** zero rows.
**In this project's snapshot:** zero duplicates across all three entities.

### 3.2 Unmatched patient relationships

Encounter and condition rows are left-joined to the patient dimension. If no
match is found, the record is an orphan and would disappear from any visual
that relies on the relationship.

**Passes when:** zero rows.
**In this snapshot:** zero orphans for both fact tables.

### 3.3 Encounter date exceptions

Returns encounters with a missing `start_date` or with `end_date` earlier than
`start_date`. Either case breaks duration and time-trend analysis.

**Passes when:** zero rows.
**In this snapshot:** zero rows.

### 3.4 Completeness summary

Counts rows, then counts nulls for common demographic and condition fields. This
is a **report**, not a pass/fail check.

Missing values are **not** automatically errors. Many FHIR fields are optional.
The point is to make missingness visible so the analyst can decide whether a
field is required for a specific KPI before excluding any records.

**In this snapshot:** gender, birth_date, state, condition_name, and onset_date
are all fully populated.

### 3.5 How to interpret a failing check

A failing check is not necessarily a broken pipeline. It is an *observation*.
The analyst decides whether to:

- Fix upstream data.
- Exclude affected rows from a specific KPI.
- Or accept the records with the missing values documented.

---

## 4. Terminology

A few terms that look similar but mean different things in this project:

| Term | Precise meaning |
|---|---|
| **Descriptive condition count** | The number of times a condition appears in the records. Not the same as disease prevalence, because the denominator is the records, not the population. |
| **Prevalence** | The proportion of a defined population that has a condition at a point in time. Requires a denominator that represents the full population, not just people who visited. |
| **Repeat utilization** | A patient who appears in the fact tables more than once. Purely operational. |
| **Readmission** | A return visit meeting specific clinical and administrative criteria (setting, discharge status, planned vs unplanned). Not derivable from this dataset. |
| **Monthly fluctuation** | A one-month change in a metric. Can be driven by reporting, calendar effects, or data quirks. |
| **Sustained trend** | A directional change visible over multiple months. The rolling average in query 2.1 is designed to surface this. |
| **Missing optional field** | A field FHIR marks as optional that happens to be empty for some records. |
| **Data error** | A value that violates a constraint the analyst has defined as required. Different from a missing optional field. |
| **Star schema** | A dimensional model where every fact table joins directly to dimension tables and not to other fact tables. This project is close but not strictly a star, because `fact_condition` links to `fact_encounter`. |
| **Snowflake schema** | A dimensional model where some dimensions are normalised into multiple related tables. |

---

## 5. Related files

- `sql/analytics_queries.sql` — the executable analytical queries.
- `sql/data_quality_checks.sql` — the executable quality checks.
- `sql/staging_layer_*.sql` — the DDL that builds the warehouse tables.
- `sql/analytics_view_patients_summary.sql` — the patient-level BI view.
- `README.md` — the project overview and results from the documented snapshot.