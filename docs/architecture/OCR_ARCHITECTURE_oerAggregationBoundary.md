# OER Aggregation Boundary Specification

**Document ID:** OCR-ENF-24
**Status:** Ratified — 2026-08-02
**Owner:** OurCommunityRituals LLC (org-level)
**Scope:** All OCR product repos — OSE, OW (WKRP), OA (OAW), OSM
**Related Linear:** OSE-390 (F5c)

---

## 1. Purpose and scope

This document defines the **OER Aggregation Boundary**: the precise contractual seam between OurEventRings (OER) and every product that feeds it. It specifies what may cross, what may never cross, how it crosses, and who governs changes.

OER is the BigQuery RAG (retrieval-augmented generation) intelligence layer for the OCR org. It answers cross-product questions that no single product database can answer alone. Its integrity depends on a strict, audited boundary: products emit qualifying data into OER; OER ingests and answers; products never query each other's databases directly.

**This document is the single source of truth for that boundary.** Every architectural decision that touches cross-product data flow must be reconcilable with the rules here or must update this document via a PR to `ourCommunityRituals/OCR-docs` before the code lands.

---

## 2. The boundary defined

```
┌─────────────┐    emit (HTTP / batch)    ┌─────────────────────┐
│   OSE       │ ─────────────────────────▶│                     │
│   OW/WKRP   │ ─────────────────────────▶│   OER (BigQuery)    │
│   OA/OAW    │ ─────────────────────────▶│   RAG + Analytics   │
│   OSM       │ ─────────────────────────▶│                     │
└─────────────┘                            └─────────────────────┘
       │                                            │
       │ ◀──────── cross-product answers ───────────┘
       │             (OER API only)
       │
       │ ✗  direct DB query (prohibited)
       │ ✗  Worker service binding (prohibited)
       │ ✗  module import (prohibited — Invariant #22)
```

**The boundary is unidirectional at the data layer.** Products push qualifying data to OER. OER answers cross-product questions. Products consume OER answers through OER's own API — they never bypass OER to reach a sibling product's database.

The **one documented exception** at the HTTP layer is the music API seam: `GET /api/events/:id/music` (WKRP exposes, OSE calls via HTTP fetch). This seam is frozen, covered by a Pact contract test (OSE-423), and explicitly permitted by Invariant #22. No new HTTP seams may be opened between product repos without a corresponding brain PR that adds them to Invariant #22's permitted seam list.

---

## 3. Privacy classes — what qualifies for OER emission

Every field that crosses into OER must be classified before it emits. There are two qualifying privacy classes and one disqualifying class.

### Class A — Anonymous-by-construction (OSE class)

Data qualifies if it carries no identifier that can, alone or in combination with other OER-resident fields, be linked to a natural person.

| Qualifying property | Requirement |
|---------------------|-------------|
| IDs | `anon_` prefixed, opaque, no session-to-person linkage |
| Timestamps | Bucketed to hour-level minimum (no sub-hour resolution) |
| Location | Corridor-level only (`corridor_id`); no exact lat/lon |
| Aggregates | Counts only; no individual-row payloads |
| Behavior | Scan codes, form type, party size — never free-text content |

### Class B — Named-with-explicit-voluntary-attribution (OW/WKRP class)

Data qualifies if the user explicitly opted into named participation and the consent record is present in the source system.

| Qualifying property | Requirement |
|---------------------|-------------|
| Identity fields | Must be tied to an active, non-revoked consent record |
| Attribution | `voluntary_attribution: true` flag must be present in the source row |
| Scope | Scoped to the specific curation event — no profile-wide aggregation without a separate consent record |

### Class X — Disqualified (never emits)

| Disqualified data | Reason |
|-------------------|--------|
| Raw email addresses | PII; not anonymous-by-construction |
| IP addresses (raw or hashed with weak pepper) | Re-identifiable |
| Free-text form responses | Uncontrolled PII surface |
| `FORMS_DB` rows of any kind | Identified-user surface; OSE Invariant #1 |
| Cross-tenant join results | Violates Invariant #9 tenant isolation |
| Any field lacking a declared privacy class | Disqualified until classified |

---

## 4. Emission contract per product

### 4.1 OSE — OurSharedEvents (anonymous class)

OSE emits **aggregate behavioral data only**. No individual-row payloads cross the boundary. Every emitted field is Class A.

| Emission dataset | Fields | Granularity | Privacy gate |
|-----------------|--------|-------------|--------------|
| Event index | `event_id`, `brand_id`, `corridor_id`, `status`, `start_date`, `end_date`, `legal_clearance_tier` | Per event | No PII; no location below corridor |
| Scan aggregates | `event_id`, `uec_code`, `hour_bucket`, `count` | Per event × code × hour | Hour-bucket enforced |
| Form submission counts | `event_id`, `form_type`, `hour_bucket`, `count` | Per event × form type × hour | Count only — no anon_id |
| Poster deployment signals | `event_id`, `corridor_id`, `deployment_count` | Per event × corridor | No exact lat/lon |
| Sponsor tier signals | `event_id`, `sponsor_tier`, `sponsor_area`, `active_count` | Per event × tier × area | No sponsor identity |
| SharedReport summary | `event_id`, `total_scans`, `total_registrations`, `avg_rating` | Per event | Aggregate only |

**Fields that may never emit from OSE:**
- `anon_id` (individual anon visitor identifiers)
- `lat` / `lon` below corridor resolution
- Any `FORMS_DB` field
- `email_hash`, `email_encrypted`
- `ip_hash`
- Free-text survey content (even via `comment_length`)

### 4.2 OW / WKRP — OurWKRP (named-with-attribution class)

OW emits **voluntarily attributed curation signals** only. The consent record must pre-exist in OW's source system before any attributed field qualifies.

| Emission dataset | Fields | Granularity | Privacy gate |
|-----------------|--------|-------------|--------------|
| Curation signals | `event_id`, `curator_id` (opaque handle), `music_tag`, `timestamp_bucket` | Per curation event × tag × hour | `voluntary_attribution: true` required |
| Community engagement | `event_id`, `engagement_type`, `count` | Per event × type | Aggregate only; no curator_id at aggregate level |
| Named profile signals | `profile_id` (opaque), `ritual_tags[]`, `consent_scope` | Per active consent record | Revocation must propagate to OER within 24 h |

**Fields that may never emit from OW:**
- Raw usernames or display names
- Email addresses
- Any field linked to a consent record that has been revoked
- WKRP × OSE cross-table join results

### 4.3 OA / OAW — OurAirwaves (deployment signals)

OA emits **deployment-tier telemetry** only. No client data crosses the boundary — OA is the white-label deployment layer, so its OER contribution is structural, not behavioral.

| Emission dataset | Fields | Granularity | Privacy gate |
|-----------------|--------|-------------|--------------|
| Deployment registry | `deployment_id`, `corridor_id`, `tier`, `activation_date` | Per deployment | No client PII |
| Ritual adoption signals | `corridor_id`, `ritual_type`, `period_bucket`, `instance_count` | Per corridor × ritual × month | Aggregate only |

OA emission is **deferred until OAW is active.** The contract is defined here so the boundary is locked before implementation begins.

### 4.4 OSM — OurSharedMagnets (API usage telemetry)

OSM emits **API usage and ritual telemetry** only. It is the developer/franchise API layer; its OER contribution helps OER answer "which rituals are scaling across deployments."

| Emission dataset | Fields | Granularity | Privacy gate |
|-----------------|--------|-------------|--------------|
| API usage by ritual | `api_key_hash` (opaque), `ritual_type`, `period_bucket`, `call_count` | Per key × ritual × day | Hash only — no raw API key |
| Franchise adoption | `franchise_id` (opaque), `corridor_id`, `deployment_tier`, `active_since` | Per franchise | No operator PII |

OSM emission is **deferred until OSM is active.**

---

## 5. Prohibited patterns — what may never cross

The following are unconditional prohibitions. No story, no shortcut, no "just this once" exception is valid without a brain PR that **explicitly revises this section** — not a comment, not a Slack message, a merged PR.

| Prohibited pattern | Invariant that enforces it | Why |
|-------------------|---------------------------|-----|
| Direct D1 binding to a sibling product's database | Invariant #17 (oer_emission_boundary) | Bypasses all privacy gates; allows raw row access |
| Worker-to-Worker service binding across product repos | Invariant #17 | Opens RPC channel that proxies raw DB access |
| Module-level `import` / `require` across repo boundary | Invariant #22 (cross_repo_import_isolation) | Code coupling destroys the isolation architecture |
| New HTTP seam between product repos (undocumented) | Invariant #22 | Every seam must be named, frozen, and Pact-tested |
| Emitting a `FORMS_DB` field to OER | Invariant #1 (anonymous_id) | Identified-user surface — destroys OSE's anonymous guarantee |
| Emitting sub-hour timestamps | Invariant #4 (ncr_data_accumulation) | Fine-grained timing enables behavioral fingerprinting |
| Emitting individual anon_id rows | Invariant #1 | Longitudinal tracking across events |
| Cross-tenant join before emission | Invariant #9 (tenant_isolation) | Join bypasses brand isolation; exposes one brand's data to another's OER slice |
| OER answering a query by proxying a direct DB call back to a product | (architectural) | Negates the decoupling; products become dependent on OER's internals |

---

## 6. Emission mechanism

### 6.1 Permitted mechanisms

| Mechanism | When to use | Notes |
|-----------|------------|-------|
| **Scheduled HTTP export** | OSE → OER ingest endpoint; runs as a Cloudflare scheduled Worker job | Preferred for OSE aggregate exports; no persistent connection required |
| **BigQuery load job (batch)** | OW / OA / OSM batch telemetry | GCS staging area → BigQuery load; latency-tolerant |
| **Cloudflare Queues** | Near-real-time OSE scan aggregate streaming | Queues → OER ingest Worker → BigQuery; decoupled, durable |

### 6.2 Prohibited mechanisms

| Prohibited | Reason |
|-----------|--------|
| Direct D1 → BigQuery connector (no Worker intermediary) | Bypasses the privacy qualification gate; raw rows cross unfiltered |
| Worker service binding between OSE and OER ingest | Prohibited by Invariant #17 |
| Shared database instance accessed by both a product and OER | No shared mutable state across the boundary |
| OER reading from a product's D1 via the D1 HTTP API | Treated equivalently to a direct binding — prohibited |

### 6.3 Pre-conditions for OSE emission activation

OSE emission to OER is **not yet active**. Before the first byte crosses:

- [ ] OER BigQuery project provisioned with OSE-specific dataset and schema
- [ ] OSE emission endpoint implemented (Cloudflare scheduled Worker job)
- [ ] Privacy qualification gate code-reviewed against §3 of this document
- [ ] Pact-style contract test for the OSE → OER emission schema (field names, types, absence of Class X fields) in CI
- [ ] Brain enrichment_history entry written documenting activation date and PR refs
- [ ] `status_summary` in `architectural-invariants.yaml` updated to reflect OER emission live

---

## 7. OER ingestion model — what questions OER answers

OER answers cross-product questions that no single product database can answer. It does **not** serve as a query proxy for individual products. If a question can be answered within one product's own data, it must be answered there.

### Cross-product questions OER is designed to answer

| Question | Required datasets |
|----------|-----------------|
| Which corridor types produce the highest ritual retention? | OSE scan aggregates + OW curation signals + OA deployment signals |
| What sponsor tier mix correlates with highest SharedReport scores? | OSE sponsor signals + OSE SharedReport summaries |
| Which ritual formats scale across franchise deployments? | OSM franchise adoption + OA deployment registry |
| Voluntary community attribution trajectory over time | OW named profile signals (Class B only) |
| Cross-corridor ritual diffusion pattern | OSE event index + OA deployment registry |

### Questions OER must refuse to answer

| Refused question | Reason |
|-----------------|--------|
| Identity of a specific anon_id | Prohibited — Class X |
| Which specific person attended which event | Prohibited — Class X |
| Email address or contact info of any attendee | Prohibited — Class X |
| Raw event rows from a specific brand (cross-tenant) | Prohibited — Invariant #9 |
| Any query whose answer exposes a FORMS_DB field | Prohibited — Invariant #1 |

---

## 8. Governance — adding a new emission field

Every new field added to an OER emission dataset must follow this process. No exceptions. The PR that adds the field to application code must contain all of the following:

### Step 1 — Classify the field

Assign it to Class A (anonymous), Class B (named-with-attribution), or Class X (disqualified). Disqualified fields may not proceed. Document the classification in the PR description.

### Step 2 — Update this document

Add the field to the relevant table in §4. State the granularity and the privacy gate. The PR to `ourCommunityRituals/OCR-docs` must be merged or open as a linked PR before the application code lands in `main`.

### Step 3 — Update `architectural-invariants.yaml`

Add an `enrichment_history` entry to the affected invariant (typically #17 or #22) documenting:
- `date` of the change
- `field_name` and `privacy_class`
- `rationale`
- `pr_refs` (both the product PR and the OCR-docs PR)

### Step 4 — Add or update the emission contract test

The CI for the emitting product must contain a test that asserts the field is present in the emission payload AND that no Class X field is co-emitted. No field ships to OER without a test that would catch a future regression.

### Step 5 — Review against the prohibition matrix (§5)

Confirm the field does not appear in any row of the prohibited patterns table. If it does, the PR must update §5 and carry an explicit architectural decision record in `docs/adr/`.

---

## 9. Invariant matrix

| Rule | Invariant | Enforcement mechanism |
|------|-----------|----------------------|
| No cross-product D1 binding | #17 oer_emission_boundary | `oer-emission-boundary.invariant.spec.ts` — wrangler.toml binding shape gate |
| No Worker service binding | #17 | Same spec — `[[services]]` stanza prohibition |
| No module-level cross-repo imports | #22 cross_repo_import_isolation | `check-cross-repo-imports.sh` in `brain-contract-check.yml` |
| No new undocumented HTTP seam | #22 | Pact test required per seam; seam must be named in Invariant #22 references |
| No FORMS_DB field emits | #1 anonymous_id | OSE anonymous ID invariant; DataProvider never exposes FORMS_DB |
| Hour-bucket minimum on timestamps | #4 ncr_data_accumulation | Enforced in OSE `mock-data.ts` fixture convention; to be enforced in emission gate |
| No cross-tenant join before emission | #9 tenant_isolation | Structural + runtime isolation gate (tenant-isolation.invariant.spec.ts) |
| OER answers only via its own API | #17 (architectural) | No mechanism exists to bypass — enforced by the absence of cross-product bindings |

---

## 10. Change log

| Date | Change | PR | Author |
|------|--------|----|--------|
| 2026-08-02 | Initial ratification — full boundary contract, 4 product emission contracts, prohibition matrix, governance protocol | OCR-docs PR #72 | OCR co-architect |

---

## 11. Pre-conditions for OER activation

OER does not exist as a deployed system yet. This document ratifies the boundary **before** implementation so that every product repo builds toward a known contract. Activation requires:

1. OER BigQuery project provisioned at the OCR org level
2. OSE → OER emission endpoint implemented and CI-tested (contract test per §8 Step 4)
3. OW → OER emission endpoint implemented and CI-tested
4. OER API defined and versioned (OER answers cross-product questions; OSE/OW never bypass it)
5. Linear epic created for OER activation with this document as the acceptance criteria reference
6. `architectural-invariants.yaml` Invariant #17 enrichment_history entry recording the activation date

Until these conditions are met, this document functions as a **pre-implementation contract** that governs how each product is built — not a description of live infrastructure.

---

*Canonical location: `ourCommunityRituals/OCR-docs/docs/architecture/OCR_ARCHITECTURE_oerAggregationBoundary.md`*
*Any copy of this document outside OCR-docs is informational only — this file governs.*
