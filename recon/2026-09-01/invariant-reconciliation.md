# invariant-reconciliation — register ↔ code ↔ docs

> **Date:** 2026-09-01 · **Register:** `ocr-docs-brain/architectural-invariants.yaml` · **Code:** ourSharedEvents @ `14f5c3b`
> **Method:** mechanical join, not reading. Register `test_file` → file on disk → named in `.github/workflows/`. Scope: the 23 invariants carrying `ose` in `applies_to`.
> **Correction made during the run:** a first pass derived spec names from invariant names (`hyperlocal_geo_resolution` → `hyperlocal-geo-resolution…`) and produced 14 false "unregistered" hits. The real convention is unrelated to the name (`#2` → `geo-resolution.invariant.spec.ts`). Redone against the register's own `test_file` field. The numbers below are from the corrected join.

## 1. Register → code

| Outcome | Count | Invariants |
|---|---|---|
| Declared file exists **and is gated** in T0 | **15** | #5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 21, 25 |
| Declared file exists, **NOT gated** | **4** | **#1, #2, #3, #4** — see §1.1 |
| Declared non-spec path, gated | 1 | #22 → `scripts/check-cross-repo-imports.sh`, invoked in `brain-contract-check.yml` ✅ |
| Declared path exists, gated by nothing | 1 | #23 → `tests/red-team/` — 5 files, **zero workflows** |
| **Declared file does not exist** | **2** | #14, #24 — see §1.2 |

### 1.1 Four `live` invariants are not enforced in CI — and they are the privacy core

| # | Name | Status | Spec | Gated |
|---|---|---|---|---|
| 1 | `anonymous_id` | **live** | `anonymous-id.invariant.spec.ts` ✅ exists | ❌ |
| 2 | `hyperlocal_geo_resolution` | **live** | `geo-resolution.invariant.spec.ts` ✅ exists | ❌ |
| 3 | `uec_encoding` | **live** | `uec-codes.invariant.spec.ts` ✅ exists | ❌ |
| 4 | `ncr_data_accumulation` | **live** | `ncr-accumulation.invariant.spec.ts` ✅ exists | ❌ |

All four run **only** in T4a "Architecture Invariants", which executes the whole `tests/e2e/0-architecture/` directory against live staging — and T4 fires only on `workflow_dispatch` with a checkbox or a `full-pipeline/*` branch. Never on PR, push, or nightly.

**The register defines `live` as "currently enforced in CI."** By its own definition these four are not live. They are anonymous ID, hyperlocal geo resolution, UEC encoding, and NCR accumulation — the identity and privacy floor of the platform.

This is defensible as *design* — those four assert runtime behaviour and genuinely need a running worker, which is why they sit in the deployed tier. It is not defensible as *status*. Either the status is wrong, or the tier is.

### 1.2 Two declared files do not exist

- **#14 `mobile_workability`** (`partial`) declares `mobile-workability.invariant.spec.ts`. **No such file.** Real enforcement is `.github/workflows/mobile-workability-audit.yml`, which is `continue-on-error` on `pull_request` and blocking only on the nightly schedule. The register points at a file; the enforcement is a workflow; neither references the other.
- **#24 `auditability`** (`partial`) declares `tests/audit-layer.spec.ts`. **No such file**, and no equivalent exists. The invariant's own protective statement says the audit layer "must never become a re-identification surface… enforced by tests that attack the logs." Nothing attacks the logs.

## 2. Code → register — enforcement with no invariant number

Six specs run in the **blocking** T0 `invariants` shard that **no register entry declares**:

| Spec | What it locks |
|---|---|
| `cost-metric-never-who.invariant.spec.ts` | seals the cost-metric payload to aggregate keys, forbids identifier tokens |
| `edge-token-verification.invariant.spec.ts` | edge token verification |
| `runtime-llm-free.invariant.spec.ts` | the standing fleet-wide L0 assertion named in `OCR_STANDARD_perStoryTestPyramid` — a *standard*, never a numbered invariant |
| `scan-path-split.invariant.spec.ts` | scan-path separation |
| `sponsor-identity-split.invariant.spec.ts` | sponsor identity separation |
| `worker-claude-md.invariant.spec.ts` | worker CLAUDE.md contract |

Plus `workers/oursharedevents/tests/schema-lexicon.spec.ts` (OSE-801) — the banned-term lexicon, PR-blocking, and absent from the register entirely (staged only as unmerged proposal #26/#27).

**Net: the register undercounts OSE's mechanical enforcement by at least seven gates.** `cost-metric-never-who` and `schema-lexicon` both enforce "never who, always how many" — the platform's central doctrine — and the constitution records neither.

## 3. Register → docs — internal contradictions

| # | Contradiction | Which side is right |
|---|---|---|
| 21 | `status: live` vs `activation_note`: *"Status PARTIAL (honest)… not yet wired to CI"* | **status.** The spec exists and is gated. The prose is stale. |
| 25 | `status: live` vs `test_file`: *"(OSE repo — planned, OSE-663 / OSE-662)"* | **status.** The spec exists (8,887 B) and is gated. The `test_file` annotation is stale. |
| 14 | `status: partial` vs a `test_file` naming a nonexistent spec | **neither.** The file never existed; enforcement lives in a workflow the entry does not mention. |
| 24 | `status: partial` vs a `test_file` naming a nonexistent spec | **neither.** No enforcement exists in either place. |

`level2_schema.py:121-127` requires only that `test_file` be a **non-empty string** — it never reads the content. So a value containing the literal word "planned", or naming a file that does not exist, passes brain validation cleanly. That is why the brain scores 10/10 on its own pyramid while four of these four contradictions stand.

## 4. The reconciliation, stated once

**Against the code**, the register is wrong in three ways: it calls four invariants `live` that no PR gate enforces; it declares two files that do not exist; and it omits at least seven gates that do.

**Against the documentation**, it contradicts itself on four entries, and its own validator cannot detect any of them because it type-checks the field instead of resolving it.

**The single change that closes most of this** is one check the brain does not have: resolve every `test_file` to a path, assert the path exists, and assert it is named in a blocking workflow — then invert it and assert every gated invariant spec has a register entry. Both directions, mechanically. This artifact is that check run by hand once; as a script it would have failed on the day each of these drifted.

---

## 5. The reconciliation checklist, as it now stands

Each item is a check that would have failed on the day the drift it catches was introduced. Two are now implemented; the rest are open.

| # | Check | Direction | State |
|---|---|---|---|
| 1 | Every register `test_file` resolves to a path that **exists** | register → code | **open** — 2 entries fail today (#14, #24) |
| 2 | Every register `test_file` is **named in a blocking workflow** | register → code | **open** — 4 `live` invariants fail (#1, #2, #3, #4) |
| 3 | Every gated invariant spec has a **register entry** | code → register | **open** — 7 gates unrecorded |
| 4 | Every register `status` agrees with its own prose | register → docs | **open** — 4 contradictions (#14, #21, #24, #25) |
| 5 | Every `applies_to` names a surface that **could violate** the invariant | register → estate | **open** — ~17 pairs on code-empty repos |
| 6 | **Every tier has a placement guard** | code → CI | **2 of N done** |

### Item 6 — added 2026-09-01

A tier runs because of one line somewhere: a shard name in a matrix, a glob in a config, a filename on a command line. Nothing asserts those lines stay. Delete one and the suite still reports green, because a test that is never *discovered* cannot fail. This estate has produced that failure three times already — 55 FE specs named in no workflow, `tests/red-team/` (1,847 lines) referenced by nothing, and OSE-852's Playwright steps discovering zero tests.

The repo already had one guard of this shape, for the invariants shard (OSE-350): classify the specs, assert every structural one is wired into the T0 step. It was never generalised.

Now implemented for two more tiers:

- **component** — asserts the matrix carries the shard, the step exists, `playwright.component.config.ts` exists *and defines a webServer that starts `wrangler dev`* (without which the tier silently reverts to pointing at staging), the batch names ≥1 spec, and every named spec exists on disk. Mutation-proved both ways.
- **pact** — asserts `tests/pact/**` is in the vitest include, the verifier exists, ≥1 `.pact.json` is defined, and every pact names a provider snapshot that exists. Mutation-proved: removing the include drops the pacts from discovery entirely while the suite stays green.

**Still unguarded**, in rough priority: the a11y shard, the lint shard's individual guards (banned-origins, no-GAS, covenant), the T2 Newman collections, and T4a's own directory glob.

### A seam worth naming

The invariants placement guard passes today while four `live` invariants are ungated — because the guard classifies those four as **runtime** (they use `page`/`request`/`baseURL`) and exempts runtime specs from T0. The guard encodes *"runtime specs may be T4-only."* The register encodes *"live = enforced in CI."* Each is internally consistent; together they contradict, and that contradiction is exactly what OSE-1151 asks a human to resolve.

## 6. Test automation still owed on this session's own changes

Recorded rather than quietly skipped:

| Change | Coverage | Gap |
|---|---|---|
| component tier | placement guard + 35 specs green in CI | none |
| pact tier | placement guard + 22 checks, mutation-proved | none |
| XSS mock fix | the test itself, now passing for the right reason | none |
| `branch-protection-drift.yml` | **none** | it calls `apply-branch-protection.mjs`, whose pure `normalize()` and `diff()` have no unit test. PR #430 set the precedent exactly — a pure classifier plus `cf-access-probe.test.sh` wired into the T0 lint shard. This should match it. |
| `dashboard.py` path fix | **none** | the bug was "paths resolve wrong off one machine", which is precisely unit-testable: assert `BRAIN_REPO` resolves to the repo containing the script. Natural home is the brain's `level3_unit.py`. |
