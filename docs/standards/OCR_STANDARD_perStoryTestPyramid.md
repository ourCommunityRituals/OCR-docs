# OCR_STANDARD — Per-Story Test Pyramid

**Status:** Active — applies to every story in every product repo
**Date:** 2026-05-15
**Owner:** mzdan
**Triggered by:** Founder reframe (2026-05-15) — _"For every story, write Postman and Playwright tests"_

---

## The rule

**Every story-scope PR ships tests at all three pyramid layers before it moves to QA:**

1. **Unit / Worker-binding** — vitest (`tests/*.spec.ts`)
2. **API contract** — Postman/Newman (`postman/collections/*.json`)
3. **UI / browser flow** — Playwright (`tests/playwright/*.spec.ts`)

A PR that ships code without all three layers is not "code review ready." It's "developer slop being thrown over the wall to the tester."

---

## Why the standard exists

The static refinement audit (2026-05-15) surfaced 50 customer-flow defects across 6 surfaces in OSE. Every defect was something a human user would hit on first interaction — and every one was code that had passed unit tests, merged to main, and reached "feature complete" status without a single click-through.

Cause: vitest catches code-shape errors but doesn't catch:

- Routes that return JSON when the user expects HTML
- DOM that renders correctly in isolation but breaks in a real browser
- Network responses that pass schema validation but include dev jargon
- A11y violations that only surface in screen readers
- Mobile layouts that look fine at 1080p and break at 375px

Postman tests catch the network-contract layer; Playwright tests catch the browser-rendering layer. Together with vitest, all three close the customer-experience loop **before** a human ever has to drive the flow manually.

---

## What "per-story" means

| Layer | Per story you ship | Test file lives at |
|---|---|---|
| **Unit / Worker** | At least one `*.spec.ts` whose name names the story or refinement ID | `<repo>/workers/<svc>/tests/<feature>.spec.ts` |
| **API contract** | At least one entry in the relevant Postman collection naming the story or refinement ID | `<repo>/postman/collections/<surface>.json` |
| **UI / browser** | At least one `*.spec.ts` in the Playwright tree naming the story or refinement ID | `<repo>/tests/playwright/<surface>.spec.ts` |

**"At least one"** — not "every assertion duplicated three times." Different layers test different things:

- Unit tests: function behavior, edge cases, internal invariants
- Postman: response shape, headers, status codes, content negotiation
- Playwright: DOM elements present, click flows, mobile viewports, real-browser behavior

If a story changes both an API and a UI surface, it ships tests on BOTH surfaces' collections (Postman) AND files (Playwright).

---

## Test naming — the unified format

**A reader 6 months from now must be able to read a test name once and know what it does.** Therefore Postman items, Playwright tests, AND vitest tests use one format:

```
<STORY-ID> | <HTTP method + path or surface> | <given / condition> → <then / outcome>
```

Three pipe-delimited segments + an arrow. **Same string in every layer.** The matching name across layers is a feature — it lets you cross-reference one scenario tested from multiple perspectives.

### Anatomy

| Segment | Answers | Examples |
|---------|---------|----------|
| **`<STORY-ID>`** | Which story or refinement | `R-001`, `OSE-272`, `OSE-15` |
| **`<HTTP method + path>`** | What surface | `GET /admin`, `POST /api/v2/events/shared-reports/batch`, `GET /forms/:eventId` |
| **`<given / condition>`** | What the user/caller is doing | `unauthenticated browser`, `bar owner signed in via CF Access`, `mobile 375px viewport`, `payload exceeds 16KB` |
| **`<then / outcome>`** | What should happen | `401 HTML sign-in page`, `200 SharedReport JSON`, `400 friendly error copy`, `card fits within viewport width` |

### Rules

- **Present tense for both segments**: "unauthenticated browser → 401 HTML sign-in page" (not "tries to access" / "should return")
- **No abbreviations that don't tell the story**: write "unauthenticated" not "unauth"; write "authenticated" not "authed"
- **Plain English on both sides of the arrow**: not raw codes (`UNAUTH`, `INVALID_BODY`) and not implementation detail (`returns null`, `throws`)
- **One scenario per test**: if you find yourself writing "and" twice on either side of the arrow, split into separate tests
- **No PW-NN / numeric suffixes**: ordering is irrelevant; the name itself disambiguates. Two tests can never have the same name; if they would, your scenario or condition is wrong

### Reference implementation (R-001 in OSE)

The exact same 11 test names appear in Postman items and Playwright tests for R-001 — only the runner differs. A reviewer comparing Newman output to Playwright output can match each scenario line-by-line.

| Postman item (Newman output) | Playwright test (Playwright output) |
|---|---|
| `R-001 \| GET /admin \| unauthenticated browser → 401 HTML sign-in page` | `R-001 \| GET /admin \| unauthenticated browser → 401 HTML sign-in page` |
| `R-001 \| GET /admin \| unauthenticated API client → 401 JSON error` | _(not applicable in Playwright — that's a curl test)_ |
| `R-001 \| GET /manage \| unauthenticated browser → 401 HTML sign-in page (alias)` | `R-001 \| GET /manage \| unauthenticated browser → 401 HTML sign-in page (alias)` |
| `R-001 \| POST /api/v2/admin/events \| unauthenticated browser → 401 JSON (no HTML leak)` | _(not applicable — that's a curl test)_ |
| _(vitest already tests internal)_ | `R-001 \| GET /admin \| unauthenticated browser → heading + lede + CTAs render` |
| _(vitest already tests internal)_ | `R-001 \| GET /admin \| unauthenticated browser → brand matches landing (logo + nav)` |
| _(vitest already tests internal)_ | `R-001 \| GET /admin \| unauthenticated browser → a11y skip-link + semantic main + focus` |
| _(vitest already tests internal)_ | `R-001 \| GET /admin \| unauthenticated browser → robots noindex meta present` |
| _(curl can't test viewport)_ | `R-001 \| GET /admin \| mobile 375px viewport → card fits within viewport width` |
| _(curl can't test viewport)_ | `R-001 \| GET /admin \| unauthenticated browser → no admin dashboard content leaked` |

When a scenario is testable in BOTH Postman and Playwright (response shape, status, headers), use the **exact same name string**. When it's only testable in one (visual layout → Playwright only; raw API contract from a non-browser → Postman only), still use the format so the output stays scannable.

### Vitest variant

Vitest tests internal Worker behavior — different audience (devs debugging unit tests) but the same naming for consistency. The describe block names the story; inner tests use the unified format:

```typescript
describe('R-001 admin front-door', () => {
  test('R-001 | GET /admin | unauthenticated browser → 401 HTML sign-in page', async () => {
    // ...
  });
});
```

### What about non-HTTP tests?

For tests that don't have an HTTP method + path (a pure function, a DB helper, a UI component in isolation), substitute the surface for the method+path slot:

- `R-NNN | mintSignedLinkToken() | valid event ID + secret → returns HMAC token`
- `R-NNN | escapeHtml() | string with < > & quotes → returns entity-encoded string`
- `R-NNN | <EventCard> component | event in pre_event phase → renders RSVP CTA`

---

## When the three layers are NOT all required

The rule is "every **customer-facing** story." Carve-outs:

| Story type | Required layers | Why |
|---|---|---|
| Customer-facing HTTP endpoint or page | All 3 | The thing customers actually use |
| Internal cron / scheduled job | Vitest only | Not user-facing; Postman/Playwright provide no value |
| Migration-only PR | Vitest only (schema drift gate) | Not user-facing |
| Docs-only PR (this file, ADRs, READMEs) | None | No code to test |
| Brain contract YAML change | Brain conformance check (existing CI) | Per-repo CI handles this |
| CI / tooling-only PR | None (or CI dry-run) | Self-evident |

When in doubt, ask: **"could a customer see this change?"** If yes, all three layers.

---

## What the audit / refinement workflow looks like in practice

For every refinement story (R-NNN in `REFINEMENT-BACKLOG-YYYY-MM-DD.md`):

1. **Branch** off `main`: `<repo>/r-NNN-<short-description>`
2. **Fix the code** — surgical, single concern, no scope creep
3. **Vitest spec** — `tests/r-NNN-<feature>.spec.ts` (or extend an existing spec with a `describe('R-NNN ...')` block)
4. **Postman update** — add named items to the relevant collection JSON, using the unified naming format (see § Test naming)
5. **Playwright spec** — `tests/playwright/<feature>.spec.ts` with the unified naming format — same string as the matching Postman item
6. **Run all three locally** before pushing:
   - `npx vitest run tests/r-NNN-*.spec.ts` → pass
   - `newman run postman/collections/<surface>.json -e postman/environments/staging.json` → pass (or doc'd skip)
   - `npx playwright test tests/playwright/<feature>.spec.ts --list` → enumerated; `--reporter=line` against staging → pass when deployed
7. **PR** title: `fix(R-NNN): <short description>` or `feat(STORY-NNN): <short description>`
8. **PR description** lists the three test artifacts explicitly under a `## Tests` heading

CI runs vitest. Newman runs on staging deploy. Playwright runs on staging post-deploy or in the smoke pipeline. Each layer fails independently — no single layer can mask another's failure.

---

## Anti-patterns

- ❌ **"The unit test covers it"** — unit tests don't catch content-negotiation, real-browser rendering, or DOM-level a11y. They MUST be paired with Postman + Playwright for customer-facing changes.
- ❌ **"It's a small fix, skipping Postman"** — small fixes are exactly when regressions sneak in. Postman test takes 5 min to add; saves hours of post-deploy "why is staging broken" investigation.
- ❌ **"Playwright is flaky, I'll skip it"** — Playwright tests against a stable surface are not flaky. If you find one is flaky, that's a defect in the surface or the test; fix the cause, don't skip.
- ❌ **Postman/Playwright tests that exercise mocks instead of the real surface** — these layers exist to catch what unit tests can't. If you mock, you're back to unit testing.
- ❌ **One Playwright test per refinement that just does `goto + expect(200)`** — that's a smoke check, not a flow test. The pyramid requires the test to exercise the actual user interaction.

---

## Examples in repo

Reference implementations of the standard, post-R-001 ship (2026-05-15):

- **Vitest:** `ourSharedEvents/workers/oursharedevents/tests/admin-signin-page.spec.ts` (7 cases)
- **Postman:** `ourSharedEvents/postman/collections/ose-pages.json` — search `"R-001 |"` for the 4 new entries
- **Playwright:** `ourSharedEvents/tests/playwright/admin-signin-page.spec.ts` (9 cases)

Each layer tests something the other two layers cannot. Use these as the template for R-002 onward.

---

## Pre-existing infrastructure (no new tools required)

| Tool | Where | Used by |
|---|---|---|
| **vitest** | `<repo>/workers/<svc>/vitest.config.mts` | All OSE worker tests |
| **Newman** | `<repo>/newman.config.json`, `<repo>/postman/` | Existing OSE Postman collections (ose-api.json, ose-pages.json, ose-api-sharedreport.json) |
| **Playwright** | `<repo>/playwright.*.config.ts`, `<repo>/tests/playwright/` + `<repo>/tests/e2e/` | Existing OSE landing-page Playwright |

This standard does NOT require new tooling. It requires writing tests in the existing layers.

---

## How this lives long-term

- **Standard is fleet-wide** — every OCR product repo follows this. Sibling repos (ourWKRP, ourAirwaves, etc.) inherit the pattern when they engage customer surfaces.
- **CI enforcement** — a future story may add a CI check that fails a customer-facing PR missing any of the three layers (detected via PR diff: did the code change a `handle*Page` / route / form? if yes, are Postman + Playwright deltas in the PR?). Until that check exists, this is **review discipline** — the reviewer's job is to refuse a customer-facing PR that ships only vitest tests.
- **Routing** — per `OPERATING_SYSTEM.md §3`, this standard lives at `OCR-docs/docs/standards/`. ADRs reference it; per-repo CLAUDE.md should pin it.

---

## Related artifacts

- `OPERATING_SYSTEM.md §3` — routing matrix (where each test layer lives per repo)
- `OCR_STANDARD_testNaming.md` — naming convention (file + test names)
- `OCR_STANDARD_d1Migration.md` — migration-test exemption rule
- `feedback_security_first_gate.md` — pyramid principle (security gates BEFORE lint)
- `REFINEMENT-BACKLOG-YYYY-MM-DD.md` in each repo's `docs/qa/` — the per-story IDs this standard references

---

_If you're shipping a customer-facing change and you only have vitest tests, you're not done. The standard exists because every defect found in the 2026-05-15 audit was code that had vitest coverage and still broke for users. Vitest is necessary; it is not sufficient._
