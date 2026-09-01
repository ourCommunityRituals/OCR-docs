# ose-pyramid-rungs — climbing the ladder, rung by rung

> **Date:** 2026-09-01 · **Repo:** ourSharedEvents @ `14f5c3b` · Lead session, every cell verified
> **Ladder (as specified):** pact → contract → lint → unit → component → integration → API → DB → FE → e2e → regression deep dives → mutations

## Status by rung

| Rung | State | Gated? | Evidence |
|---|---|---|---|
| **pact** | **BUILT this session** | ✅ T0 `tests` | `tests/pact/` — 22 checks, mutation-proved. Branch `test/pact-layer-l8` |
| **contract** | Real coverage exists; the file count misleads | ✅ partial | see below |
| **lint** | Solid | ✅ T0 `lint` | banned-origins, sponsor-pricing covenant (#25), no-GAS guard + self-tests, schema-guard constants, eslint, static manifest preflight |
| **unit** | Solid | ✅ T0 `tests` | 60 files / 1,841 tests pass locally; 53 worker specs across the five surfaces |
| **component** | **ABSENT** | — | OSE-1070 classifies **47 specs / 995 tests** as COMPONENT/VIEWPORT, destination "real-engine Playwright CT on Chromium *and* WebKit — no deploy" |
| **integration** | **ABSENT** | — | OSE-1070 classifies **43 specs / 573 tests** for in-job miniflare / wrangler dev |
| **API** | Two executors, **both dark** | ❌ | see below |
| **DB** | Gated only at deploy time | partial | `deploy-production`'s own gates: canonical D1 shape, zero unapplied migrations, no unprovisioned binding IDs. Real, but they run at deploy, not on PR |
| **FE** | Exists, **gates nothing** | ❌ | 55 Playwright specs across the five surfaces, named in **zero** workflows |
| **e2e** | Dispatch-only or dead | ❌ | T4 fires only on a checkbox or a `full-pipeline/*` branch |
| **regression deep dives** | One script exists | ❌ | `test:deepdive:newman` → `ose-api-sharedreport.json`, in no workflow |
| **mutations** | Used ad-hoc, no standing score | ❌ | this session mutated the provider snapshot to prove the pact layer bites; nothing measures mutation score continuously |

## The contract rung — the file count is not the coverage

21 files sit in `tests/contract/`. **None of them imports provider source or references the schema snapshots.** Their imports are: `../shared/helpers/test.helpers` (11), `../shared/fixtures/*` (7), `../shared/helpers/test-runner.js` (4), `path`/`fs`, `config/brand-config`.

What they assert, in sample: `expect(isEnvelope({ ok: true, value: { foo: 'bar' } })).toBe(true)`. That validates the **validator helper** against a literal the test wrote itself. If the Worker stopped emitting envelopes tomorrow, it stays green.

**This is not useless code — it is mislabeled.** Testing `isEnvelope()` is legitimate *unit* testing. The defect is that it is filed and counted as contract coverage. This is exactly OSE-1070's demotion thesis, applied one directory over: 21 files that belong at the unit rung.

**The contract rung's real coverage is three things, and all three are gated and offline:**

1. `api-response-schema.invariant.spec.ts` (#16) — locks that every `projected_column` in the snapshot appears in the `handleListEvents` / `handleGetEvent` SELECT, that the envelope keys are returned, and that `enrichWithPhase` runs. **Snapshot → handler.**
2. `shared-report-schema.invariant.spec.ts` (#21) — the output-side complement.
3. `tests/pact/` (new) — **consumer → snapshot.**

Together those close the chain end to end without a deployed worker:

```
consumer reads field  →  pact  →  snapshot  →  handler SELECT
   (template grep)     (new)     (existing)     (existing)
```

Every link gated in T0. That is the contract rung actually standing up.

## The API rung — two executors, both dark, and it is not where the docs say it is

**Executor 1 — Newman.** Three collections (`ose-api.json`, `ose-pages.json`, `ose-api-sharedreport.json`), environments, fixtures, and **seven** npm scripts. Runs in T2 `contract-staging`. Blocked since 2026-05-19 on the CF Access service token.

**Executor 2 — Playwright in API mode.** `tests/api/smoke/{api-health,fail-fast-gates}.spec.ts` at `ci.yml:1005` and `form-endpoints.spec.ts` at `:1016`, via `playwright.smoke.config.ts`. These run in T3 `smoke-staging` — which is hard-gated on `needs.contract-staging.result == 'success'`. **So executor 2 is dark for the same reason as executor 1, one hop removed.** The same two specs also run in `smoke-production` (`:1865`), post-deploy.

This matches the `perStoryTestPyramid` standard, which defines `API` and `FE` as layer *qualifiers* rather than tools — API from "Postman/Newman, curl, vitest with `SELF.fetch()`, Playwright API mode", FE from Playwright. Playwright legitimately holds both.

Of 27 files under `tests/api/`, **12+ are under `archive/`**; the live API surface is three specs.

### Where the API rung is supposed to live

`ourSharedMagnets/CLAUDE.md:9` states OSM *is* "API and white label support. **Postman collections. Newman CI.**" Lines 33–34: "Postman collections for all OSE endpoints / Newman CI integration for API testing."

**OSM contains zero Postman collections.** Measured: 31 tracked files, 0 code files, and the only Postman/Newman occurrences are prose in `CLAUDE.md`, `README.md`, `SKILL.md` and the propagated `.ocr-standards/` copies. All three collections and all seven Newman scripts are in OSE.

In fairness, the same CLAUDE.md says "This repo is currently documentation-as-code… will be added as the platform matures," so lines 33–34 read as intended scope rather than a claim about today. The finding is narrower and still real: **the ownership boundary is declared but unimplemented, and a reader sent to OSM for the API rung finds nothing there.** Either move the collections, or mark the claim as planned in the same sentence that makes it.

## What the ladder says to do next

The two rungs with the best return are **component** and **integration**, for the same reason pact was the right place to start: OSE-1070 has already classified them (47 specs / 995 tests and 43 specs / 573 tests), and **neither needs staging or the CF Access token**. Everything from API upward does.

The FE rung is the largest single gap — 55 specs, zero gating — but wiring it means choosing a tier, and every tier above integration is currently dark. Component-testing those surfaces (no deploy) reaches the same code sooner.
