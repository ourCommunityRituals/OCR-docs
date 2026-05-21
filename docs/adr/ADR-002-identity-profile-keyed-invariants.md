# ADR-002: Key architectural invariants to identity profile, not product-ID lists

**Status:** Proposed
**Date:** 2026-05-21
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

## Context

The governance brain (`OCR-docs/ocr-docs-brain/architectural-invariants.yaml`)
binds each architectural invariant to the products it governs through a
hand-maintained `applies_to` list of product IDs. Invariant #1 `anonymous_id`
carries `applies_to: [ose, osm]`; #10 `deprecation_lock` carries
`applies_to: [ose, osm, wkrp, oaw]`; and so on. `check_brain_contract.py`
reads that list to decide whether a given invariant gates a given product's CI.

This model was sufficient while every product in the fleet shared one identity
model. It no longer is. The fleet now spans two genuinely different end-user
identity models, and the brain has no vocabulary for the difference:

- **Anonymous-identity products** — OSE (`ourSharedEvents`), OSM
  (`ourSharedMagnets`). The brand promise is "you're part of the group,
  anonymously." Zero-PII, two-database separation, no correlation back to a
  person. Invariant #1 `anonymous_id` is the architectural commitment.
- **Non-anonymous-identity products** — WKRP (`ourWKRP`), OAW
  (`ourAirwaves`). The brand promise is the opposite by design: a contributor
  *deliberately* plants a flag — "I want my name on this" — authenticates,
  and their identity is on the record. WKRP stores a contributor name, a
  generational lineage tag, and a Spotify identity. That is not drift from
  the anonymous invariant; it *is the product*.

The trigger for this ADR is the WKRP brain-conformance work
(branch `claude/wkrp-conformance-phase-gate`, ourWKRP PR #26). Bringing WKRP
under the brain surfaced three structural failures in the `applies_to` model:

1. **The opt-out hole.** WKRP is correctly absent from `anonymous_id`'s
   `applies_to` list — the zero-PII rule genuinely does not apply to it. But
   the brain has *no* positive identity invariant for non-anonymous products.
   The way a non-anonymous product "passes" identity governance today is by
   being *absent from a list*. Absence-by-design and absence-by-omission are
   indistinguishable. A product that should be governed but was forgotten
   looks byte-identical to a product that is correctly exempt. For the
   single most load-bearing concern in the fleet — how a product handles a
   human being's identity — silent omission is the most dangerous failure
   mode, and the current schema makes it the *default* one.

2. **One invariant cannot carry two correct answers.** The invariant *is* the
   anonymous rule. There is no way to express "identity must be handled
   correctly" as a single concern whose *correct implementation differs* by
   product. Non-anonymous products do not need a relaxed `anonymous_id`; they
   need a *different* identity contract — explicit opt-in, a consent record,
   bounded PII retention, and brand copy that does not falsely claim
   anonymity. The brain can currently say only "anonymous_id applies / does
   not apply." It cannot say "the non-anonymous form of identity-correctness
   applies to you, and here is what that form requires."

3. **`applies_to` restates the registry, by hand, and drifts.**
   `product-registry.yaml` already declares `identity_layer` per product
   (`anonymous`, `non-anonymous`, `pre-tech`, `n/a`). The invariant file
   re-encodes that same fact, by hand, scattered across a dozen `applies_to`
   lists. Every new product and every identity reclassification requires a
   human to remember to touch N lists. The two files can — and eventually
   will — silently disagree. Single source of truth is violated.

The forces are: the fleet is multi-identity-model and will stay that way
(`OCR_VISION.md` and the privacy-boundary doctrine make anonymous OSE and
non-anonymous WKRP both permanent); the brain must *gain* signal as products
diverge, not lose it; and identity classification must live in exactly one
place.

## Decision

**Architectural invariants are keyed to identity profile, resolved from the
product registry — not to hand-maintained product-ID lists.**

Introduce a two-level model and a registry-driven resolver.

### 1. Invariant vs. contract

Separate the **invariant** (the named architectural concern — stable, numbered,
never deleted) from the **contract** (the concrete, testable rule — a
`test_file` + `enforces` statement). An invariant owns one or more contracts.

### 2. Every invariant declares a `scope`

| `scope`         | Meaning |
|-----------------|---------|
| `universal`     | One contract. Applies to every product that has code, regardless of identity profile. |
| `identity-keyed`| A *map* of contracts — one entry per identity profile. A product resolves the contract matching its `identity_layer`. |

### 3. Contracts are keyed to identity profile

The canonical profiles are exactly the `identity_layer` values already in
`product-registry.yaml`:

| Profile         | Products today        | Identity model |
|-----------------|-----------------------|----------------|
| `anonymous`     | OSE, OSM              | Zero-PII; no correlation back to a person. |
| `non-anonymous` | WKRP, OAW             | Identity on the record by deliberate user choice. |
| `pre-tech`      | OSP, OSR, OSG, OOT    | No application code yet; identity model not realized. |
| `n/a`           | OCR-docs, ocr-platform-tests | Governance / CI repos; no end-user identity surface. |

An `identity-keyed` invariant **must enumerate every profile** — including the
ones it does not govern — with an explicit contract *or* an explicit
`not-applicable` plus a one-line `reason`. Example shape:

```yaml
- id: 1
  name: identity_handling
  title: Identity Handling
  scope: identity-keyed
  contracts:
    anonymous:
      test_file: anonymous-id.invariant.spec.ts
      enforces: Zero-PII scan system. Two-database separation (DB / FORMS_DB).
        ose_anon cookie contract. No cross-linking.
    non-anonymous:
      test_file: non-anonymous-identity.invariant.spec.ts
      enforces: Explicit opt-in ("plant a flag") gate before identity capture.
        Consent record persisted. Bounded PII retention. No brand copy that
        claims anonymity.
    pre-tech:
      status: not-applicable
      reason: No application code; identity model not yet chosen. Resolves to
        a real contract automatically when identity_layer is set.
    n/a:
      status: not-applicable
      reason: Governance/CI repo; no end-user identity surface.
```

### 4. Membership is resolved, never declared

The `applies_to` product-ID list is **removed**. `check_brain_contract.py`
resolves membership on every run:

1. Read the product's `identity_layer` from `product-registry.yaml`.
2. For each invariant:
   - `universal` → the single contract applies (subject to the existing
     lifecycle gates — `code_present`, `pipeline_present` — unchanged).
   - `identity-keyed` → look up `contracts[identity_layer]`. A
     `not-applicable` entry PASSes with its recorded reason. A real contract
     is enforced against the product's `test_file`.
3. There is no list to consult. Membership is *derived*, every run, from the
   registry. The two files cannot drift because one no longer restates the
   other.

### 5. `not-applicable` must be explicit — this is the load-bearing rule

The conformance check **fails** if an `identity-keyed` invariant omits any
profile. Absence ceases to be a valid state. Exemption now requires a
positive, reviewed declaration with a reason. This single rule closes the
opt-out hole: a forgotten product can no longer masquerade as an exempt one,
because exemption is now a thing someone had to *write down*.

### 6. Identity profile is orthogonal to lifecycle phase

This decision does **not** touch the lifecycle-phase gates. `pipeline_present`,
`code_present`, and `pipeline_activation_phase` answer *"is the mechanism
built yet?"* — and keep doing exactly that. Identity profile answers *"which
rule is the correct one once it is built?"* The two axes are independent: a
`pre-tech` product resolves to the `pre-tech` contract slot (`not-applicable`)
until it picks an identity model, at which point the registry's
`identity_layer` flips and the product automatically resolves to a real
contract with no edit to the invariant file.

## Alternatives Considered

### Alternative A: Keep `applies_to` lists; add WKRP/OAW to a new non-anonymous invariant

Leave the schema alone. Write a second invariant — `non_anonymous_identity` —
with `applies_to: [wkrp, oaw]`.

**Rejected because:** it patches today's two products without fixing the
mechanism. The *next* non-anonymous product still depends on a human
remembering to edit a list; absence still equals exemption; the registry is
still restated by hand and still drifts. It treats the symptom (WKRP is
ungoverned) and leaves the disease (omission is silent, and the schema cannot
tell exempt-by-design from forgotten). It also leaves `anonymous_id` and
`non_anonymous_identity` as two unrelated invariants when they are two
contracts of one concern — "identity is handled correctly" — which is exactly
the comparability a fleet brain exists to provide.

### Alternative B: Per-product invariant files

Give each product its own invariant set under
`ocr-docs-brain/products/<name>/invariants.yaml`.

**Rejected because:** it explodes the brain into N copies and destroys the
cross-product comparability that makes a fleet brain valuable. Universal
concerns (`deprecation_lock`, `tenant_isolation`, the runner invariants) would
be copy-pasted N times and *guaranteed* to drift apart. The whole point of a
single brain is one source of truth for shared contracts; per-product files
are the opposite of that.

### Alternative C: Boolean governed/not-governed matrix per invariant per product

Replace `applies_to` with an explicit `{product: true|false}` map so every
cell is stated and none can be silently omitted.

**Rejected because:** a boolean closes the opt-out hole (Failure 1) but not
Failure 2. It can say "governed / not governed" — it cannot say *which rule*.
It cannot express that WKRP needs a different, differently-strict identity
contract rather than an exemption from the anonymous one. Non-anonymous
products would still get *no* identity contract, just now-explicitly-no
instead of silently-no. It records the gap without closing it.

### Alternative D: Auto-derive `applies_to` from `identity_layer`, keep one rule per invariant

Keep one contract per invariant, but compute the product list from the
registry instead of hand-maintaining it.

**Rejected because:** it closes Failure 3 (drift) only. One invariant still
cannot carry two correct answers (Failure 2), so the identity invariant stays
anonymous-only and non-anonymous products still resolve to *no* identity
contract — now automatically. Automating the derivation of an incomplete
model just produces the incomplete result faster.

## Consequences

### Positive

- **The opt-out hole is closed.** Every product, on every conformance run,
  resolves to an *explicit* identity contract — a real rule or a reviewed
  `not-applicable` with a reason. A forgotten product fails CI; it cannot pass
  by omission. Exempt-by-design and forgotten are now distinguishable.
- **Non-anonymous products gain real identity governance for the first
  time.** WKRP's "plant a flag" opt-in gate, its consent record, and its
  bounded PII retention become brain-enforced contracts with test files —
  not untested intentions. OAW inherits the same contract the day its code
  lands, with no invariant-file edit.
- **`product-registry.yaml` is the single source of truth for identity
  classification.** The invariant file consumes `identity_layer` and never
  restates it. The two files cannot disagree.
- **Adding or reclassifying a product is a one-field edit.** Change
  `identity_layer` in the registry; every invariant re-resolves automatically
  on the next run.
- **Identity profile and lifecycle phase are cleanly separated.** The
  `pipeline_present` / `code_present` escape hatches keep doing their job; the
  identity axis does its own. Neither contaminates the other.

### Negative

- **One-time schema migration.** `architectural-invariants.yaml`,
  `level2_schema.py`, `check_brain_contract.py`, and the PACT-level test
  (`level8_pact.py`) all change. The migration must respect the existing
  `enrichment_history` discipline — never renumber, never delete an invariant,
  append a history entry for the shape change.
- **More verbose YAML.** Every `identity-keyed` invariant must now enumerate
  all four profiles, including `not-applicable` slots. This verbosity is the
  feature — it is precisely what makes omission impossible — but it is more
  lines to read.
- **The non-anonymous identity contract is net-new work.** Writing the
  `non-anonymous` contract and its `non-anonymous-identity.invariant.spec.ts`
  for WKRP/OAW is real engineering, not a rename. The brain will be honestly
  `planned`/`partial` on that contract until the test file lands and gates
  WKRP CI.

### Neutral

- Of the 12 current invariants, most become `universal` (deprecation_lock,
  tenant_isolation, the runner invariants, geo-resolution, etc.). Only the
  identity-sensitive few become `identity-keyed` — clearly `anonymous_id`,
  and candidates `aggregate_only_reporting` and `bounded_pii_retention`
  (anonymous and non-anonymous products bound PII for different reasons and
  to different rules).
- Invariant numbers are preserved. The change is to the *shape* of each
  entry, tracked in `enrichment_history` exactly as the past lean→rich
  transitions were.

## Implementation Notes

Suggested phased migration (each phase a focused PR):

- **Phase 1 — brain schema.** Bump `architectural-invariants.yaml` to
  `schema_version: 2.0.0`. Add `scope` and the `contracts` map. Teach
  `level2_schema.py` the new shape and add a check that every `identity-keyed`
  invariant enumerates all four profiles. Append an `enrichment_history`
  entry for the schema transition.
- **Phase 2 — resolver.** Rewrite the `applies_to` lookup in
  `check_brain_contract.py` as a registry-driven resolver keyed on
  `identity_layer`. Remove `applies_to` from the YAML.
- **Phase 3 — contracts.** Author the `non-anonymous` identity contract and
  its `non-anonymous-identity.invariant.spec.ts` in WKRP (and OAW when its
  code lands). Note: `deprecation_lock` is `universal`, so WKRP resolves to
  it directly — the outstanding WKRP `deprecation-lock.invariant.spec.ts`
  conformance item is satisfied by the universal contract with no list edit.
- **Phase 4 — PACT.** Update `level8_pact.py` so invariant↔product assertions
  resolve through the new model rather than through `applies_to`.

- **Affected repos:** OCR-docs (brain + scripts + tests), ourWKRP, ourAirwaves;
  OSE/OSM unaffected at the contract level (their `anonymous` contract is the
  current `anonymous_id` rule, unchanged).
- **Brain invariant:** `OCR-docs/ocr-docs-brain/architectural-invariants.yaml`
  invariant #1 and the schema as a whole.
- **Registry:** `OCR-docs/ocr-docs-brain/product-registry.yaml` —
  `identity_layer` becomes the resolution key (no schema change to the
  registry itself).
- **Related:** the `pipeline_present: false` WKRP escape hatch
  (ourWKRP PR #26 / branch `claude/wkrp-conformance-phase-gate`) is the
  lifecycle-phase axis and is *retained* unchanged by this decision.

## References

- Trigger: WKRP brain-conformance work — ourWKRP PR #26, OCR-docs branch
  `claude/wkrp-conformance-phase-gate`.
- Builds on: ADR-001 (docs-as-code scaffold) — the `identity_layer` field and
  the anon / non-anon / both taxonomy referenced in ADR-001's Revisit Criteria.
- Brain contracts codifying enforcement: `architectural-invariants.yaml`,
  `ocr-docs-brain/scripts/check_brain_contract.py`,
  `ocr-docs-brain/tests/level2_schema.py`,
  `ocr-docs-brain/tests/level8_pact.py`.
- Doctrine memory: `project_privacy_boundary.md` (WKRP non-anonymous opted-in;
  OSE anonymous; the individual chooses the tracking level) — the product
  doctrine this ADR makes the brain able to enforce.
- Standard: `OCR-docs/docs/standards/OCR_STANDARD_brainEnforcementLocation.md`.

## Revisit Criteria

- If a fourth end-user identity profile is introduced beyond `anonymous` /
  `non-anonymous`, the `contracts` map simply gains a key — by design, no
  schema change. Revisit only to confirm the resolver and `level2_schema.py`
  enumerate the new profile.
- If a single product ever needs *two* identity profiles simultaneously (a
  genuinely dual-mode application), the single-`identity_layer` resolution key
  breaks and the resolver must accept a list — that is a material schema
  change and warrants a superseding ADR.
- If the fleet ever collapses back to a single identity model across every
  product, the two-level invariant/contract model becomes overhead and could
  fold back to flat invariants.
