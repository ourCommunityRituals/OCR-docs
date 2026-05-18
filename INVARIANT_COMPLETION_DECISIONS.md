# Brain Invariants — completion decisions (#6, #8, #9)

**Status:** PROPOSED — awaits founder sign-off
**Date:** 2026-05-18
**Author:** Co-Architect
**Related:** `OCR-docs/ocr-docs-brain/architectural-invariants.yaml` (current canonical), CCR-5 audit (in-session)

---

## Why this doc exists

CCR-5 (5 loops × 7 SCRUM roles) audited the six "partial" brain invariants. Three need explicit founder choice — **build the missing piece** or **downgrade the brain status to reflect reality**. The founder's standing preference is "finish invariants" (build, don't downgrade), but each invariant has a different shape and a different cost, so the choice should be made deliberately per invariant.

Priority 1 already shipped the no-controversy ones:
- #5 (tier_equity) → covered by `tier-equity.invariant.spec.ts` + ADR-013
- #10 (deprecation_lock) → covered by `deprecation-lock.invariant.spec.ts` + CI wiring (just landed)
- #11 (runner_env) and #12 (runner_pool_readiness) → invariants tests landed; brain entries pending (sister proposal to be filed after these three are decided)

This doc covers the remaining three.

---

## #6 — Inert Monetization Hooks

### Brain (today)
- Status: `partial`
- Enforces: `X-Monetization-Inert: true` header on every response; no billing logic executes; billable units are read-only
- Promotion note: "Existing CI gate checkMonetizationHooksInert + contract test story-f4-monetization-hooks_MOCK.test.js already enforce; promote to 0-architecture suite."

### Verified reality
- `scripts/security/` references `checkMonetizationHooksInert` — gate exists
- `tests/contract/story-f4-monetization-hooks_MOCK.test.js` exists and runs
- The `X-Monetization-Inert: true` header is asserted in contract tests, NOT in a structural 0-architecture test
- The handler that emits the header is generic middleware — easy to break silently if someone "tidies up" response headers

### The choice

**A. Build (recommended).** Write `tests/e2e/0-architecture/monetization-inert.invariant.spec.ts` following the same pattern as the 4 tests that landed today. Two assertions:
1. The middleware that emits `X-Monetization-Inert: true` exists and the literal string is present
2. No file under `src/` references billing libraries (Stripe, Square, etc.) — fail-closed against accidental introduction

Estimated: 1 PR, ~120 lines of test code, runs in <1s.

**B. Downgrade.** Change brain status to `planned` and remove the "already enforce" text. Cheap (1-line YAML change) but contradicts the founder's standing preference.

### Recommendation: **A — Build.**

The mechanism really does exist; the only missing piece is the structural test that catches a future contributor breaking it. This is the same gap we just closed for #10 — the cost is small and the protection is durable.

---

## #8 — Bounded PII Retention

### Brain (today)
- Status: `partial`
- Enforces: All opt-in PII has a finite TTL (`expires_at`, `retention_expires_at`); daily lifecycle cron deletes expired registrations (90d), scrubs survey PII, deletes expired email signups (30d)
- Promotion note: "Cron + TTL columns + PRIVACY.md exist; promote unified test to 0-architecture suite."

### Verified reality
- `workers/oursharedevents/tests/lifecycle.spec.ts` exists and runs the real cron via `worker.scheduled()`
- Test verifies actual PII cleanup across `form_registrations`, `form_surveys`, `email_signups`, `pii_audit_log`
- The mechanism is genuinely shipped — this is the closest to "live" of the three

### The choice

**A. Build (recommended).** Write `tests/e2e/0-architecture/pii-retention.invariant.spec.ts`:
1. Assert the cron handler file exists and references each PII-bearing table by name
2. Assert each table in question has the TTL column declared in its migration
3. Assert no PII-bearing table is missing from the cron (the failure mode this guards: someone adds a new PII column without wiring it into the cleanup loop)

Estimated: 1 PR, ~150 lines.

**B. Downgrade.** Same as #6 — contradicts the stated preference and loses the future-proofing benefit.

### Recommendation: **A — Build.**

This is the highest-value invariant of the three because **the failure mode is silent PII over-retention** — a regulatory liability if it ever happens. The test costs little; the protection is meaningful.

---

## #9 — Tenant Isolation

### Brain (today)
- Status: `partial`
- Enforces: Dual-key pattern (`id` + `brandId`) on every multi-tenant table; no cross-tenant data leakage in queries; brand-scoped URLs maintain isolation
- Promotion note: "Schema pattern exists; needs the cross-cutting test."

### Verified reality
- Search for `tenant.*isolation` or `brandScoped` helper across `workers/oursharedevents/src/` returns essentially nothing
- The schema has the column shape; queries DO filter by brandId — but **inconsistently** (each handler does its own `WHERE brand_id = ?`)
- Failure mode: a future handler forgets the brandId filter. No centralized helper means no central enforcement.

This is the **weakest** of the three. The brain claim is aspirational, not yet structural.

### The choice

**A. Build full (most comprehensive).** Two steps:
1. Centralized helper: `src/lib/brand-scoped-query.ts` that every multi-tenant query routes through. Type-safe — calling it without a brandId is a compile error.
2. Structural test: `tests/e2e/0-architecture/tenant-isolation.invariant.spec.ts` that asserts every handler touching a multi-tenant table calls the helper (regex over source).

Estimated: 1 PR for the helper + migration of existing call sites (~10-15 files), 1 PR for the structural test. Medium effort — the migration touches every multi-tenant query path.

**B. Build narrow (partial).** Skip the helper, just write the structural test that asserts every `SELECT/INSERT/UPDATE` against a multi-tenant table includes `WHERE brand_id` literally. Cheaper but more brittle (regex on SQL).

**C. Downgrade.** Honest about current state. Doesn't fix the underlying inconsistency.

### Recommendation: **A — Build full.**

This is the most comprehensive path and best aligned with the founder's "comprehensive" preference. It's also the only path that turns the invariant from "documented intent" into "mechanically enforced." Cost is medium (one PR's worth of migration work), payoff is durable.

If timing pressure forces a compromise, B is the fallback — it at least catches new violations even if it doesn't fix existing inconsistencies.

---

## Summary table

| Invariant | Today's status | Reality check | Recommended path | Effort |
|---|---|---|---|---|
| #6 inert_monetization_hooks | partial | mechanism exists, no structural test | A — Build structural test | Small |
| #8 bounded_pii_retention | partial | mechanism exists, real cron test exists, missing structural test | A — Build structural test | Small |
| #9 tenant_isolation | partial | schema exists, no centralized helper, inconsistent enforcement | A — Build helper + migration + test | Medium |

Common pattern across all three: the 0-architecture structural test is the missing layer that catches *future* drift. The mechanisms already exist (or, for #9, mostly exist). What's missing is the lock that says "you can't silently break this."

---

## What I need from the founder

For each of the three, choose A / B / C (or modified version):

- **#6:** ___
- **#8:** ___
- **#9:** ___

Once chosen, I'll file the implementation PRs in this order:
1. #8 first (highest-value — regulatory liability)
2. #6 second (smallest, closes the cleanest gap)
3. #9 last (longest — migration work)

Each lands as a separate PR with the same shape as today's Priority 1 work (test + matching CI wiring where applicable + brain status flip to `live` in a follow-on PR after staging verification).

---

## What does NOT happen without sign-off

- No brain edits.
- No code commits beyond the structural test files themselves.
- No status flips in `architectural-invariants.yaml` — that always waits for staging verification per the three-layer doctrine.

The Priority 1 invariant tests that landed today (#5, #10, #11, #12) followed exactly this discipline: tests committed, brain status flips proposed as a separate sign-off PR after the founder confirms staging holds. Same flow applies here.
