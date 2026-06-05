# ADR-004: Role-Ready Invariants — Schema Extension for SCRUM Execution

**Status:** Proposed
**Date:** 2026-06-01
**Amended:** 2026-06-05 (pre-acceptance — CCR of the #14 `mobile_workability` proof point surfaced a self-contradictory null convention; see Changelog)
**Deciders:** Matt (Co-Architect convener)
**Supersedes:** None
**Cross-refs:** ADR-002 (Identity-Profile-Keyed Invariants — Phase 1 bundle target), ADR-003 (Self-Checking Infrastructure — the operational doctrine this ADR specifies for execution)

---

## Context

The brain's architectural invariants today are *structurally* ready — they pass
the conformance check, they catch phantoms, they declare scope. They are NOT
yet *role-ready* — a Senior Frontend, SRE, PM, or QA picking one up cannot
extract their role's actionable specification without re-deriving it from
prose `protective_statement` and `enforcement_statement` blocks.

This gap is invisible while the framework is operated by Matt + Co-Architect
(roles compressed into two operators). It becomes load-bearing the moment any
of the following ship:

- A real SCRUM team picks up an invariant as a sprint commitment.
- A new product onboards under the framework (per the L5 Per-Product
  Onboarding Epic) and needs to know what every role owes.
- The L5 Framework-Readiness Telemetry Epic measures whether the framework
  applies to all the roles it claims to govern.

Today's schema (post-2026-05-17 rich-form pattern) gives:

| Field | Serves |
|---|---|
| `protective_statement` | PM rationale (partial) |
| `enforcement_statement` | DevOps + Playwright (well) |
| `references` | Playwright file paths, ADR pointers |
| `applies_to` (v1) / per-surface (v2) | DevOps scope |
| `activation_note` | DevOps gate criteria |

What it does NOT give, per the audit:

- **SRE:** runtime observability, SLO, on-call, runbook.
- **Frontend:** component constraints, design-system dependencies, browser
  matrix, governed surfaces by route.
- **PM:** structured acceptance criteria, user impact, sprint decomposition.
- **Postman / Newman:** collections, endpoints covered, environment variables.
- **Playwright:** viewport matrix, fixture story (partial — paths are named).

A SCRUM team cannot execute on testimony. They execute on artifacts. This ADR
specifies the artifact shape.

---

## Decision

**Every rich-form invariant declares up to six optional `role:` sections.
Each section is validated if present; absence is allowed and explicit.**

### The six role sections

1. **`pm:`** — Product Manager
2. **`devops:`** — DevOps Engineer
3. **`sre:`** — Site Reliability Engineer
4. **`frontend:`** — Senior Frontend Engineer
5. **`playwright:`** — UI/E2E test automation
6. **`postman:`** — API contract test automation (Newman)

### Per-section canonical shape

```yaml
pm:
  acceptance_criteria:       # list[str] — observable signals for "done"
    - "<criterion>"
  user_impact: "<string>"    # one-line — who feels the breakage, how
  sprint_decomposition: "<string>"  # rough effort + sequencing

devops:
  ci_gates:                  # list[str] — workflow + job paths
    - "<workflow.yml:job>"
  secrets:                   # list[str] — token / key names (no values)
    - "<NAME>"
  deploy_gates:              # list[str] — what blocks if this fails
    - "<env>"
  rollback: "<string>"       # one-line — what to revert if violated post-deploy

sre:
  observability:             # list[str] — emit/scrape signals
    - "<metric or log marker>"
  slo: "<string or null>"    # SLI/SLO; null if pre-deploy gate
  runbook: "<path>"          # docs/runbooks/<name>.md
  on_call_action: "<string>" # what on-call does when this fires; "none" allowed

frontend:
  governed_surfaces:         # list[str] OR string (path to surface manifest)
    - "<route>"
  component_constraints:     # list[str] — what UI primitives must satisfy
    - "<rule>"
  design_system_dependencies: # list[str] — which DS components this binds
    - "<product>:<component>"
  browser_matrix: "<string>"  # viewport floor + special cases

playwright:
  spec_files:                # list[obj] — each file + what it asserts
    - path: "<path>"
      asserts: "<short description>"
  fixtures: "<string>"       # seed/fixture story
  viewport_matrix: "<string>" # device floor; "n/a" if API-only

postman:
  collections:               # list[str] — collection + section
    - "<collection.json#section>"
  endpoints:                 # list[str] — endpoints covered
    - "<METHOD /path>"
  env_vars:                  # list[str] — Newman env vars required
    - "<NAME>"
  adversarial_cases:         # list[str] — explicit attack patterns covered
    - "<case>"
```

### Required vs optional

**All six sections are optional.** When a section does not apply, declare it
explicitly with a machine-readable reason:

```yaml
frontend:
  applicable: false
  reason: "registry-side invariant, no UI surface"
postman:
  applicable: false
  reason: "UI invariant, not API"
sre:
  applicable: false
  reason: "pre-deploy gate, no runtime presence"
```

The not-applicable form is a two-key map (`applicable: false` + `reason:`), NOT
a YAML scalar `null`. This is deliberate: a scalar `null` cannot carry a
`reason:` field, so "deliberately not applicable + why" is only expressible as a
map. (An earlier draft of this ADR showed both `section: null  # reason: ...`
*and* "requires a `reason:` field when null" — a contradiction, since a scalar
null has no fields. The map form resolves it.)

Explicit `applicable: false` with a reason is preferred over omission.
Conformance validates the populated shape when `applicable:` is absent or true,
requires a `reason:` when `applicable: false`, and allows omission entirely.
Omitted = "not yet authored"; `applicable: false` with a reason = "deliberately
not applicable."

### Examples — applied to current invariants

**#1 anonymous_id** would populate:
- `pm` (acceptance criteria around zero-PII surfaces)
- `devops` (the two-DB static gate + PII column gate workflows)
- `sre` (the ose_anon cookie audit trail; FORMS_DB access patterns)
- `frontend` (anonymity affordance on every public page — brand-voice §4.1)
- `playwright` (the existing structural specs)
- `postman: {applicable: false}` (correlation gate is server-side, not endpoint-shape)

**#14 mobile_workability** would populate:
- `pm` (the five-contract acceptance criteria per surface)
- `devops` (audit workflow path + CI gate)
- `sre: {applicable: false}` (pre-deploy gate, no runtime SLO)
- `frontend` (component-level requirements: Button v2 tap target floor, input
  font-size, etc.)
- `playwright` (the per-product audit spec at canonical path + viewport matrix)
- `postman: {applicable: false}` (UI invariant)

**#10 deprecation_lock** would populate:
- `pm` (acceptance criteria around the four enforcement layers)
- `devops` (the guard scripts + self-tests + CI step ordering)
- `sre: {applicable: false}` (pre-deploy gate)
- `frontend: {applicable: false}` (code-level gate, no UI surface)
- `playwright` (the structural invariant spec)
- `postman: {applicable: false}` (code-level gate, no API surface)

The pattern: each invariant honestly declares which roles it touches. A
single-role invariant declares one section; a cross-cutting one (like #1)
declares five.

---

## Consequences

### Positive

- **The SCRUM team can execute without an interpreter.** Senior Frontend reads
  `frontend:` and knows what to build; SRE reads `sre:` and knows what to
  observe; PM reads `pm:` and knows what to accept.
- **L5 Framework-Readiness Telemetry gets six new KPIs.** "% invariants with
  each role section populated" — six bars on the dashboard, one per role.
  Forces the answer to *"is this framework load-bearing for each role?"*
- **New-product onboarding has a checklist.** A product joining the framework
  walks through every invariant's role sections and declares which surfaces /
  components / endpoints satisfy them. No tribal knowledge.
- **The lean → rich enrichment work has a target.** OCR-71's "rich form"
  becomes "role-ready rich form" — the same pass that adds
  protective_statement adds role sections.

### Negative / trade-offs

- **Schema bloat.** Six new top-level sections per invariant; a fully-populated
  rich-form entry doubles in length. Mitigation: all sections optional; null
  with reason is a first-class citizen; YAML anchors permit shared fragments
  (e.g., a single `devops:` block referenced by multiple related invariants).
- **Drift between sections.** `enforcement_statement` and `devops:` can say
  different things. Mitigation: the conformance check (L1 — OCR-53 hardening)
  validates cross-section coherence (e.g., every workflow path in `devops:`
  matches a path in `references:`). Single source of truth, multiple views.
- **The "right" role taxonomy will change.** Today: PM / DevOps / SRE /
  Frontend / Playwright / Postman. Tomorrow: maybe DesignOps, ML Engineer, ...
  Mitigation: the role list is itself versioned in the schema; ADR amendments
  add roles, never rename them.

### Neutral / explicit

- This ADR does NOT specify *which* invariants get which sections — that's the
  per-invariant authoring decision, tracked in OCR-71.
- This ADR does NOT bind the role definitions to a specific org chart. A "PM"
  may be a founder filling that role; an "SRE" may be a future hire; the
  schema is role-as-function, not role-as-headcount.
- This ADR's role list is the v1 canonical set. Future ADRs may extend.

---

## Implementation

**Bundled with ADR-002 Phase 1** — schema v2.0.0 absorbs the role sections in
the same migration that adds `scope` / `profile` / `contract`. One bump, not
two. The Linear sub-Story is filed under OCR-49 alongside OCR-54 /
OCR-55 / OCR-56 / OCR-57.

### Sequence within Phase 1

1. Author the role-section schema in the YAML header comments + level2_schema.py.
2. Backfill all six existing rich-form invariants (#1, #3, #5, #8, #10, #14)
   with role sections (the backfill is the proof point — if it can't be done,
   the schema is wrong).
3. Update the lean → rich enrichment cadence (OCR-71) to author role sections
   from day one — no lean→rich without role-section pass.
4. Add the six KPIs to L5 telemetry; emit on every conformance run.

### Validation

- `level2_schema.py` validates each role section's shape when it is populated
  (i.e., `applicable:` is absent or true).
- `level2_schema.py` requires a `reason:` field when a section declares
  `applicable: false`, and rejects scalar `null` (it cannot carry a reason).
- `level2_schema.py` enforces a closed key set per section. The `devops:` keys
  are exactly `ci_gates`, `secrets`, `deploy_gates`, `rollback` — there is no
  `workflow_paths` key. A test-spec path belongs under `playwright.spec_files`,
  not `devops:`. (The #14 proof point's stray `devops.workflow_paths` is a
  reconcile item for the OCR-71 backfill, not a schema addition.)
- `check_brain_contract.py` (per OCR-53 hardening) validates cross-section
  coherence: workflow paths in `devops:` must resolve; spec paths in
  `playwright:` must exist on disk; etc.
- L5 telemetry emits per-role completion percentages on every main-branch run.

### Doctrine link

This ADR specifies *what* role-readiness means; ADR-003 specifies *how* the
framework absorbs the work (L0 schema → L1 conformance → L5 telemetry). Read
together they form the contract that lets the framework scale to a real
SCRUM team without losing its self-checking property.

---

## Open questions

- **Cross-section coherence rules.** What's the minimum coherence the
  conformance check enforces? V1 candidate: every path in `devops.ci_gates`
  resolves on disk; every path in `playwright.spec_files` resolves on disk.
  Stronger coherence (e.g., the spec actually asserts what `frontend:`
  declares) is harder to mechanize — tracked separately.
- **Per-product instances of the same invariant.** Some role sections will
  differ across products (e.g., `frontend.design_system_dependencies` is
  "ose: ouroboros-ds" for OSE but TBD for WKRP). Schema: keep the section
  per-invariant; allow per-product overrides via a future `per_product:` key
  if pressure demands. Defer until pressure is real.
- **Authoring tooling.** Should `/adr` and `/story` skills understand the
  role sections? E.g., `/story` auto-routes to the right team based on which
  role section the work touches. Defer to L5 Continuous-Improvement cadence
  to surface when authoring pain is acute.

---

## References

- ADR-002 — Identity-Profile-Keyed Invariants. Phase 1 of ADR-002's
  implementation is the bundle target for this ADR's schema changes.
- ADR-003 — Self-Checking Infrastructure. The operational doctrine this ADR
  fleshes out for execution.
- `ocr-docs-brain/architectural-invariants.yaml` — the registry that absorbs
  the schema extension.
- `ocr-docs-brain/tests/level2_schema.py` — the validator that enforces
  shape on the new sections.
- Linear OCR-49 (Phase 1 schema migration) — implementation home for the
  schema sub-Story.
- Linear OCR-71 (lean → rich enrichment) — scope expansion target.
- Linear *L5 — Framework-Readiness Telemetry* Project — KPI consumer.

---

## Revisit Criteria

- If a sixth-plus role emerges that recurs across multiple invariants (e.g.,
  DesignOps, ML Engineer, Security Engineer as a distinct role), add it via
  ADR amendment — never silently extend.
- If cross-section drift becomes a recurring CI failure pattern, harden the
  coherence rules and re-issue this ADR.
- If the SCRUM team operating against the framework reports the role
  sections are insufficient for execution, this ADR is the revisit point.
- Quarterly review (L5 Continuous-Improvement Epic) reads the six per-role
  completion KPIs and decides whether the role definitions are pulling
  their weight.

---

## Changelog

### 2026-06-05 — pre-acceptance amendment (CCR of #14 proof point)

Source: CCR review of the `mobile_workability` (#14) role-section backfill —
ADR-004's first and only worked example — performed before acceptance.

- **C2 (material) — null convention was self-contradictory.** The "Required vs
  optional" section showed the not-applicable form as `section: null  # reason:
  ...` while the Validation section required "a `reason:` field when explicitly
  null." A YAML scalar `null` has no fields, so the two statements could not
  both be satisfied. The #14 author had silently resolved this by using
  `{applicable: false, reason: ...}` — the only form that attaches a
  machine-readable reason. **Resolution:** canonicalized the two-key map
  (`applicable: false` + `reason:`) as the not-applicable form; scalar `null` is
  now rejected. The example was correct; the prose was wrong.
- **C1 (minor) — `devops.workflow_paths` is not a schema key.** The #14 example
  introduced a `devops.workflow_paths` key holding a Playwright spec path. The
  `devops:` schema is a closed set (`ci_gates`, `secrets`, `deploy_gates`,
  `rollback`); a spec path belongs under `playwright.spec_files`. Recorded as a
  reconcile item for the OCR-71 backfill, not a schema addition.

Status remains **Proposed**. This amendment clears the blocker CCR found; the
ADR is now internally consistent and ready for the acceptance review.
