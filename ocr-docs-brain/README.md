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
| `corridor-definitions.yaml` | NCR hierarchy definitions. The six founding nodes, then Harbor Country as the network destination. Research comparators. Flywheel sequence. | 2 (Data Contract — corridor_id validation) |
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

## ADR to invariant edge

An invariant and the ADR behind it point at each other, and `scripts/check_adr_edges.py` checks that both sides agree on every brain CI run (`brain-validate.yml`).

**Qualified IDs.** An ADR is named `<scope>:ADR-NNN`: `fleet:ADR-002` is in `OCR-docs/docs/adr/`, `ose:ADR-009` is in `ourSharedEvents/docs/adr/`.
The scopes are listed under `adr_scopes` in `product-registry.yaml`.
The fleet scope is read straight from `docs/adr/`; every other scope is read from its committed index in `adr-indexes/`, which holds only ADR ids, status and declarations, never code.

**Invariant side.** `references.adr` in `architectural-invariants.yaml` is a list of qualified IDs, for example `adr: [ose:ADR-009]`.
Other ADR-flavoured keys (`adr_coordination`, `adr_tier_axis`, `ose_adr` and the like) are commentary, not edges.

**ADR side.** An ADR declares its invariants with `**Enforced-by:** invariant #N, #M` (or `**Enforced-by:** none - <reason>`) in its first 30 lines; OSE's `## Enforced by invariants` section is read too; an `Invariants touched:` bullet is not, because it names invariants an ADR touches, not ones it is enforced by.
The forms are set out in `docs/adr/README.md` under "Numbering".

**The rules.**

- E1 unresolved: an invariant names an ADR whose scope is not in `adr_scopes`, or whose number is not in that scope.
- E2 bare: a `references.adr` value is not a qualified ID (an old path string counts).
- E3 one-sided: an invariant lists an ADR that has declared its invariants, and that ADR does not name it back.
- E4 one-sided: an ADR names an invariant that does not exist or does not list the ADR back (a retired invariant may be named, but is not required to list it).
- E5 undeclared: a fleet ADR has no declaration and is not on the ratchet, or is on the ratchet but now has one.
- E6 ratchet: a live invariant has no ADR and is not on the ratchet, or is on the ratchet but now has one, or the ratchet holds an id above its ceiling.
- E7 status (report only, never fails): an invariant lists an ADR that is not `Accepted`.

E3 and E4 skip ADRs with no declaration and say how many they skipped.
The check prints one line per rule and writes `adr-edge-report.json` (not committed).

**Clearing a ratchet entry.** `adr-edge-ratchet.json` holds the debt that predates the check: invariants with no ADR yet, and fleet ADRs with no `Enforced-by` yet.
To clear one, assign the edge on both sides in the same change: add the qualified ID to the invariant's `references.adr` and name the invariant in the ADR's `Enforced-by` line, then remove the id from the ratchet.
The check fails if an entry is left on the ratchet after its edge exists, so a stale entry cannot stay.
A new invariant cannot join the invariant list (ids above `frozen_max_id` are rejected), but the check does not compare either list with the base branch, so a reviewer must reject any other addition to them.
`frozen_max_id` is the ceiling: no invariant numbered above it can be added to the ratchet, so every new invariant must carry an ADR.

---

## Related ADRs

- ADR-001: Platform Architecture (Workers + D1 + Firebase)
- ADR-003: Event Taxonomy
- ADR-007: NCR Methodology
- ADR-009: SharedReports
- ADR-010: Org-Level CI/CD
