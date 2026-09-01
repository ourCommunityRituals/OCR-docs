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

## Reconciling the doc that already exists

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
