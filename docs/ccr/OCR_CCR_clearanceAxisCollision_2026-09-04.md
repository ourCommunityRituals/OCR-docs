# CCR — `legal_clearance_tier` axis collision

**Date:** 2026-09-04 · **Protocol:** CCR v3.0, 3 loops, extended scrum team (5 role lenses)
**Target:** the WHERE×WHAT governance lattice in ourSharedEvents, and the proposed fix
**Verdict:** **HELD** — unanimous across all five lenses

---

## 0. Finding under review

`legal_clearance_tier` carries the same name with incompatible types across the two axes of
the governance model:

| Migration | Table | Type | Domain | Axis |
|---|---|---|---|---|
| 0011 | `node_hierarchy` | TEXT | OPEN / RESTRICTED / REGULATED | **WHERE** (place) |
| 0023 | `event_type_registry` | INTEGER | 1–5 | **WHAT** (type) |
| 0023 | `events` | INTEGER | default 1 | **WHAT** |

WHAT is wired (`lib/template-clearance.ts`, `MAX()` in 0057 marked `LOAD_BEARING`). WHERE has
**zero reads and zero writes** in `src/`. 0011 defaults to `'OPEN'`, so the unread axis is
invisible wherever the honest answer is OPEN — hence the empirical signature: a congressional
event at an OPEN node works (right answer, wrong reason); a rec centre that should be
RESTRICTED is the first disagreement and silently gets the OPEN answer.

**Proposed fix under review:** rename to `regulatory_regime`; leave WHAT alone; add
`regime_constraints(regime, excluded_business_type, requires_disclosure, min_clearance_tier)`;
combine by UNION of exclusions and MAX of min tiers; mirror `category_selections`' JSON shape.

---

## 1. Corrections to the recon that produced this finding

Recorded first, because two lenses caught them independently and they change the design input.

1. **`category_selections` is NOT unread.** It is validated against `category_registry` at
   write time, fails closed on malformed/off-registry input
   (`handlers/sponsors-draft.ts:validateCategorySelections`), and is **re-validated at
   promotion** with no partial write (`lib/sponsor-promotion.ts`). Caught by Security and
   Backend Architecture independently. **Cause:** the original grep combined
   `category_selections` with `excluded`, and SQLite `excluded.` upsert syntax swamped the
   output. *Grep each identifier alone before asserting it is unread.*
   The genuinely-unread set, re-verified individually: `node_hierarchy`,
   `corridor_regulatory_status.phase_unlocked`, `business_type_category_map`.
2. **The Invariant #13 citation over-extends.** `OCR_STANDARD_brainEnforcementLocation.md`
   governs where *enforcement code for brain YAMLs* lives; it does not mandate routing
   OSE-local regulatory params into the brain. Caught by DevOps and Backend Architecture
   independently. The correct precedent for `regime_constraints` is `category_registry`
   (0058) — a local D1 table.
3. **A third INTEGER copy exists.** `events.legal_clearance_tier` alongside
   `event_type_registry.legal_clearance_tier`. Doesn't change the diagnosis; widens the
   blast radius of "which column reads which."

---

## 2. The finding no lens had — a fourth and fifth representation

Found in parallel, outside the repo the lenses were pointed at.

| # | Representation | Location | Form | Values |
|---|---|---|---|---|
| 1 | `node_hierarchy.legal_clearance_tier` | 0011 | TEXT | OPEN / RESTRICTED / REGULATED |
| 2 | `event_type_registry` / `events` | 0023 | INTEGER | 1–5 |
| 3 | **`REGULATORY_POOLS`** | `src/lib/pool-contract.ts` | **TS union, brain-verified** | **general / hipaa / coppa** |
| 4 | BigQuery dataset routing | `pool-contract.ts` `BIGQUERY_DATASETS` | map | `oureventring_{general,hipaa,coppa}` |
| 5 | Brain schemas | `ocr-docs-brain/bigquery-schemas/{coppa,hipaa}.json` | JSON | COPPA / HIPAA |

The mapping is exact, and 0011's own comments make it: RESTRICTED = *"school functions, youth
events (COPPA compliance required)"*; REGULATED = *"healthcare-adjacent, museum partnerships
(HIPAA/institutional)"*.

**So `general | hipaa | coppa` is the same concept, already typed (`RegulatoryPool`), already
brain-conformance-verified, already routing live BigQuery exports, and already propagated to
every data-contributing OCR app by the propagate-standards workflow.**

**Consequence for the fix:** do not invent a third vocabulary. Adopt the live one. This also
explains the drift's origin — the *routing* use of regime went to `pool-contract.ts` while the
*governance* use on `node_hierarchy` was orphaned. One concept, two teams, two vocabularies.

**Timing argument:** ourWKRP has neither the collision nor a `pool-contract.ts`. Fixing OSE
before the contract propagates is materially cheaper than fixing every spoke after.

---

## 3. Loop 1 — Critical

| # | Concern | Sev | Lens |
|---|---|---|---|
| 1 | **The danger is one env var away, not one PR away.** `ALLOWED_MAX_TIER` is config-overridable with no code review (`resolveAllowedMaxTier`). The only thing preventing COPPA/HIPAA exposure today is `LAUNCH_MAX_CLEARANCE_TIER = 1` — an *accidental, unrelated* compensating control on the WHAT axis. Raise that env var and the WHERE axis is still dark. 0057 already names a Phase-5 `school_event` type waiting. | **High** | Security |
| 2 | **The proposed fix is DB-layer-only, and that shape has already failed once.** `node_hierarchy` has zero **writes** as well as zero reads — there is no admin UI to set a regime. The rec-centre host is never asked the question. Renaming a column nothing writes to does not fix a UI-absence problem. | **High** | PO/FE |
| 3 | **`min_clearance_tier` reproduces the disease one join away.** Sitting adjacent to `event_templates.max_clearance_tier` and `events.legal_clearance_tier`, it is the same bare-word cross-axis collision, disambiguated only by min/max. Either define what ordinal thing it measures and axis-prefix it, or drop it and keep `regime_constraints` purely categorical. | **High** | Security + BE |
| 4 | **`regulatory-schema.spec.ts` is governance theatre.** It inserts a `node_hierarchy` row and asserts CHECK constraints and column shape. A reviewer scanning test names concludes the regime is governed. It is under *shape* test only — nothing reads it to gate a decision. | **High** | SDET |
| 5 | **No detection path exists.** Zero dashboards, zero alerting, and no log line distinguishes "correctly OPEN" from "should have been RESTRICTED but nobody asked." The failure is invisible in production by construction. | **High** | SDET |
| 6 | **Mixed-type same-name collision is a live footgun.** SQLite is dynamically typed: `WHERE legal_clearance_tier <= ?` against the wrong table returns wrong or empty rows silently rather than throwing — the textbook shape of a silent authz failure. | **Med-High** | Security |
| 7 | **UNION/MAX evaluation timing unspecified.** Computed at promotion (can go stale if participants or `business_type` change) or at every read? A compliance fact computed once and never revisited is the exact class of bug this finding is about. | **Med-High** | Security |
| 8 | **Migration sequencing creates a third floor.** Production 41 / staging 68 / this change 69+, at the moment OSE-802 is supposed to collapse two into one. Batch-applying 27+ migrations to a stale production DB is a different risk profile than the file-by-file history implies. | **High** | DevOps + BE |
| 9 | **Caching point unspecified; tree-walk N+1 risk.** 0057 caches the WHAT axis onto `event_templates`. The proposal never says where the WHERE result lands. Resolving regime per render — walking `parent_node_id` up to 7 levels — is unbounded per-request cost. | **Med** | BE |
| 10 | **Test-data realism.** Every real row is tier 1 / OPEN. No RESTRICTED or REGULATED fixture exists anywhere. The WHAT gate is green only via a synthetic `TEST-TIER2-999` fixture; on real data `isTemplateSelectable` never returns false. | **Med** | SDET |
| 11 | **Brand-voice exposure if enum values surface.** `RESTRICTED` / `REGULATED` / "tier" are the engineer-jargon class the Voice Constant bans in customer copy. Not live (nothing renders it) but a translation layer must be specified before build, not caught in review. | **Med** | PO/FE |
| 12 | **The categorical claim holds.** REGULATED (HIPAA) does not subsume RESTRICTED (COPPA) — HIPAA compliance does not satisfy parental consent. `MAX()` is genuinely wrong for this axis. *Confirmed, not refuted.* | — | BE |

---

## 4. Loop 2 — Conservative

**KEEP**

1. **Rename `node_hierarchy.legal_clearance_tier`** — but to the **live vocabulary**
   (`general`/`hipaa`/`coppa` per `RegulatoryPool`), not a fresh `OPEN/RESTRICTED/REGULATED`
   coinage. Rename the dependent index too (`idx_node_hierarchy_legal_tier`). Precedent
   exists: 0064 does exactly this shape (`RENAME COLUMN unique_agents TO
   distinct_agent_hashes`), D1 ships SQLite 3.40+, CHECK constraints auto-rewrite, and the
   T1 canonical-shape gate is not tripped (`CRITICAL_DB_INDEXES` doesn't list it).
2. **The WHAT/WHERE coupling CI gate** — fail the build if `ALLOWED_MAX_TIER` /
   `LAUNCH_MAX_CLEARANCE_TIER` is ever raised above 1 while the WHERE axis still has zero
   call sites. *This is the single highest-leverage item in the whole review* — it is cheaper
   than `regime_constraints` and it closes the actual danger (Loop 1 #1).
3. **A born-red WHERE-axis invariant spec** asserting some `src/` path reads the regime before
   an event or sponsor artifact is finalised. Red today for the right reason: the join does
   not exist.
4. **One admin toggle + a hardcoded minimal exclusion list**, plain-language, zero migration —
   this closes the actual rec-centre case using the column that already exists.
5. **Sponsor-facing rejection copy**, friendly-error shaped. A gate with no visible rejection
   just moves the silent failure from host to sponsor.
6. **A structured log line** (`REGULATORY_AXIS_UNCHECKED`) at event/sponsor-draft creation —
   grep-able signal in prod the day this ships, ahead of any dashboard.

**DEFER**

7. `regime_constraints` table + UNION/MAX engine — until Loop 1 #3 (naming) and #7 (evaluation
   timing) are answered in writing, and until Phase-5 tier>1 types actually exist.
8. Mirroring `category_selections` — reuse it directly if possible rather than building a
   parallel structure. *Building two unread-then-wired mechanisms in sequence is how this bug
   happened the first time.*
9. Dashboards/alerting — join the existing backlog; don't make this finding the reason SRE
   builds a subsystem.

**CUT**

10. Tree inheritance of regime down `parent_node_id`. Require regime set explicitly per node.
    No recursive CTE, no live tree-walk.
11. Brain-YAML routing of `regime_constraints` — keep it a local D1 table per
    `category_registry` (0058).
12. More schema-shape assertions on `regulatory-schema.spec.ts` — that test *shape* is what
    produced the false confidence.

---

## 5. Loop 3 — Recursive

**REQUIRED**

1. `regulatory-regime-consulted.invariant.spec.ts` in `tests/e2e/0-architecture/`, **wired into
   the T0 `invariants` shard file list** — a new invariant spec not listed there does not run.
2. A RESTRICTED/REGULATED node fixture, proving a non-OPEN node produces a different answer
   once the read exists. Without it the rename ships and the uniform-data blind spot
   reproduces one level down.
3. An end-to-end check that a RESTRICTED node actually suppresses the excluded sponsor
   category — not a schema-level test.
4. `ROLLBACK_PLAN.md` reverse-SQL entry + CI `EXPECTED_DB` checklist in the **same commit** as
   the migration (the file's own checklist makes this merge-blocking).
5. A **production** row-count query on `node_hierarchy` before the rename is ever scheduled —
   evidence, not inference from "zero reads."
6. Brand-voice pass on every new string before merge.
7. Answer Loop 1 #7 (promotion-time vs read-time) in writing, with a test.

**RECOMMENDED**

8. Adopt `RegulatoryPool` as the single vocabulary and state the WHAT/WHERE two-axis model once,
   explicitly, in `docs/REGULATORY-PHASES.md` — which today documents regulatory-phase ×
   payment-tier as the two axes and **does not mention the WHERE axis at all**.
9. A one-time audit: repeated column names with divergent type/CHECK across non-adjacent
   migrations. This collision pattern may not be unique.
10. Re-verify every "zero reads" claim individually before it is used as a design input again.
11. Re-check `docs/REGULATORY-PHASES.md`'s reference to a `legal_corridors` table — it may be
    a fourth phantom.

**NICE-TO-HAVE**

12. A cheap static CI check flagging any new column sharing a name with an existing column on a
    different table with a different type — prevents the next collision before recon finds it.

---

## 6. Verdict

**HELD** — unanimous across Security, Backend Architecture, SDET/SRE, DevOps, and PO/Frontend.

Not FAILED: there is no live exploit. All real nodes are OPEN and the WHAT-axis launch ceiling
is doing real work. Not PASS: the proposed fix as written is DB-layer-only, and on the evidence
of this very finding, that shape has already failed once.

### Top three concerns

1. **One env var from silent COPPA/HIPAA exposure.** The compensating control is accidental and
   config-overridable without code review.
2. **The fix repeats the bug's own shape.** Schema with no reader, and now no writer either —
   there is no UI to set a regime.
3. **Nothing would detect it.** No alerting, and the one test suite in the area produces false
   confidence that governance exists.

### Top three follow-ons

1. The WHAT/WHERE coupling CI gate — cheapest item, closes the actual danger.
2. The born-red invariant spec, wired into the T0 shard list.
3. Adopt `RegulatoryPool` (`general|hipaa|coppa`) as the one vocabulary before the contract
   propagates to other spokes.

### Holds — all must clear before PASS

1. **Do not raise `ALLOWED_MAX_TIER` above 1** until the WHERE axis has a call site. Enforce
   this as a CI gate, not a convention.
2. **No `regime_constraints` build** until (a) `min_clearance_tier` is renamed/axis-prefixed or
   dropped, and (b) promotion-time vs read-time evaluation is answered in writing with a test.
3. **No production application of the rename** until OSE-802 has fired, production is confirmed
   at the code floor, and a live production row-count on `node_hierarchy` is recorded.
4. **Do not bundle** the rename with `regime_constraints` — separate migration, separate story.
5. **No approval of a DB-only plan.** Any approval must carry, as one unit: the admin toggle,
   the sponsor rejection copy, and an end-to-end enforcement test.
6. **Adopt the existing `RegulatoryPool` vocabulary** rather than coining a third.

### Clear to proceed now, unheld

Writing and merging the `RENAME COLUMN` migration **file** (with index rename and
`ROLLBACK_PLAN.md` entry) — CI T1 validates it against a fresh schema, precedent is 0064, and
the hold is on *production application*, not on writing the code.

---

*Five role lenses run as independent CCR passes; findings deduplicated and severity-reconciled.
Two recon errors were caught by lenses and are recorded in §1. §2 is a finding no lens had.*
