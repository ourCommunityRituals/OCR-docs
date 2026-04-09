# Decision: OCR-6 Mock Data Provider vs OSE MOCK-1

> **Status:** DECIDED — OSE builds MOCK-1 first, OCR-6 inherits
> **Flagged by:** Bloodraven sync (2026-04-09) — duplication risk
> **Stakeholders:** PO / OCR + OSE

---

## The problem

Two teams have urgent backlog items for mock/demo data:

- **OCR-6** (OCR-docs): org-level mock data provider
- **OSE-146/147/148** (MOCK-1): configurable demo environment for OSE

If both build independently, the implementations diverge. Integration debt accrues. Per OCR_DEPENDENCY_crossRepo.md, OSM's Postman collections and Newman CI depend on OSE's feature flag configuration — a shared mock standard prevents sync drift.

---

## Decision

**OSE builds MOCK-1 first. OCR-6 extracts and formalizes the working pattern.**

---

## Rationale

### OSE already has working mock infrastructure

| Asset | Location | Status |
|-------|----------|--------|
| Postman mock endpoint | `postman/environments/ocr-ose-mock-stg.environment.yaml` | Active |
| D1 seed migration (test event) | `migrations/0013_seed_test_event.sql` | Deployed |
| D1 seed migration (32 templates) | `migrations/0015_seed_event_templates.sql` | Deployed |
| Test fixtures | `tests/shared/fixtures/` (events, analytics, sponsors, templates) | Active |
| Feature flag tiers | Free / Mid / Enterprise (controls demo visibility) | Active |

Starting OCR-6 from scratch would re-implement all of the above and create two systems to maintain.

### The extraction path is clear

Once OSE-146/147/148 are complete, OCR-6 formalizes:

| Aspect | Org-level (stable) | Product-level (varies) |
|--------|-------------------|----------------------|
| Schema version | D1 migration format, idempotent seeding | Event details, sponsor brands |
| Tier mapping | Free=2, Mid=5, Enterprise=15 sponsors | Which sponsors per tier |
| Seeding pattern | `INSERT OR IGNORE`, safe for re-runs | Template selection, event count |
| Testing | Newman CI gate + E2E smoke per tier | Product-specific assertions |

### Risk comparison

| Scenario | Risk |
|----------|------|
| OSE first → OCR-6 extracts | Low — real working code to generalize from |
| OCR-6 first → OSE consumes | High — generic interface may not fit D1 patterns; OSE refactors twice |
| Both in parallel | High — parallel builds, sync debt, per OCR_DEPENDENCY_crossRepo.md |

---

## Execution sequence

### Step 1: OSE builds MOCK-1 (OSE-146/147/148)

OSE delivers:
- Tier-aware demo endpoint (sponsor count controlled by feature flag tier)
- Demo seeding migrations (idempotent, per D1 standard)
- Postman collection updated for all three tiers
- Newman CI validates demo consistency

### Step 2: OCR-6 extracts the standard

OCR-docs formalizes:
- Mock data interface specification (what varies vs what stays stable)
- Org-level seeding contract (schema version, tier mapping, idempotency rules)
- Shared testing expectations (Newman gate per tier)
- Documentation in `docs/standards/`

### Step 3: OSM inherits

Per OCR_DEPENDENCY_crossRepo.md, OSM's Postman collections and Newman CI update to match the formalized contract. Franchise operators get consistent demo environments across tiers.

---

## What this unblocks

- **OSE-146**: MOCK-1 configurable demo environment — can start immediately
- **OSE-147/148**: dependent MOCK-1 stories — sequence after 146
- **OCR-6**: moves from "build" to "extract" — lower effort, higher quality
- **OSM-1** (partially): franchise layer needs demo environments for operator testing

---

*Decided: April 9 2026*
*Owner: Matt*
*Status: DECIDED*
