# NCR Brain Promotion Proposal

**Status:** PROPOSED — awaits founder sign-off before any brain edits
**Date:** 2026-05-18
**Author:** Co-Architect (working session with mzdan)
**Sister proposal:** `OCR_DOCS_REORG_PROPOSAL.md` (structural cleanup)
**Note (2026-10-29) [historical record]:** this proposal was written when there were five founding corridors. The roster is now owned by `ocr-docs-brain/corridor-definitions.yaml` (six founding nodes, then Harbor Country). The text below is left as written.
**Scope:** What this proposes — promoting NCR governance from OSE-internal docs into the brain. What it does NOT do — touch any brain file without founder sign-off, change any code, or merge any of the artifacts referenced.

---

## TL;DR

Brain's NCR coverage today is one file (`corridor-definitions.yaml`) reflecting a **NCR v1** 7-level hierarchy. OSE shipped **NCR v2** in migrations 0010–0012 (Mar 2026) with a different 7-level hierarchy, signal taxonomy, lifecycle, and growth model. The substrate moved forward; the brain didn't. Today the substrate is the de-facto source of truth, with full implementation but no machine-readable contract for sibling repos to consume.

The fix: promote NCR from a single brain yaml into a proper brain section (`ocr-docs-brain/ncr/`), driven by NCR v2, with one file per concept and the same drift-check pattern OSE-323 (UEC) and OSE-336 (sponsor-allocation) already use. Then deprecate `corridor-definitions.yaml` after the migration window.

This makes NCR a first-class brain citizen — peer to `architectural-invariants.yaml`, `sponsor-allocation.yaml`, `flags-contract.yaml`. Sibling repos (OSM, ouWKRP, OurAirwaves) consume the same canonical NCR contract OSE does, instead of each rediscovering it.

---

## 1. What exists today (full audit)

### 1.1 Brain (`OCR-docs/ocr-docs-brain/`)

| File | What it covers | Status vs OSE |
|---|---|---|
| `corridor-definitions.yaml` | NCR v1 hierarchy (Venue→Sector→Community→Sub-region→Region→Metro→Network), founding 5 corridors, research comparators, flywheel | **Drifted** — uses v1 hierarchy names; OSE ships v2 |
| `architectural-invariants.yaml` #4 | "NCR Data Accumulation" — enforces poster_deployments lat/lng, scan_aggregates pipeline, permanent storage | OK — invariant is generic |
| `causal-identification.yaml` | Causal identification framework | Adjacent — references NCR but doesn't define it |
| `construct-validity-map.yaml` | Construct validity for research | Adjacent — references NCR but doesn't define it |

### 1.2 OSE substrate (`ourSharedEvents/`)

| Artifact | What it is | Authoritative? |
|---|---|---|
| `docs/adr/ADR-009-ncr-v2-geographic-hierarchy.md` | NCR v2 7-level hierarchy: Community→District→Zone→Metro→Region→Territory→Network. SIGNAL_PRESENCE / SIGNAL_BEHAVIORAL taxonomy. Corridor lifecycle (HYPOTHESIZED→VALIDATED). Directionality (UNI/BI/UNKNOWN). separation_blur_index. SPIDERWEB/FRACTAL/REVERB growth. Wave 1–4 event verticals. | Effective truth for OSE; should be in brain |
| `docs/RING-METHODOLOGY.md` | Full scientific methodology. Part 1 LOCKED, Part 2 DEFERRED. Signal taxonomy, ring emergence criteria, minimum topology. | Effective truth for OSE; should be in brain |
| `docs/features/NCR-METHODOLOGY.md` | Original NCR data pipeline description. Three phases (Event Automation, Pattern Recognition, Geo-Spatial Intelligence). | Should consolidate into brain canonical |
| `config/corridors.js` | Founding corridor seed data (Level 1 communities + Level 5 highway corridors). | OSE-runtime; should consume from brain |
| `migrations/0010_create_ncr_v2_hierarchy.sql` | D1 schema for `node_hierarchy` + `corridors` tables | Implementation of brain contract |
| `migrations/0011_corridor_growth_model.sql` | Adds parent_corridor_id, growth_pattern, reverb_strength, event_verticals, legal_clearance_tier | Implementation of brain contract |
| `migrations/0012_ring_emergence_support.sql` | Renames signal_class CLASS_A/B → SIGNAL_PRESENCE/BEHAVIORAL | Implementation of brain contract |
| `tests/e2e/0-architecture/ncr-accumulation.invariant.spec.ts` | Structural invariant test for #4 | OK — generic accumulation; doesn't depend on hierarchy version |

### 1.3 External city-ID catalog (location to be designated)

There is a 594-U.S.-city ID catalog that pre-dates the brain promotion work, organized into 9 region files (Northeast, South, West, West-CA, Midwest, Midwest-ENC, Midwest-WNC, Territories, plus an index). It is not currently bound to brain or OSE.

This proposal does NOT specify where the catalog physically lives — that's a founder decision (§10 Q6). The point of including it in the audit is: the city catalog exists, it's structural, and the brain's `region-catalog.yaml` should define the CONTRACT for what a valid catalog looks like regardless of the physical home.

### 1.4 Academic framing

| Artifact | Where |
|---|---|
| Condon academic deck (`ncr_condon_academic_2.html`) | Founder-shared; not yet checked into any repo |

---

## 2. The two drifts to resolve

### Drift A — Brain hierarchy is NCR v1, substrate ships NCR v2

| Level | Brain `corridor-definitions.yaml` (v1) | OSE `ADR-009` (v2) |
|---|---|---|
| 1 | venue | community |
| 2 | sector | district |
| 3 | community | zone |
| 4 | sub_region | metro |
| 5 | region | region |
| 6 | metro | territory |
| 7 | network | network |

These are **incompatible names**. A sibling repo reading brain today and writing schema against it would produce data that can't join with OSE's v2 tables. Anyone consuming brain in good faith ships broken integrations.

### Drift B — Six load-bearing concepts are in OSE docs but not in brain

| Concept | OSE source | In brain? |
|---|---|---|
| Signal taxonomy (PRESENCE / BEHAVIORAL) | RING-METHODOLOGY.md §1.1, ADR-009 | No |
| Corridor lifecycle (HYPOTHESIZED → VALIDATED) | ADR-009 | No |
| Corridor directionality (UNI / BI / UNKNOWN) | ADR-009 | No |
| separation_blur_index (0.0–1.0) | ADR-009 | No |
| Growth model (SPIDERWEB / FRACTAL / REVERB) | ADR-009, corridors.js comment | No |
| Event vertical waves (1–4 + regulatory tier mapping) | ADR-009 §Growth Sequence | No |

A sibling repo can't know any of this without reading OSE's internal docs — which is the opposite of how the brain is supposed to work.

---

## 3. Proposed brain structure

Following the precedent set by `bigquery-schemas/` (one subdirectory, one file per pool), promote NCR to its own subdirectory:

```
OCR-docs/ocr-docs-brain/
├── ncr/                         # ← NEW subdirectory
│   ├── README.md                # NCR brain index — what each file owns
│   ├── hierarchy.yaml           # NCR v2 7-level hierarchy (the canonical names)
│   ├── signal-taxonomy.yaml     # SIGNAL_PRESENCE, SIGNAL_BEHAVIORAL definitions + CHECK constraint
│   ├── corridor-lifecycle.yaml  # Status states, directionality, separation_blur_index
│   ├── growth-model.yaml        # SPIDERWEB, FRACTAL, REVERB definitions + invariants
│   ├── event-vertical-waves.yaml # Wave 1–4 + per-wave regulatory tier mapping
│   ├── founding-corridors.yaml  # The 5 founding + 1 research comparator (migrates from corridor-definitions.yaml)
│   ├── region-catalog.yaml      # CONTRACT for the canonical city-ID catalog (physical location TBD)
│   └── ring-emergence.yaml      # Phase 2 deferred analytical criteria (minimum topology, temporal req)
├── corridor-definitions.yaml    # DEPRECATED — pointer to ncr/ contents, removed after one minor version
├── architectural-invariants.yaml
└── (other existing brain files)
```

### Why split, not one big file

- Each concept gets its own drift check (per OSE-323 / OSE-336 pattern).
- Each concept can version independently — `signal-taxonomy.yaml` rarely changes; `founding-corridors.yaml` changes every new activation.
- Sibling repos can consume just the file they need (OSM might only need signal-taxonomy + region-catalog, not founding-corridors).
- Code review is bounded — a PR touching `growth-model.yaml` doesn't bury changes to lifecycle.

### Why `ncr/README.md` at the subdir level

Mirrors `bigquery-schemas/` and the top-level brain README. New contributors land on the file and learn "the brain's NCR section is this set of yamls; here's what each one owns; here's the drift-check that keeps each in sync with OSE."

---

## 4. Per-file content sketch (founder-reviewable before any commit)

Each yaml stays under ~150 lines. The point of this section: founder reads the sketches, comments on what's missing or wrong, then I write the actual content in a follow-on PR.

### `ncr/hierarchy.yaml`
- `schema_version`, `methodology: "NCR v2"`, `replaces: "corridor-definitions.yaml::hierarchy"`
- 7-level enum with name, level number, description, example
- Maps the v1 names as `legacy_alias` so the deprecation window is non-breaking
- Cross-ref: ADR-009 (substrate decision), Brain invariant #4 (accumulation), `migrations/0010_create_ncr_v2_hierarchy.sql`

### `ncr/signal-taxonomy.yaml`
- The two signal classes with full prose definitions
- `corridors.signal_class` CHECK constraint values (`SIGNAL_PRESENCE`, `SIGNAL_BEHAVIORAL`) — sibling repos read this to write their schemas
- Legacy `CLASS_A`/`CLASS_B` mapping for migration window
- What each signal proves and does NOT prove (the analytical guardrail)
- Cross-ref: RING-METHODOLOGY.md §1.1, migration 0012

### `ncr/corridor-lifecycle.yaml`
- State machine: `HYPOTHESIZED → VALIDATED`
- Directionality enum: `UNIDIRECTIONAL`, `BIDIRECTIONAL`, `UNKNOWN`
- `separation_blur_index` definition + valid range
- Validation rules: what evidence promotes from HYPOTHESIZED to VALIDATED

### `ncr/growth-model.yaml`
- SPIDERWEB / FRACTAL / REVERB definitions with the OSE prose preserved verbatim
- Invariant: `growth_pattern` column in `corridors` table CHECK constraint

### `ncr/event-vertical-waves.yaml`
- 4 waves with the verticals each contains
- Per-wave `legal_clearance_tier` (OPEN / RESTRICTED / REGULATED)
- The contract is: a `corridors.event_verticals` array can only include verticals from waves whose `legal_clearance_tier` matches the current platform regulatory pool

### `ncr/founding-corridors.yaml`
- Direct port from existing `corridor-definitions.yaml::founding_corridors`
- Adds NCR v2 hierarchy fields (district, zone, etc.) where v1 had only sub_region/region
- Marks status (`active` for Blue Island, `planned` for the other 4)

### `ncr/region-catalog.yaml`
- **Does not embed** the 594-city catalog (it's structural, not governance — would balloon the brain)
- Defines the contract for what a valid city-ID catalog looks like: format (`node-<slug>` lowercase ascii), regional grouping (9 regions: Northeast / South / West / West-CA / Midwest / Midwest-ENC / Midwest-WNC / Territories / + an index), minimum required fields per city
- Catalog physical home is a separate founder decision (§10 Q6) — could live in `OCR-docs/`, a new dedicated repo, or stay external. The contract is location-agnostic
- Drift check: every city ID referenced anywhere in OSE migrations / seed data must exist in whatever catalog is designated

### `ncr/ring-emergence.yaml`
- Marked `methodology_status: deferred` (mirrors RING-METHODOLOGY.md Part 2 status)
- Captures: minimum topology (3+ nodes, A↔B↔C↔A), bidirectional requirement, temporal requirement (2+ seasons)
- Leaves statistical-validation criteria EMPTY with explicit rationale ("deferred to academic partner") — codifies that the brain says "do not pre-register thresholds here"

---

## 5. Integration with the existing brain

### Update `architectural-invariants.yaml` #4 (NCR Data Accumulation)

Add `depends_on:` reference so the invariant is mechanically tied to the brain's NCR files (mirrors how #5 depends on `tier-gates.yaml`):

```yaml
- id: 4
  name: ncr_data_accumulation
  title: NCR Data Accumulation
  status: live
  test_file: ncr-accumulation.invariant.spec.ts
  enforces: poster_deployments lat/lng. scan_aggregates pipeline. Permanent storage (no PII = no TTL).
  applies_to:
  - ose
  - oureventring
  depends_on:                       # ← NEW
  - ncr/hierarchy.yaml
  - ncr/signal-taxonomy.yaml
  - ncr/corridor-lifecycle.yaml
```

### Update top-level `README.md` file index

Add an NCR row pointing at `ncr/README.md` and update the Architecture Summary to call NCR out as a named brain section (peer to BigQuery schemas).

### Update `ROLLBACK.md` and `TESTING.md`

Add the NCR drift check pattern alongside the existing UEC and sponsor-allocation checks.

---

## 6. Substrate side — OSE consumed copies

Mirror the existing OSE-323 (UEC) and OSE-336 (sponsor-allocation) pattern:

```
ourSharedEvents/workers/oursharedevents/src/lib/ncr/
├── hierarchy.ts                  # mirrors ncr/hierarchy.yaml
├── signal-taxonomy.ts            # mirrors ncr/signal-taxonomy.yaml
├── corridor-lifecycle.ts         # mirrors ncr/corridor-lifecycle.yaml
├── growth-model.ts               # mirrors ncr/growth-model.yaml
├── event-vertical-waves.ts       # mirrors ncr/event-vertical-waves.yaml
└── founding-corridors.ts         # mirrors ncr/founding-corridors.yaml
```

Each file is a tree-shakeable, statically-typed mirror of its brain canonical (ADR-012 pattern). `config/corridors.js` becomes a consumer of `src/lib/ncr/founding-corridors.ts` rather than the primary source.

Drift checks land as `tests/ncr-{name}-drift-check.spec.ts`, following the OSE-336 pattern byte-equivalence-at-the-data-level enforcement.

---

## 7. Sibling repos (the payoff)

Today: OSM, OurAirwaves, ourWKRP cannot wire NCR without reading OSE docs and reverse-engineering.

After this proposal lands:
- OSM reads `ocr-docs-brain/ncr/signal-taxonomy.yaml` → ships its scan handler with the same SIGNAL_PRESENCE/BEHAVIORAL contract
- ourWKRP reads `ocr-docs-brain/ncr/hierarchy.yaml` → its network-graph features use the canonical 7-level names
- A new sibling (OurSharedRecords) reads `ncr/region-catalog.yaml` → can claim a node without inventing a name

The brain becomes load-bearing for NCR exactly the way it already is for UEC, sponsor-allocation, and flags.

---

## 8. Phasing — what ships in what order

| Phase | Output | Blocking? |
|---|---|---|
| P0 — this doc | Founder reviews + sign-off (or comment + revise loop) | Yes — no brain edits before sign-off |
| P1 — brain promotion | `ocr-docs-brain/ncr/` lands with all 8 yaml files. `corridor-definitions.yaml` becomes a deprecation pointer. Invariant #4 gets `depends_on`. | Drives P2/P3 |
| P2 — OSE consumed copies | `workers/oursharedevents/src/lib/ncr/*.ts` files land, mirroring brain. Drift checks added per file. | Brain-substrate alignment complete for OSE |
| P3 — OSE consumer migration | `config/corridors.js` becomes consumer of `src/lib/ncr/founding-corridors.ts`. Removes the v1 hierarchy names from OSE entirely. | Closes Drift A |
| P4 — sibling adoption | OSM and ourWKRP each open PRs consuming `ocr-docs-brain/ncr/*.yaml` into their own `src/lib/ncr/*.ts` mirrors. | Optional, async per sibling |
| P5 — deprecation removal | After 1 minor version with the v1 pointer, remove `corridor-definitions.yaml` entirely. | Closes the migration window |

Linear stories: P1 = NCR-100, P2 = NCR-101, P3 = NCR-102, P4 (one per sibling) = NCR-103/104/105, P5 = NCR-106. Naming follows the `OSE-NNN` pattern but uses `NCR-NNN` to signal cross-repo scope.

---

## 9. Risks I'm naming up front

| Risk | Mitigation |
|---|---|
| Founder disagrees with v2 hierarchy as canonical (wants to keep v1 names) | This proposal makes the hierarchy choice explicit so it gets decided once, in writing, with reasons. The decision belongs to founder; the proposal stays loud about it |
| `corridor-definitions.yaml` is referenced by something we don't know about | Run `grep -r corridor-definitions.yaml` across all 7 OCR repos before P5 deprecation removal; replace each reference |
| Splitting into 8 files inflates contributor cognitive load | `ncr/README.md` is the single landing page; the split is by concept, not by arbitrary slicing. Reviewers diff one file at a time |
| External city catalog binding is fragile (separate-workspace dependency) | The brain's `region-catalog.yaml` defines the CONTRACT; the actual catalog can live anywhere as long as it conforms. If the external location changes, only the catalog moves — the contract is stable |
| Ring emergence criteria get pre-registered in brain (founder's standing concern) | `ncr/ring-emergence.yaml` carries `methodology_status: deferred` AND empty `statistical_validation:` with explicit rationale — codifies "we do NOT pre-register thresholds" in the brain itself |
| Brain change cadence makes drift checks brittle | Same drift-check pattern as UEC and sponsor-allocation. Those have proven robust through multiple changes. Skip-on-missing keeps local dev unblocked |
| Sibling repos adopt at different speeds (some never adopt) | Adoption is opt-in (P4 is per-sibling). Brain stays canonical regardless. A sibling that doesn't consume the brain just doesn't get the contract — same as today |

---

## 10. What I need from the founder

1. **Hierarchy choice confirmation.** NCR v2 (Community→...→Network) as the canonical brain hierarchy, with v1 names as deprecated aliases for one minor version? (My recommendation: yes — v2 is what OSE actually ships and what ADR-009 documents)
2. **Subdirectory location.** `ocr-docs-brain/ncr/` (mirrors `bigquery-schemas/` precedent)? Or different name?
3. **Phasing comfort.** P1 + P2 ship together, or P1 lands first and waits for substrate consumed copies?
4. **Sibling adoption mandate.** Is P4 (OSM/ourWKRP adoption) mandated or opt-in? (My recommendation: opt-in — each sibling adopts when ready)
5. **Linear story naming.** `NCR-100` series, or fold into existing `OSE-` numbering? (My recommendation: `NCR-` — cross-repo scope is exactly what NCR is)
6. **City-ID catalog physical home.** The 594-city catalog needs a designated location for the brain's `region-catalog.yaml` to point at. Options: (a) check it into `OCR-docs/` under a new subdir, (b) new dedicated `ocr-region-catalog` repo at workspace root, (c) embed in `ocr-docs-brain/ncr/region-catalog.yaml` directly (would inflate that file to ~600 entries), (d) leave external with the brain contract documenting the format. My recommendation: (a) — keeps the catalog with the rest of the canonical governance, doesn't bloat the brain index file, and survives any external-workspace reorg.
7. **Condon academic deck integration.** Should the deck be checked into `OCR-docs/docs/references/` as part of P1, or stays out-of-repo for now? (My recommendation: in references/ — the brain should cite the academic framing it depends on)

Once these six are answered, I have everything I need to write the actual P1 brain files for a PR you can merge with confidence.

---

## 11. What does NOT land in this proposal

- No brain edits. Zero. `corridor-definitions.yaml` and the rest are unchanged.
- No code changes. `src/lib/ncr/` doesn't exist yet.
- No deprecations executed.
- No migration written.
- No Linear stories filed.

This is a design doc for founder review. If approved, P1 lands as a separate PR with its own confirmation gate.

---

## Footer

- **Cross-references:**
  - `OCR-docs/ocr-docs-brain/corridor-definitions.yaml` (current canonical)
  - `OCR-docs/ocr-docs-brain/architectural-invariants.yaml` #4
  - `OCR-docs/OCR_DOCS_REORG_PROPOSAL.md` (sister proposal — structural cleanup)
  - `ourSharedEvents/docs/adr/ADR-009-ncr-v2-geographic-hierarchy.md`
  - `ourSharedEvents/docs/RING-METHODOLOGY.md`
  - `ourSharedEvents/docs/features/NCR-METHODOLOGY.md`
  - `ourSharedEvents/config/corridors.js`
  - `ourSharedEvents/migrations/0010_create_ncr_v2_hierarchy.sql`
  - `ourSharedEvents/migrations/0011_corridor_growth_model.sql`
  - `ourSharedEvents/migrations/0012_ring_emergence_support.sql`
  - External 594-city catalog (9 region files; physical home TBD per §10 Q6)
