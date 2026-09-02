# PROPOSAL — SharedReport six-axis model, and privacy-by-construction as the enterprise unlock

> **Status:** Proposed — owner-authored model (2026-09-02), captured verbatim in substance by the OSE-1167 session; not yet in `OCR_VISION.md` or the brain, so per `OCR_STANDARD_knowledgeHomes.md` this is staged truth, flagged, not asserted.
> **Home once ratified:** `ocr-docs-brain/` (a `shared-report-composition.yaml` contract, §4) + an `OCR_VISION.md` positioning line (§2). Until then this file is the single home; everything else points here.
> **Consumes:** `ourCommunityRituals/docs/testing/OSE-1167-sharedreport-matrix-design.md` (the L1 matrix), which this proposal generalises and which derives its tests from §5.
> **Verified against:** `ourSharedEvents@81c98aa`, `OCR-docs@793c038`.

## 1. The model — six axes of a SharedReport

A SharedReport is not one gate. It is the intersection of six independent axes. Naming them separately is what lets each be tested at its own lowest honest layer.

| Axis | Question it answers | Decides |
| --- | --- | --- |
| **Depth** | how much of a node's report does this viewer see? | which sections are present (existing depth gating: local / mid / premium, by omission only) |
| **Scope** | whose data? | org / brand / sub-org isolation; a sponsor's own slice |
| **Composition** | how do nodes group into one report? | A+B including B's sub-groups; C independent; roll-up to parent |
| **Tier / flags** | what composition powers did you buy? | free / mid = per-node report; enterprise = configurable cross-node grouping |
| **Role** | who may configure the grouping vs who may view the result? | configure ≠ view |
| **Stateful config** | is the grouping itself an object? | yes: mutable, so "A+B, pull C in, move B's sub-group out, change my mind" inherits the same indecision invariants as the event wizard. Configuring a report is a deep flow. |

Depth and Scope exist in code today. Composition exists only in fixed, implicit forms. Tier-gating of composition, configure-vs-view roles, and stateful config do not exist. §3 has the evidence.

## 2. Privacy-by-construction is the enterprise feature, not the fine print

The owner's reframe, kept in full because it changes what the model is *for*:

1. **The consolidation is legal by construction.** Pooling footprint across sub-orgs (often separate legal entities: franchises, venues) into one report is normally a cross-entity data-sharing problem; combining attendee datasets across legal boundaries is where compliance says no. Because the model is never-who + aggregate-only + K-floored, the consolidation is compliant automatically. The legal blocker to the play is removed. That is the unlock, not a constraint.
2. **The report is freely shareable with sponsors.** Built on identifiable data, handing a footprint report to a sponsor is a data transfer: consent chains, a DPA per sponsor, liability. Aggregate-only means no PII leaves, so the enterprise can hand the report to any sponsor with no consent overhead and no processing agreement. The covenant makes the report a freely circulating BD instrument; remove the privacy and the business model gets legally expensive.
3. **It resolves internal governance friction.** Sub-orgs resist handing attendee lists up to HQ. Never-who means HQ gets the aggregate value without sub-orgs surrendering identities: they contribute footprint, not people. The privacy structure dissolves the org-chart politics that would otherwise kill the roll-up.
4. **Trust and regulatory tailwind.** With cookie deprecation and ad-tech backlash, "we prove your presence creates sponsor value without ever tracking who you are" is a forward position. The enterprise inherits that trust story with attendees and sponsors and bets with the regulatory wind instead of building surveillance it will have to rip out.

**GTM line:** "Consolidate your footprint into sponsor revenue — provably anonymous." The covenant scales platform value → enterprise compliance capability → sponsor confidence; every corner of the triangle benefits from the same guarantee.

> **⛔ Security hold on this language (CCR Loop 1, Dr. Security, 2026-09-02 — Regulatory Required, no partial credit).** Points 1–4 above are the product thesis, and the *single-node* half of it is true today (never-who, aggregate-only, per-bucket K≥5 are live and CI-enforced). The *consolidate* half is not yet earned: §3 C3/C4/C10 document an unproven composition/differencing surface, and "anonymous" in the GDPR recital 26 / CCPA aggregate-exemption sense is a **legal standard (motivated-intruder, reasonably-likely means) the code has not been evaluated against**, not an engineering property a K threshold confers. Therefore: the words **"provably anonymous", "legal by construction", "no consent overhead", "no processing agreement"** do not ship — not into `OCR_VISION.md`, a deck, a landing page, or a sponsor conversation — until (a) G3 (OSE-1189) lands as a passing CI gate covering the release-ledger rule in §4, and (b) counsel has reviewed the anonymisation-sufficiency claim. Until then the honest external line is: *"aggregate-only, never-who by construction, with a K-anonymity floor on every published number; consolidated reporting is in design."* Read §2 only together with §3 C3, C4, C9 and C10.

**Brain anchors this rests on (all live):** #1 `anonymous_id`, #7 `aggregate_only_reporting`, #8 `bounded_pii_retention`, #9 `tenant_isolation`, #5 `tier_equity` (collection is tier-blind), and the K floors in code (`CORRIDOR_MAP_MIN_COUNT = 5` applied per bucket before summation, `RETURN_RATE_MIN_SAMPLE = 3`, `CORRIDOR_BASELINE_MIN_SAMPLE = 10`). Point 2 additionally rests on the cross-product boundary: the WKRP service class fails closed on the batch endpoint (OSE-577, ADR-0001).

## 3. How this clashes or dovetails with existing code (verified)

### Dovetails

| Axis | What exists | Where |
| --- | --- | --- |
| Depth | exactly the model: `DEPTH_SECTIONS` local/mid/premium, omission only, sponsor capped at mid, fail-closed to local, `upgrade.locked_sections` printed on the wire | `workers/oursharedevents/src/lib/report-depth.ts` |
| Scope (sponsor slice) | `sponsor_id` claim filters `sponsor_impressions`; `campaign_summary` re-derived after scoping; no `sponsor_id` → zero rows, and mint refuses the token | `shared-report-read.ts`, OSE-595, Q6 |
| Scope (brand) | object-level brand scope on every admin event sub-route including mint-link; an operator's scope is a **list of brand ids** (`ADMIN_BRAND_MEMBERSHIP` → `brandIds[]`), and mode `deny` reaches nothing | `admin-object-scope.ts`, `admin-brand-scope.ts`, OSE-1080 |
| Composition (fixed) | **portfolio rollup**: brand-scoped aggregate over the brand's own events (per-node roll-up, K-floored); **event series**: auto-detected cross-event grouping feeding `headcount_trend` (`SERIES_CLUSTER_MIN_EVENTS = 3`); **batch**: N independent reports in one call, no server-side aggregation | `handlers/portfolio-rollup.ts` (OSE-669), `lib/shared-report.ts`, batch endpoint |
| Tier / flags | flag tiers `free / mid / enterprise` with per-tier feature presets; brain `tier-gates.yaml` already gates `shared_reports`, `cross_corridor`, `aggregate_intelligence` by tier, so read-side capability gating by pricing is sanctioned law | `lib/feature-flags.ts`, `handlers/feature-flags.ts`, `ocr-docs-brain/tier-gates.yaml` |
| Role | "organizer generates, sponsor receives": mint-link is admin-auth only; viewers are token bearers with role ∈ {bar_owner, sponsor, admin}; service classes `internal` / `cross_product` | `shared-report-auth.ts`, mint handler |
| Stateful deep flow (pattern) | the admin create-and-launch wizard is being built as the parameterised deep-flow surface (D1, OSE-1183) | `docs/plans/FE-DEV-PREP-2026-08-29.md` |

The strongest dovetail: **an operator's brand scope is already a set.** Composition's candidate universe is naturally "the brands the caller is scoped to", and a configured grouping is a chosen subset of that set. `isAdminObjectInScope` already answers "may this caller include node X" per node. **But brand scope is not enforced by every composition primitive that ships today** — see C9: `event_series` is a live counterexample, so "nothing new is needed" is withdrawn (CCR Loop 1).

### Clashes and gaps

| # | Clash / gap | Evidence | What the model has to say about it |
| --- | --- | --- | --- |
| C1 | **No org hierarchy in the schema.** `events.brand_id` is the only tenant key; no parent/sub-org relation exists in any migration. "B including B's sub-groups" has no representation. | `workers/oursharedevents/migrations/*` (no `parent_brand`, `org_id`, `sub_org`) | Composition must be modelled as an explicit membership object, not inferred from a hierarchy that is not there. The Linear doc "PROPOSED ADR Decision 8 — Multi-Flag Identity (account ↔ flag ↔ brand)" is the identity-side draft this must reconcile with. |
| C2 | **Three tier vocabularies, and the brain disagrees with code on the third name.** Report depth = local/mid/premium; flag tier in code = free/mid/**enterprise**; `tier-gates.yaml` calls the third tier **premium**; VISION says Free/Mid/Enterprise. | `report-depth.ts` header comment; `feature-flags.ts` `VALID_TIERS`; `tier-gates.yaml`; `OCR_VISION.md` invariant #5 row | Composition powers are a **flag-tier** gate (enterprise), never a report-**depth** gate. Do not invent a fourth vocabulary; do fix the brain/code name drift (a reconciliation item, not this proposal's decision). |
| C3 | **Differencing oracle.** A mutable grouping plus a K-floor applied per released aggregate is the textbook complementary-release attack: `report(A+B) − report(A)` reveals B even when B alone is sub-K, and "pull C in, read, pull C out, read" is a query-set-difference oracle. Today only single-slice K≥5 is proven; composition/metamorphic K-anonymity is explicitly **not** (CCR verdict, Story G3 OSE-1189). | `shared-report-builder.ts` per-bucket floor; `shared-report-kanon-floor.spec.ts`; CCR verdict in OSE-1167 | **This is the one hard clash.** Stateful config turns the covenant's most plausible break from theoretical into a product feature unless the contract forbids it. §4 makes the composition floor a contract rule: every released aggregate **and every complement of a released aggregate against any prior release** clears K. Story G3 stops being a nice-to-have and becomes the gate on shipping Composition. |
| C4 | **Batch is client-side composition with no floor on the composite.** Bar_owner/admin get N premium reports; a client can sum or difference them. Acceptable today because every node returned is the caller's own; it stops being acceptable the moment a group contains nodes the caller does not own (HQ ↔ sub-org). | batch handler returns `reports{}` per id, `Cache-Control: no-store` | Cross-owner composition must be **server-side**, floored, and the per-node reports of non-owned members must not be individually readable by the group viewer (or C3 bites through the batch path). |
| C5 | **Invariant #5 wording vs tier-gated capability.** VISION's #5 row says pricing governs "display priority within events only — never platform access". Tier-gating composition is a platform capability gate. | `OCR_VISION.md` line 89; `tier-gates.yaml` already gates read-side features by tier | Not a real conflict, but the wording needs the carve-out made explicit: **collection and per-node numbers are tier-blind; grouping power is not.** Same numbers, different grouping. The equity test remains "no tier touches ingest". |
| C6 | **No configure-vs-view split in the role model.** Today configure = the admin actor behind mint-link; view = whoever holds the token. There is no object that a non-admin could be allowed to configure. | mint handler; no config schema | Role axis needs a new object kind in `matchAdminObjectTarget` (`report-composition`) so OSE-1080's wall covers it on day one, and a viewer token that binds to a **composition id**, not an event id (the signed-link claim today is `{eventId, role, exp, depth?, sponsor_id?}`). |
| C7 | **"Indecision invariants" are not yet a named artefact.** The owner references the event wizard's indecision invariants; `docs/plans/FE-DEV-PREP-2026-08-29.md` and `docs/CHOICE-INVARIANTS.md` do not use that term (CHOICE-INVARIANTS is the identity choice, not change-of-mind). | grep across both repos | Name them before Composition's config CRUD is specified (idempotent re-save, remove/re-add returns to the identical state, moving a sub-group is atomic, an abandoned draft never affects a live grouping). Then the same list gates both wizards. |
| C9 | **A composition primitive already leaks across tenants.** `event_series` (migration 0033) has no `brand_id`; the detector clusters on venue string + weekday + hour with no brand predicate; the `headcount_trend` read selects every event in the series with no brand predicate. Two brands at one venue on one cadence become one series; once confirmed, a premium viewer on brand A's event receives brand B's per-instance headcounts (K-floored, so never-who holds; Invariant #9 `tenant_isolation` does not). | `shared-report.ts` series detector; `shared-report-builder.ts` instances query; `migrations/0033_create_event_series.sql` | Verified by the CCR lead in code. Predates this proposal; the fix is Security-owned and scheduled in the hub design doc (F10, P8, cell T1). It is also the proof that composition's floor must be enforced per primitive, never assumed from scope. |
| C10 | **Temporal / batch differencing is live today for a viewer's own nodes.** A bar_owner or admin can read the same event at T1 and T2, or N own events in one batch call (`no-store`, no release memory), and difference K-floored sums. The delta reveals a count increment in a bucket, never an identity, and the viewer owns every node involved, so never-who holds; but it is the same oracle class as C3 with no ledger behind it. | batch handler; `Cache-Control: no-store` | Loop 2 classifies whether this is acceptable-by-ownership or a floor gap; either way the §4 ledger applies to batch reads, not only to configured groups. |
| C8 | **Phase gate is UI-only — and not implemented in the UI either.** The API is phase-blind (never reads `events.status`); "full report only post_event" is a render rule per `event-phase-contract.yaml`, but `shared-report.html` has no phase or status branch (frontend lens, CCR Loop 1). The brain line describes intent, not code. | `handleGetSharedReport`; `shared-report.html`; the brain contract | A composite report of mixed-phase nodes needs the rule restated: a group report renders the post_event members, and the pre/live members contribute nulls with suppression reasons, exactly as a single pre-event node does today. |

## 4. What OCR-docs captures (brain candidates)

Staged for `ocr-docs-brain/shared-report-composition.yaml` (draft v0.1; CI drift check arms when a second consumer ships). Field sketch, law-leads-implementation-conforms:

```yaml
schema_version: 0.1.0
status: draft
axes: [depth, scope, composition, tier_flags, role, stateful_config]
composition:
  node: 'an event, or a brand (all its events)'
  group: 'an explicit, stored set of nodes; may contain groups'
  membership_universe: 'the caller''s server-derived brand scope; nothing outside it is ever a candidate'
  release_floor:
    per_node: 'every aggregate clears K (today K=5 per bucket, before summation)'
    per_group: 'every group aggregate clears K'
    per_complement: 'for any two released aggregates R1 ⊂ R2 the difference R2 − R1 clears K, else R1 is withheld with a suppression reason'
    per_release_ledger: 'a persistent ledger per (viewer, composition universe) records every released aggregate; a new release is refused, with a suppression reason, if any linear combination of it with any subset of prior releases would isolate a sub-K node (A+B, B+C, A+C jointly solve for B even when every pairwise complement clears K; the Stateful-config axis manufactures exactly this multi-query surface)'
    applies_to_batch_reads: 'the ledger also covers repeated single/batch reads of own nodes over time (C10), not only configured groups'
    metamorphic_property: 'adding or removing one node, or re-reading over time, never lets a sub-K slice be derived by differencing or linear combination'
  cross_owner: 'server-side only; individual non-owned member reports are not readable by the group viewer'
tier_flags:
  free: per-node report only
  mid: per-node report only
  enterprise: configurable cross-node grouping   # flag tier; depth vocabulary unchanged
role:
  configure: 'scoped admin actor with object-level scope over every member node'
  view: 'signed-link bearer bound to a composition id'
stateful_config:
  invariants_ref: 'the event-wizard indecision invariants (to be named — C7)'
phase: 'API phase-blind; mixed-phase groups render post_event members, others contribute nulls'
```

Plus one line for `OCR_VISION.md` positioning (§2's GTM line) and the #5 wording carve-out (C5).

## 5. Then testing 1167 — derivation table

Each axis maps to a layer and to concrete artefacts in the OSE-1167 programme. The L1 cells for Depth, Scope and Phase are specified in the hub design doc; the rest are the additions this model creates.

| Axis | L0 (unit / static, every PR) | L1 (API matrix, every PR post-deploy) | L2 / L3 (UI) | Ticket |
| --- | --- | --- | --- | --- |
| Depth | `resolveDepth` / `filterReportByDepth` tests (exist); **derivation snapshot** of `DEPTH_SECTIONS` (new) | viewer × phase cells, section present/absent, `upgrade` | LOCAL viewer's DOM never contains stripped sections | C2 OSE-1181, E1 OSE-1184 |
| Scope | object-scope structural invariant (exists); sponsor-slice unit tests (exist) | sponsor cells on every phase; mint-link S1/S2 as a **scoped operator** (never `ADMIN_SCOPE_ALL`) | — | C2, OSE-1080 |
| Composition | **K-anon composition / metamorphic property tests** (fast-check): differencing never yields sub-K; complement rule holds (new, blocking before any composition code) | portfolio-rollup cells (exist as a route, uncovered); group-report cells once the object exists: own-only group 200, group with a non-owned node 403, sub-K complement withheld with reason | render of a group report shows suppression, never a blank | G3 OSE-1189 (promoted to gate), new Feature H |
| Tier / flags | flag-tier preset tests (exist) | free/mid attempting group config → 403 with a printed refusal code; enterprise → 201 | wizard hides nothing it cannot do; prints the refusal | new Feature H |
| Role | new object kind in `matchAdminObjectTarget` covered by the structural invariant | configure as viewer-role → 403; view with a composition-bound token → 200 | — | new Feature H |
| Stateful config | indecision invariants as property tests over the config state machine (idempotent save, remove/re-add identity, atomic move) | config CRUD mutation matrix: create, add, remove, move-subgroup, abandon-draft | **L3 deep flow**: the report-composition wizard, same harness as the event wizard | D1 OSE-1183 pattern, new Feature H |
| Phase | phase resolver tests (exist, brain contract) | cache policy per phase; mixed-phase group nulls | post_event render gate | E1 |

Reconciliation loop this closes (OSE-1166 flagpole): brain (this proposal → contract) → code (OSE) → CI (named L1/L2/L3 checks under OSE-1167) → results → owner. The matrix design doc is the CI leg; this file is the brain leg.

## 6. Owner questions

- **P-Q1** — Ratify the six axes as the canonical SharedReport model (brain contract in §4)?
- **P-Q2** — Composition floor: adopt the per-complement rule as law before any composition code, with G3 (OSE-1189) promoted from "forefront addition" to a **gate**?
- **P-Q3** — Composition is a flag-tier (`enterprise`) power, never a depth; and fix the brain's `premium` vs code's `enterprise` name drift as a separate reconciliation item?
- **P-Q4** — Name the event-wizard indecision invariants now (C7) so both wizards share them?
- **P-Q5** — *Team-decided (CCR Loop 1, product lens), recorded for veto:* **Feature H — Report Composition opens as a sibling epic, not a child of OSE-1167**, blocked by A (honest green) and by G3 as a passing gate. Keeps the CI redesign's reviewer attention on the honest-green push.
- **P-Q6** — Ratify the Security hold in §2: the four quoted phrases stay off every external surface until G3 passes and counsel has reviewed anonymisation sufficiency?
- **P-Q7** — Is C10 (own-node temporal differencing on batch reads) acceptable by ownership, or does the §4 ledger apply to batch before Composition ships?
