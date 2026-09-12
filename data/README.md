# Data

## Source

All data in this project comes from the **public SMART Health IT R4 FHIR test
server** at `https://r4.smarthealthit.org`. That server is a publicly accessible
sandbox that exposes synthetic (fake) patient records for developers to practice
against.

**No real patient data is used anywhere in this project.** Nothing in this
repository is clinically valid, and nothing in it should be used to make any
clinical or operational decision about a real patient.

## What lives where

| Folder | Contents | Committed to Git? |
|---|---|---|
| `raw/fhir/` | Full FHIR bundles as downloaded (JSON) | ❌ No |
| `processed/fhir/` | Flattened CSVs produced by the transform scripts | ❌ No |

The `.gitkeep` files inside these folders exist only so that Git preserves the
folder structure. The actual `.json` and `.csv` files are excluded by
`.gitignore` because:

1. They are large.
2. They are regenerable by running the pipeline.
3. They reflect a snapshot of a **mutable** public server — different runs
   produce slightly different data.

## Why the source is mutable

The SMART test server is a shared public sandbox. Developers all over the world
can add records to it. Two people running the same pipeline a week apart may get
different row counts.

This means the **results in this repository describe one documented snapshot**,
not a stable dataset. The README records the snapshot numbers from the run that
was actually validated, and labels them as such.

## How to regenerate the data

From the project root, with the virtual environment activated:

```bash
python src/run_pipeline.py
```