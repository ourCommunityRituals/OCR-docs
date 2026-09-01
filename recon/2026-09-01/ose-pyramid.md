# ose-pyramid — ourSharedEvents CI/CD ↔ test pyramid, four traversals

> **Agent:** `pyramid-tracer` · **Date:** 2026-09-01 · **Repo:** ourSharedEvents @ `14f5c3b`
> **Lead verification:** the two highest-severity claims re-checked directly. Both confirmed.

## Gate Queue

**1. Production is reachable on S0 + T0 alone, via a tag push that touches no branch protection.**
`deploy-production` declares `needs: [security, gate]` — **verified**, `oursharedevents-ci.yml:1607`. It does not name `deploy-staging`, `contract-staging` (T2 Newman), `smoke-staging` (T3), or `functional-staging` (T4). Its trigger is `push` on `refs/tags/v*` **or** `workflow_dispatch` with a typed `PRODUCTION` string. No tag protection is codified anywhere in the repo — only `main` branch protection exists.

So: merge through a normal PR (S0 + T0 only), then push a tag on a later, disconnected run. The tag run re-runs S0 + T0 against that SHA and deploys. Whether the API contract suite, the E2E smoke suite, the entire T4 functional tier, or the S2 tamper tripwire ever passed is not checked, not referenced, and structurally cannot be — they are separate workflow executions with no state carried across.

**2. `S2 Post-Execution Security` is a required check no workflow produces.**
`tools/ci/main-branch-protection.json:7` requires the context `S2 Post-Execution Security`. **Verified:** that string appears in exactly two places in the repo — that JSON, and `README-branch-protection.md:17`. No job, no step, in any of the 18 workflows emits a check by that name. The job that did (`security-post`) was retired by `5016aed` (2026-08-28) and its logic re-homed to a step at the tail of `functional-staging`, which `if:`-skips on `pull_request` entirely. The branch-protection JSON was never updated — one commit has ever touched it.

Two possible live states, both bad: GitHub still requires the dead context, and every PR sits at "Expected — waiting for status"; or it was edited out-of-band on GitHub without updating the versioned source of truth, which is exactly what `README-branch-protection.md:6-8` exists to prevent. **And the drift detector that would catch this — `scripts/apply-branch-protection.mjs --check`, documented as "safe to wire into CI" — is invoked by no workflow** (verified: zero hits).

**3. Five of ten raw `npx playwright test` call sites lack the zero-discovery guard, including a required merge gate.**
`scripts/pw-guarded.sh` exists because of a real incident (OSE-852): a Playwright step that discovers zero tests is indistinguishable from one whose tests all passed. It is wired into 4 of 10 invocations. Unguarded: **`T0 Gate (invariants)`** — a *required* check running 19 explicitly-listed file paths — plus all three `smoke-staging` steps, T4b, T4c, and both `smoke-production` steps. A rename that silently drops files from that 19-path list would not necessarily exit non-zero. The fix exists two shards away and was never applied to the one shard that gates merges.

**4. T3 is dead on every trigger, because T2's broken token gates it.**
`smoke-staging` is hard-gated on `needs.contract-staging.result == 'success'` with no schedule bypass. `contract-staging` depends on the CF Access service token that has been stale since 2026-05-19. So the entire T3 E2E smoke tier has not run on any trigger — push, tag, or nightly — for over three months. One expired credential silently removed a whole tier.

**5. The red-team suite has no CI root, and it is not one step from having one.**
`tests/red-team/` (5 files, 1,847 lines) plus `test:red-team*` scripts and `playwright.red-team.config.ts` — **zero hits across all 18 workflows** (verified). Its own header states the intended placement ("nightly / pre-release CI gate") that was never implemented. Correction to the Wave 1 rollup, which called this the cheapest item: the config targets live staging (`baseURL` → `https://stg.oursharedevents.com`) and needs `ADMIN_KEY`, `X_OCR_INTERNAL`, and a seeded `SMOKE_EVENT_ID`. It is blocked on the same credentialed-staging precondition as items 4 and OSE-349 — not on a missing workflow step.

## Traversal summary

**Bottom-up.** Unit, contract, integration, worker unit/schema, a11y and the 19 structural invariants all reach a required check. Everything from T2 down is advisory to merge by trigger design — documented, not accidental. Red-team is the one fully-built layer with no CI root at all.

**Top-down.** Every required check except one rests on a real assertion: S0 propagates semgrep's exit code and fails on new secrets; T0's lint shard runs the sponsor-pricing covenant and the no-GAS guard; the tests shard runs the full vitest suite with no `continue-on-error`. The exception is item 2. Notably the **T3 Newman covenant assertion is genuinely correct** — when the token is stale the collection calls `pm.expect.fail('COVENANT TEST BLOCKED…')` rather than skipping, and `contract-staging` re-asserts the failure at `:1291-1295`. It is a true red. Its correctness simply doesn't matter, because nothing on the path to production depends on it.

**Left-to-right.** A tag push skips `deploy-staging` (path-filtered on `refs/heads/main`), and with it T2, T3 and T4. T4 additionally never runs on push, PR, or nightly — dispatch-only, by documented cost control.

**Right-to-left.** See item 1. `smoke-production` runs *after* `deploy-production`, so it inspects an already-shipped build.

## Verification (lead session)

| Claim | Result |
|---|---|
| `deploy-production: needs: [security, gate]` only | ✅ `oursharedevents-ci.yml:1607` |
| Tag + `workflow_dispatch` both reach it | ✅ `if:` block at `:1608-1610` |
| `S2 Post-Execution Security` required but produced by nothing | ✅ 2 hits repo-wide, both documentation |
| `apply-branch-protection` wired into no workflow | ✅ zero hits |
| `red-team` referenced by no workflow | ✅ zero hits |
