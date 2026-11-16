# bigquery-schemas

What this folder holds, and what it does not.

## What the four files are

`general.json`, `hipaa.json`, `coppa.json` and `aggregate.json` are the **design** of
the pool datasets: version 1.0.0, dated 2026-04-15. HIPAA and COPPA are declined
regimes (`docs/standards/OCR_STANDARD_declinedRegimes.md`); their files are kept as
records of what is refused.

## What a product writes today lives in that product's code

The column list of a table a product writes to BigQuery has one home: the code that
builds the row. This folder names those tables and points to that code. It does not
copy their columns, so it cannot drift from them.

OurSharedEvents writes four tables. Each pool's dataset gets its own copy
(`datasetForPool` in `workers/oursharedevents/src/lib/pool-contract.ts`).

| Table | Name is set in | Rows are built in |
| --- | --- | --- |
| `events_backup` | `src/cloud/bigquery.ts`, `BACKUP_TABLES.events` | `src/handlers/bigquery.ts` |
| `corridor_returns_export` | `src/lib/shared-report-export.ts`, `BQ_TABLE_CORRIDOR_RETURNS` | same file, `exportAnonIdReturns` |
| `corridor_density_baseline_export` | `src/lib/shared-report-export.ts`, `BQ_TABLE_CORRIDOR_DENSITY` | same file, `exportCorridorDensityBaseline` |
| `event_series_export` | `src/lib/shared-report-export.ts`, `BQ_TABLE_EVENT_SERIES` | same file, `exportEventSeries` |

Paths are under `workers/oursharedevents/` in the ourSharedEvents repo.

Method (ourSharedEvents `main` at `f2c98fd`, read 2026-11-15):

```bash
git grep -n "BQ_TABLE_\|BACKUP_TABLES" origin/main -- workers/oursharedevents/src
```

That search shows three `BQ_TABLE_` constants, each with its name on the same line,
and the `BACKUP_TABLES` object, whose one entry (`events: 'events_backup'`) is on the
line below its opening (`src/cloud/bigquery.ts`, lines 28 to 30). Four names in all.
No other product's code was searched.

`event_series_export` carries each confirmed series' name. The owner decided on
2026-11-14 that a series name may leave OurSharedEvents in this table.

## Known gap, not settled here

The table names in `general.json` (`events`, `qr_scans`, `funnel_conversions`,
`corridor_density`) are not the names the code writes. Method:

```bash
python3 -c "import json;print(list(json.load(open('ocr-docs-brain/bigquery-schemas/general.json'))['tables']))"
```

Which side is right is an open question tracked in Linear: OSE-1460 (what the export
sends), OSE-255 (drift detection between D1 and BigQuery) and OCR-24 (the pool
contract). This file records the gap and changes neither side.
