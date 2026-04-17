# OCR-docs Brain

**CONFIDENTIAL — TRADE SECRET**
**OurCommunityRituals LLC**
**Version 1.0.0 — April 2026**

---

## What This Is

This directory contains the machine-readable governance contracts for the OurCommunityRituals platform. These files are not documentation — they are **enforcement mechanisms**. The org-level CI/CD pipeline (`ocr-platform-tests`) parses these files and validates every commit, every deploy, and every data write against them.

**It lives in OCR-docs. It is parseable. It has teeth.**

---

## File Index

| File | Purpose | Enforces Dimension |
|---|---|---|
| `product-registry.yaml` | Every product line registered with identity layer, regulatory pools, tier availability, data contracts, and pipeline activation phase. | 1 (Repo Health), 2 (Data Contract), 3 (Regulatory Pool), 4 (Dataset Routing), 5 (Phase Maturity) |
| `tier-gates.yaml` | Feature and data visibility matrix by tier and phase. Defines what Free, Mid, and Premium customers can see and do at each build phase. | 5 (Phase Maturity), 6 (Product Tier) |
| `corridor-definitions.yaml` | NCR hierarchy definitions. Founding five corridors. Research comparators. Flywheel sequence. | 2 (Data Contract — corridor_id validation) |
| `event-taxonomy.yaml` | All event types with UEC codes, category colors, product origins, and regulatory classifications. | 2 (Data Contract — event_type/uec_code validation), 3 (Regulatory Pool) |
| `bigquery-schemas/general.json` | BigQuery table schemas for the General regulatory pool. | 2 (Data Contract), 4 (Dataset Routing) |
| `bigquery-schemas/hipaa.json` | BigQuery table schemas for the HIPAA regulatory pool. Includes de-identification pipeline spec. | 2, 3, 4 |
| `bigquery-schemas/coppa.json` | BigQuery table schemas for the COPPA regulatory pool. Includes consent records and aggregation thresholds. | 2, 3, 4 |
| `bigquery-schemas/aggregate.json` | The fourth layer. What the RAG reads. De-identified contributions from all three pools. | 2, 3, 4, 6 |

---

## The Six Enforcement Dimensions

Every data point, at every phase, across every product line:

1. **Repo Health** — Is the pipeline green?
2. **Data Contract** — Is the schema conformant for OurEventRing?
3. **Regulatory Pool** — General, HIPAA, or COPPA?
4. **Dataset Routing** — Which BigQuery destination?
5. **Phase Maturity** — What's available at this build stage?
6. **Product Tier** — Free, Mid, or Premium?

Dimensions 1–4 are **hard stops**. No human override. No exceptions.
Dimensions 5–6 are **soft stops** with upgrade and phase-progression paths.

---

## Architecture Summary

```
OurCommunityRituals (Parent Org)
├── OCR-docs ──────── THE BRAIN (this directory)
│
├── ANONYMOUS ID LAYER
│   ├── ourSharedEvents (OSE)
│   └── ourSharedMagnets (OSM)
│
├── PRE-TECH LAYER (no code — community-first → funnel to OSE)
│   ├── ourSharedPulse (OSP)
│   ├── ourSharedRecords (OSR)
│   └── ourSharedGames (OSG)
│
├── NON-ANONYMOUS ID LAYER
│   ├── ourWKRP
│   └── OWL (OurWhiteList)
│
└── ocr-platform-tests ── Enforces the contracts in this directory
```

All roads lead to **OurEventRing** (BigQuery RAG):

```
Nine repos → Three raw pools → One aggregate intelligence layer → One RAG
             (General, HIPAA, COPPA)    (de-identified)           (Vertex AI)
```

---

## Legal Review Required Before

- [ ] HIPAA de-identification pipeline activation
- [ ] COPPA aggregation pipeline activation
- [ ] OurWKRP Spotify competition format (IP clearance)
- [ ] BAA template selection
- [ ] COPPA parental consent mechanism design

---

## Related ADRs

- ADR-001: Platform Architecture (Workers + D1 + Firebase)
- ADR-003: Event Taxonomy
- ADR-007: NCR Methodology
- ADR-009: SharedReports
- ADR-010: Org-Level CI/CD
