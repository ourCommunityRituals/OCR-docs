# ose-coverage-grid — surface × layer coverage, keyed to what actually gates

> **Date:** 2026-09-01 · **Repo:** ourSharedEvents @ `14f5c3b` · Lead session, verified per cell
> **Supersedes:** `docs/qa/TEST_MATRIX.md` in OSE — dated **November 2025**, ~10 months stale.
> **Question this answers:** for each surface, at each layer — is there coverage, what kind, and does it gate anything?

## The rule this grid is built on

A test is not coverage. **A test is coverage only if a gate fails when it is violated.** Every cell below is therefore two facts: what exists on disk, and whether CI will stop a merge or a deploy because of it.

CI invokes Playwright **by explicit file list** at every call site. A spec not named in a workflow runs nowhere, regardless of where it sits in the tree. That single mechanic explains most of this grid.

## The grid

| Surface | Worker unit (vitest) | Root unit/contract | Structural invariant | FE (Playwright) | API contract (Newman) |
|---|---|---|---|---|---|
| **admin** | 23 files — **GATED** (T0 `tests`) | in root vitest — **GATED** | none | 22 files — **UNGATED** | 172 refs — T2, **dead since 2026-05-19** |
| **public** | 7 — **GATED** | — **GATED** | none | 9 — **UNGATED** | 27 refs — dead |
| **display** | 2 — **GATED** | — **GATED** | none | 12 — **UNGATED** | 18 refs — dead |
| **poster** | 12 — **GATED** | — **GATED** | none | 9 — **UNGATED** | 38 refs — dead |
| **shared-report** | 9 — **GATED** | — **GATED** | 1 — **GATED** (T0 `invariants`) | 3 — **UNGATED** | 11 refs — dead |

**Legend.** GATED = a failure blocks a merge on `pull_request`. UNGATED = the file exists and no workflow names it. Dead = the tier exists and cannot currently run.

## What the grid says

**1. The unit layer is solid and gating. The browser layer is entirely ungated.**
53 worker unit specs across the five surfaces all run in the blocking T0 `tests` shard via a glob. Meanwhile **55 Playwright specs covering those same five surfaces are named in zero workflows** — verified individually: `admin-page`, `public-page`, `display-page`, `poster-page`, `admin-dashboard`, `display-kiosk`, `poster-print`, `public-events`, `shared-report-mobile` each return **0 workflow hits**.

T4 `functional-staging` names only `form-registration`, `form-checkin`, `form-email-signup`, `form-survey`, `sponsor-journey` and `cross-brand-isolation`. T3 `smoke-staging` names only `security-smoke`, `api-health`, `fail-fast-gates` and `form-endpoints`. The surface page specs appear in neither.

So: every surface has real browser tests, and no surface has browser coverage that can fail a build.

**2. Four invariant specs run only on manual dispatch — and they are the privacy core.**
25 `*.invariant.spec.ts` exist; 21 are named in the blocking T0 `invariants` shard. The four that are not:

- `anonymous-id.invariant.spec.ts`
- `geo-resolution.invariant.spec.ts`
- `ncr-accumulation.invariant.spec.ts`
- `uec-codes.invariant.spec.ts`

They run in **T4a Architecture Invariants**, which executes the whole `tests/e2e/0-architecture/` directory against live staging with `ADMIN_KEY`, `X_OCR_INTERNAL` and a seeded `SMOKE_EVENT_SPONSORED`. T4 fires only on `workflow_dispatch` with a checkbox, or a `full-pipeline/*` branch — never on PR, push, or nightly.

**These four are the identity and privacy invariants — anonymous ID, hyperlocal geo resolution, NCR accumulation, UEC encoding. They are verified only by a job nobody triggers, against an environment that has been credential-broken since 2026-05-19.** This is the sharpest single statement the whole recon produced. It is by design (runtime behaviour genuinely needs a live worker), and the design has a hole in it.

**3. The API contract column is a whole layer that cannot run.**
266 Postman references across the five surfaces, in a T2 tier hard-blocked by the stale CF Access service token — and T3 is `needs:`-gated on T2, so both tiers have been dark for over three months on every trigger including nightly.

**4. Structural invariant coverage is uneven by surface.**
Only `shared-report` has a surface-specific gated invariant. `admin`, `public`, `display` and `poster` have none — their structural guarantees are covered obliquely, through cross-cutting invariants (`sponsor-share-covenant`'s WALL-3b geometry sub-suite touches `display`/`poster`/`public`/`shared-report` templates) rather than by a per-surface contract.

## The ratified matrix — `FE-DEV-PREP-2026-08-29.md` §1

**This is the current grid, and it supersedes `TEST_MATRIX.md` as the thing to reconcile against.** Dated 2026-08-29, status *Ratified (Phase A in progress)*, owner PO. It defines a parameterized matrix — 4 screens × 5 cells (`wizard|advanced` × `local|mid|enterprise`, with `wizard × enterprise` excluded by design because enterprise is provisioned through the OA layer, never self-serve).

| | Doc says | Reality |
|---|---|---|
| Spec home: `tests/e2e/3-flows/sponsor-lifecycle.matrix.spec.ts` | core deliverable | **exists**, 6,479 B, implements scenario × tier across admin path / public / sponsor card / display |
| Fixture home: `tests/e2e/fixtures/scenario-tier-matrix.ts` | mirrors `demo.ts` mapping | **exists**, 4,437 B, mapping documented, design gap explained |
| `is_local` asserted independently of tier | covenant floor, every cell | **implemented** — `sponsor-local-badge` asserted separately, comment states it renders because the sponsor IS local, never because of tier |
| Runs in CI | implied by "core deliverable" | **ZERO workflow references** |

**The spec is well-built and wired to nothing.** T4b `Core Journeys` names `sponsor-journey.spec.ts` and `cross-brand-isolation.spec.ts` — not the matrix spec. Verified: `grep -rn "sponsor-lifecycle.matrix" .github/workflows/` returns nothing.

### Why that is worse than an ordinary ungated spec

The suite is **born-red by design**. Its own header: *"BORN-RED (Phase A): the wizard admin path does not exist yet — those cells MUST fail today. Their failure is the proof this suite bites."*

A born-red suite that no workflow runs cannot prove anything. Nobody observes the red, so the claim that it bites is untested. And when Phase B ships the wizard, **nothing will turn green**, because nothing is watching. The mechanism that makes born-red valuable — a visible failure that flips to visible success — is absent at both ends.

### And wiring it into T4 would not be enough

T4 `functional-staging` is dispatch-only (checkbox or a `full-pipeline/*` branch — never PR, push, or nightly), runs against live staging, and needs `CF_ACCESS_CLIENT_ID`/`SECRET` — the credential stale since 2026-05-19 that already killed T2 and T3. Adding the matrix spec to T4b would move it from *ungated* to *in a tier that cannot currently run*.

**This is the doc → code → CI chain, traced on a two-day-old ratified document.** Doc and code agree; code and CI do not; and the CI tier it would join is itself dark. That is the reconciliation gap, located precisely.

---

## The older matrix it supersedes

`docs/qa/TEST_MATRIX.md` is the right structure and stale in a specific, correctable way. Of eight test files it cites, four are **archived**:

| Cited file | Reality |
|---|---|
| `template-service.test.js` | `archive/legacy-tests/tests/unit/` |
| `template-flows.contract.test.js` | `archive/legacy-tests/tests/contract/` |
| `api.contract.test.js` | `archive/legacy-tests/tests/contract/` |
| `sponsor-utils.test.js` | `archive/legacy-tests/tests/unit/` |
| `admin-page.spec.js` | live, `tests/e2e/2-pages/` — but ungated |
| `public-page.spec.js` | live, ungated |
| `display-page.spec.js` | live, ungated |
| `sponsor-page.spec.js` | live, ungated |

**Every unit and contract row in the existing matrix points at retired GAS-era tests.** The four surviving rows are the e2e ones, and all four are ungated. The matrix reports coverage that is either archived or unwired — which is the most expensive kind of stale doc, because it answers "are we covered?" with yes.

## Where this grid belongs

Per `.ocr-standards/standards/OCR_STANDARD_perStoryTestPyramid.md`, each story ships a unit/worker spec, a Postman entry, and a Playwright spec, named `<STORY-ID> | <LAYER> | <method+path (condition)> | <assertion>`. The standard defines the layers; this grid measures them. Two things follow:

1. The grid should be **generated, not written** — from the CI workflow's own file lists joined against the tree. Written by hand it will be stale in ten months, exactly like the one it supersedes.
2. The generator answers the reconciliation question directly: for surface S at layer L, is there a spec, and does a gate name it? That is the same register↔CI-wiring join the brain needs for invariants, applied one level down.

## Verification

Every number re-derived from the tree in this session: `git ls-files` for existence, `grep -rl` against `.github/workflows/` for gating, individually per spec for the nine surface pages, and `comm` between the 25 on-disk invariant specs and the 21 named in CI.
