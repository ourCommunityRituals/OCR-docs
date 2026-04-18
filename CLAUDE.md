# CLAUDE.md — OCR-docs

> **Session protocol**
> 1. Read this file.
> 2. Read `docs/OCR_VISION.md` — the source of truth.
> 3. Execute the task at org level.

---

## What this repo is

OCR-docs is the org brain for OurCommunityRituals LLC. Governance, vision, architecture, and coordination only. **No application code.**

If it is not written in `docs/OCR_VISION.md`, it does not exist at the org level. Do not assert org-level facts that aren't in VISION.md — flag them as drift instead.

---

## Product line — at a glance

| Code | Repo | Data model |
|------|------|------------|
| OCR  | this repo        | Governance |
| OSE  | ourSharedEvents  | Anonymous ID |
| OW   | ourWKRP          | Named identity |
| OSG  | ourSharedGames   | Inherits OSE |
| OSR  | ourSharedRecords | Archive / oral history |
| OSP  | ourSharedPulse   | Human-delivered, tech-optional |
| OSM  | ourSharedMagnets | Developer / franchise |
| OER  | —                | Intelligence / analytics |
| OA  | ourAirwaves     | Deployment / white label |

Full registry with per-product detail → `docs/OCR_VISION.md §6`.

---

## Architectural boundaries

Architecture is the Triangle + 4 invariants + 4 governance files per repo. Source of truth lives in code at `ourSharedEvents/tests/e2e/0-architecture/`. This document mirrors what the tests enforce. Full prose in `docs/OCR_VISION.md` (Architecture section).

**The Triangle.** `Sponsor → Event ← Customer` with `SharedReport` derived. Any entity plugs into any corner. The Triangle enforces HOW entities participate, not WHAT they are.

**The ten invariants.** Status legend: ✅ in code · ⚙️ partial (CI gate or related tests; promote to 0-architecture suite) · 📋 proposed.

1. ✅ **Anonymous ID** — Zero-PII, two-DB separation (DB / FORMS_DB), `ose_anon` cookie contract, no cross-linking.
2. ✅ **Hyper-local Geo-Resolution** — `sponsor_areas` + `sponsor_event_types`, corridor-level resolution, zip+radius matching.
3. ✅ **UEC Encoding** — 7 color-semantic QR codes (Blue `#1A3A8A` = SPONSOR) + 4 extensions.
4. ✅ **NCR Data Accumulation** — `poster_deployments` lat/lng + `scan_aggregates` pipeline, permanent storage (no PII = no TTL).
5. 📋 **Tier Equity / Pricing Governance** — pricing tiers govern display priority only, never platform access. Same QR / forms / privacy / counts at every tier. Local stays in at all flag levels.
6. ⚙️ **Inert Monetization Hooks** — `X-Monetization-Inert: true` header on every response. Existing CI gate `checkMonetizationHooksInert` already enforces.
7. 📋 **Aggregate-Only Reporting** — SharedReports return aggregates only, never individual rows.
8. ⚙️ **Bounded PII Retention** — every opt-in PII column has a TTL; daily lifecycle cron deletes/scrubs on schedule.
9. ⚙️ **Tenant Isolation** — dual-key (`id` + `brandId`) on multi-tenant tables; no cross-tenant leakage.
10. ⚙️ **Deprecation Lock** — once a runtime is removed (GAS today; HTML/Phase-3 future), CI forbids its re-introduction. Generalizes `scripts/guard-no-gas.js`.

**The four governance files per repo.** Every repo maintains `CLAUDE.md`, `docs/OCR_VISION.md`, `README.md`, `SKILL.md`.

**Derived patterns Claude enforces:**

- **OSM + OA is one flywheel.** OSM = back (API, skills, CI). OA = front (fork, onboarding, environment). Together they spin up new entity instances that inherit all four invariants by construction.
- **OSE and OW are parallel platforms, not one merged service.** Same architecture, separate databases, opposite identity invariants (OSE anonymous-by-construction; OW named with voluntary attribution). "Converge under the OCR moniker" = shared architecture and brand, NOT merged data. Cross-platform features are per-record decisions.
- **OA serves at every scale.** Corridor, partner, venue, AND individual creator (every DJ profile is a single-person OA deployment).
- **OER is the BigQuery RAG.** All qualifying product DBs (OSE, OW, OA, OSM) feed it. Products do not query each other's DBs directly — they emit, OER ingests, OER answers.
- **OSP has no anonymous ID dependency.** Human-delivered. Tech-optional entry point.
- **File and folder naming is architectural.** `OCR_<TYPE>_<subject>.md` camelCase. Canonical `docs/` subfolders: decisions, standards, corridors, releases, prompts, ccr-gates.
- **Simplicity over completeness.** Code is the source of truth. When code and docs disagree, code wins.

---

## CCR protocol

All production-grade decisions across the OCR product line are governed by **CCR — Critical, Conservative, Recursive**.

- 3 layers: Critical, Conservative, Recursive
- 3 loops minimum per review
- **95% confidence gate** — below that, human gate activates
- Artifacts are earned, not generated
- Prompts are data — the input is part of the artifact chain

Full spec: `skills/ccr-protocol.knowledge.md`.

---

## Pointers (not copies)

To avoid drift, Claude should not duplicate these from VISION.md here:

- **The Triangle and four invariants (source of truth)** → `ourSharedEvents/tests/e2e/0-architecture/` (executable specs) and `docs/OCR_VISION.md` (Architecture section, prose mirror)
- **Four governance files per repo** → `docs/OCR_VISION.md` (Architecture section, governance-files subsection)
- **OSM + OA flywheel** → `docs/OCR_VISION.md` (Architecture section)
- **OSE / OW platform symmetry** → `docs/OCR_VISION.md` (Architecture section)
- **Data flow / OER as BigQuery RAG** → `docs/OCR_VISION.md` (Architecture section)
- **Product registry** → `docs/OCR_VISION.md` (Product registry)
- **Founding corridors** → `docs/OCR_VISION.md` (Founding corridors)
- **Archive commitment** → `docs/OCR_VISION.md` (Archive commitment)
- **NCR methodology** → `docs/OCR_VISION.md` (NCR methodology) · full doctrine in `LOCKED_NCR_Methodology_v1.3`
- **Open decisions** → `docs/OCR_VISION.md` (Open decisions)

---

*Last updated: 2026-04-14 (v2 — de-duplicated against VISION.md)*
*Owner: Matt*
*Status: DRAFT — awaiting review.*
