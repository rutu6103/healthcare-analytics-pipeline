# Dashboard Guide

This Power BI report contains six pages: five analytical views plus one drillthrough.

## Executive Overview

Population size, total encounters, total conditions, average utilization, repeat-patient rate, and encounter growth. Designed as the starting point before drilling into a specific view.

**Answers:** How big is this population, how active is it, and how much of the activity is repeat vs. one-time?

## Patient Population Insights

Who appears in the data and how heavily they use the system. Age-group distribution and top cities by patient count.

**Answers:** What are the demographic characteristics of the patient population, and where are they concentrated?

## Encounter Utilization Analysis

When encounters occurred and how they are distributed by class. Ambulatory dominance, encounter volume trend, and top cities by encounters.

**Answers:** When is the system being used, and which encounter types dominate?

## Condition & Disease Analysis

Recorded conditions ranked by frequency, age-wise average conditions per patient, clinical status distribution, and top cities by condition.

**Answers:** What conditions are recorded most often, and how do they vary by demographics?

## Data Quality Monitoring

Load freshness, row counts, and table counts from the ETL log.

**Answers:** When did data last arrive, how much arrived, and did the load succeed?

## City Drillthrough

Right-click drillthrough from the Patient Population page. Shows city-scoped patient, encounter, and condition counts.

**Answers:** What does the data look like for a specific city, filtered from the main view?

## Notes

- The report filters encounters and conditions to records from 2000 onward.
- Pre-2000 records exist in the warehouse but are excluded from the semantic model.
- Condition counts describe recorded documentation, not disease prevalence.