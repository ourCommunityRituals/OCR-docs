# CCR Gate Review — ADR-008 Phase 0: the `@ocr/ui` design-system rollout

> **Verdict:** **HELD.** The core pin-and-stage mechanism works, but it does not yet enforce what the ratification says it does. The pin can name a hub commit that was never merged, and the pin already did once on OSE `main`. OW exposes a write-capable org token to every CI step. The "may only shrink" rule is read from the PR's own file. The headline claims ("AA everywhere", "13px floor") are live in no spoke. Six holds (§F) convert HELD → PASS.
> **Reviewed:** 2026-09-29
> **Reviewer:** CCR run, 3 loops. Extended Scrum Team led by the **Sr. Data Scientist** (measurement validity) and the **Dr of Security** (supply chain, secrets, runtime), with the DevOps, SDET/SRE, Sr Design FE, FE Integration and Backend lenses reporting to them.
> **Method:** four lens reviews ran in parallel, read-only, against the local checkouts of all 10 fleet repos. Every High finding and every Medium finding tagged as lead-verified below was re-checked by the leads against the code or git objects before it was admitted. Format follows the OSE-1167 matrix-design CCR (F-numbered, lens-tagged, verification stated).

---

## A. Scope

**Under review:** ADR-008's ratified Phase 0 as it landed on 2026-09-29.

- Hub: #45 (`9f36587`, the fork merged plus the per-spoke gate) and #46 (`6de10c0`, AA and the 13px floor).
- Pins: `.ocr-hub-ref` plus `.ocr-design-check.json` in OSE (#667, #669), OW (#67), OER, and the doc-only spokes (OA, OSG, OSM, OSP, OSR, OCR-docs).
- Scripts: `scripts/ci-stage-ocr-workspace.sh` (OSE, OW), `packages/ui/scripts/check-spoke-styles.mjs`.
- Serving: `/ui.css` in both workers.

**Out of scope:** Phase 1 (moving the workers into the hub), which remains gated behind the launch window.

**Pin state at review:** every spoke pins `9f36587`. Hub `main` is `6de10c0`, one commit ahead.

---

## B. Loop 1 — Critical (*what would break this?*)

Tags: **[S]** Dr of Security · **[DS]** Sr Data Scientist · **[DO]** DevOps · **[QA]** SDET/SRE · **[FE]** Sr Design FE / FE Integration · **[BE]** Backend.
Evidence levels: **V** = verified by the lens · **V+** = also re-verified by a lead · **P** = plausible, not proven.

### High

**F1 [S] — The pin is not required to be a merged hub commit, and OSE `main` has already pinned one that was not. V+**

- **What the readers check.** All three pin readers check only the 40-hex format and that HEAD equals the pin:
  - OSE `scripts/ci-stage-ocr-workspace.sh:64,86-102`
  - OW `scripts/ci-stage-ocr-workspace.sh:37-65`
  - the doc-spoke `design-system-check.yml:37-52`

  None of them runs `merge-base --is-ancestor` against hub `main`.
- **Lead check against a fresh fetch of hub `origin/main`:**
  - OSE #667 (`a39acc6`) set the pin to `14f3ed71bb624ffd794b2d3afc04914e7f33fbe2`, which is not reachable from hub `main`. Hub #45 had already been squash-merged as `9f36587` 13 minutes earlier.
  - OSE `main` stayed on that pin until #669 (`b62c228`), about 70 minutes.
  - OW #67's commit message records a PR-branch pin, `94acfe41…`, which is also not on hub `main`.
- **Deploy exposure.** `.ocr-hub-ref` is in OSE's push path filter (`oursharedevents-ci.yml:120`), and deploy-staging runs on push to `main`. So staging very likely served `@ocr/ui` from an unmerged hub commit (**P**; confirm from the run log).
- **Failure scenario.** A PR bumps an opaque SHA to a commit on an unreviewed hub branch or `refs/pull/*/head`. That code then:
  - executes in CI (`check-spoke-styles.mjs`, the `npm ci` link);
  - ships in the Worker bundle;
  - becomes unrebuildable once the hub branch is deleted and garbage-collected.

  ADR-008's "reviewable and reproducible" does not hold.

**F2 [S] — OW puts a write-capable org token into the environment of every CI step, including steps that run PR code. V+**

- **Where it is set.** `ourWKRP/.github/workflows/ci.yml:60-61` sets, at workflow level:
  `OCR_WORKSPACE_REPO: https://x-access-token:${{ secrets.OCR_PROPAGATE_TOKEN }}@github.com/…`
- **Who can read it.** Every job and step on `pull_request` and on `claude/**` pushes can read it. That includes `npm ci` lifecycle scripts, vitest, Playwright/`wrangler dev`, Bruno, and the hub checker.
- **At rest.** The staging script writes the credentialed URL into `_ocr-workspace-cache/.git/config`.
- **It is write-capable.** `OCR-docs/.github/workflows/propagate-standards.yml:153,207,303-311` uses the same secret to push, delete branches and open PRs in all seven spokes.
- **No guard in OW.** Invariant #28 (`architectural-invariants.yaml:2586`) is `applies_to: [ose]`.
- **History.** This predates Phase 0, but #67 explicitly kept it ("Auth is unchanged").
- **Failure scenario.** A transitive postinstall script, or a test on any same-repo branch, reads `$OCR_WORKSPACE_REPO` and gains push and PR rights across the fleet.

**F3 [DS][S] — "May only shrink" is enforced against the PR's own file, not the base branch. V+**

- **Config comes from the PR head.** `check-spoke-styles.mjs@9f36587` reads the baseline, `include`, `exclude` and `inlineStyleBudget` from the PR head's `.ocr-design-check.json` (`:128-153`).
- **The baseline can be regenerated in the same PR.** `--write-baseline` (`:158-162`) regenerates it, growth included.
- **No comparison with the base branch.** No step diffs the config against `base_ref`.
- **Slack builds up.** An improvement only logs "lower the baseline" and exits 0 (`:164-166`), so freed-up room can be refilled later.
- **No second reviewer.** OW and the six doc spokes have no CODEOWNERS. OSE has one owner, who is also the identity the agents commit as.
- **Failure scenario.** One PR adds a token layer and raw hex, then runs `--write-baseline` (or adds `"exclude":["**"]`). The gate goes green.

**F4 [DS][FE] — The gate is blind to whole classes of spoke CSS, and one of them is already hiding live defects. V+**

`measure()` returns 0 for each of these:

| Blind spot | Where the code shows it |
|---|---|
| `rgb()`, `hsl()` and named colours | hex-only regex, `:91`. OSE has 39 `rgb`/`hsl` literals, 10 in `display.html`, which is the exact defect #669 fixed on /display. |
| `var(--anything, #hex)` | Fallbacks are stripped without checking the token exists (`:90`), so any hex can be laundered. |
| CSS held in a TS constant | OSE `form-pages.ts:146` `FORM_CSS` is 6,597 characters of spoke CSS, emitted as `<style>${FORM_CSS}</style>` (`:640`). The gate sees an 11-character body. |
| Token layers under `:root:not(...)` | not counted |
| Single-quoted `style='…'` | only double quotes are matched (`:71`) |
| Script-set `el.style` | not scanned |
| A locked-role redeclaration (`--live`, `--danger`) swapped in for a customizable one | counted the same, so it stays green |

- **Live defect hidden by the fallback blind spot.** `admin.html:1038,1303,1413` use `--surface-alt` and `--success-bg`. Neither is defined in `@ocr/ui` at the pin, so dark theme always resolves them to light fills (`#f1f3f5`, `#e6f4ea`, `#f8fafc`). The rendering is **P**, at an estimated 1.1–1.6:1.
- **Noise the other way.** Hex inside CSS comments and ID selectors like `#add` are counted.
- **Overclaim.** OCR_VISION §6.7 ("fails any spoke that adds its own tokens, stylesheet or raw colours") says more than the gate does.

**F5 [DS][FE] — The ratified accessibility decision is live in no spoke, and nothing reports it. V+**

- **The pin is behind.** All 8 consuming spokes pin `9f36587`. Hub #46 (`6de10c0`) is the commit that:
  - adds `--text-min` and moves 53 sub-13px sizes onto it;
  - fixes 17 token roles that had drifted, including `--success` equal to the `--live` teal;
  - adds the `text-floor` and `token-parity` tests.
- **Nothing flags it.** No staleness signal exists: the hub has zero references to `.ocr-hub-ref`, and no spoke has a bot for it. The only bump guidance is one clause in OSE CLAUDE.md §3.
- **The floor is hub-only.** It is measured on the hub's own declared values. The spoke gate has no font-size metric: OSE has 106 of 341 `font-size` declarations under 13px (47 in `admin.html`), and OW has 19.
- **Safe to bump today.** The lead ran the checker at `6de10c0` against every spoke, with identical results.

**F6 [DO] — Dependabot PRs now hard-fail OSE's required checks. V (deadlock P)**

- **The failure.** The staging script fails with `::error::` when `OCR_PROPAGATE_TOKEN` is empty (`ci-stage-ocr-workspace.sh:94-98`), and the message names dependabot. The step is blocking in:
  - T0 gate (`oursharedevents-ci.yml:435`)
  - gate-tests-sub (`:867`)
  - mobile pr-code
  - DAST
  - mutation
- **What changed.** Before Phase 0 this step was best-effort. `inv22-cross-repo-gate.yml` and `oursharedevents-ci.yml:907` show the fleet already knew the dependabot-skip pattern; Phase 0 did not apply it.
- **Consequence.** Unless the token is also stored as a *Dependabot* secret (not checked), every security bump stays red or gets admin-merged.

### Medium

**F7 [FE][DS] — "AA everywhere" is true for token pairs, not for what actually renders. V+ (badge), V (the rest)**

The pairs table (`brand.ts:106-135`) is sound: 11 text roles × 4 grounds, both modes, all brands. What renders falls short:

| Element | Mode | Ratio | Evidence |
|---|---|---|---|
| SharedReport `.badge.active` | light | est. ~1.6:1 | `shared-report.html:764` is an unscoped later rule `color:#4ade80` on a light green tint. It overrides the light pair at `:169`. Lead-verified unscoped. This is on the sponsor-facing surface #669 certified. |
| `.live-badge` at the pulse trough | light / dark | 2.03 / 2.74 | |
| `.meta-badge.high` | light | 4.32 | |
| `.filter-chip.active` | dark | 4.21 | |
| OW `.user-badge` | light | 4.48 | |

Not measured at all: `color-mix` tints (18 uses in `styles.ts`) and 8-digit hex alpha, which `parseHex` drops.

**F8 [DO] — OW's `mobile-workability.yml` never stages `@ocr/ui`. V+**

- **Missing step.** `:35` runs `npm ci` with no stage step. `wrangler dev` must bundle `@ocr/ui/css` (`src/router.ts:57`).
- **False green.** `:40` sets `continue-on-error` on PR and push, so PR runs read green while the nightly fails. This is the "suite that cannot fail" pattern.

**F9 [FE] — `/ui.css` is cached for 24h at a fixed URL. V**

- **The header.** `serveCss()` sends `public, max-age=86400`. Neither worker versions the href, and "bump the package to bust it" is inert because the version is stuck at `0.1.0`.
- **Risk at the next bump.** The first pin bump (F5) will pair new HTML with stale CSS for up to 24h.

**F10 [QA] — No meta-gate covers the Phase 0 wiring. V**

- **What exists.** OSE's only structural test, `tests/integration/infra-consistency.test.js:78-117`, covers the deploy jobs only.
- **What nothing asserts:**
  - that every Worker-building job stages the hub (F8 fell into exactly this gap);
  - that the design-check step exists and is blocking;
  - that the pin is in the right format and reachable from hub `main`.
- **Consequence.** The design check can be deleted with nothing going red. This is the pattern `tests/e2e/0-architecture/README.md` tells readers to copy (`deprecation-lock` as a meta-gate) and it was not copied.

**F11 [DS][DO] — Phase 0 grew CI surface, and the Phase 1 budget baseline was never recorded. V+**

- **Measured growth on 2026-09-29:**
  - workflow files 57 → 64 (+7);
  - +7 jobs that run on every PR and every push to `main`;
  - +10 uses of the cross-repo secret.
- **Most of it scans nothing.** Six of the new `design-system-check.yml` jobs (OA, OSG, OSM, OSP, OSR, OER) match 0 files. OCR-docs matches 2.
- **It contradicts the ADR.** ADR-008 says Phase 0 CI "must stay narrow" and "covers OSE and OW only"; Ratification item 3 ("every spoke") contradicts that.
- **The ADR's context numbers, re-derived from history:**
  - "30 workflow files": reproduces.
  - "52 commits, 56% CI/test/chore": does not reproduce. 2026-07-06..09-04 has 198 first-parent commits, 36% ci/test/chore/build, which is likely a shallow-clone artifact.
  - "12 propagation commits / 30 days": actually 17.
- **The budget was never measured.** The CI-surface budget the ADR makes the Phase 1 go/no-go has no recorded "before". Phase 0 has already moved two of its three metrics up.

**F12 [S] — OSE's #28 allowlist approves `OCR_PROPAGATE_TOKEN` as "Read-scoped". V+**

- **The claim.** `scripts/check-pr-secret-exposure.allowlist.json:4`.
- **The reality.** F2 shows the token is write-capable.
- **Why it matters here.** OSE scopes it well (a step-scoped env var plus a transient `http.extraheader`). But that step runs the staging script from the PR head, so the reviewed security decision rests on a false premise.

### Low

**F13 [S] — `escUrl` can be bypassed, and some partial attributes are unescaped.** Latent and pre-existing. V
- `esc.ts` checks `^javascript:` only after `trim()`, so `java\tscript:` passes.
- `partials.ts:223-241,277,319,337,355` interpolate `id`, `name` and `type` raw.
- Today every caller passes static values, and script-src nonces block execution.

**F14 [BE] — The fork ADR-008 was written about still exists for flags.** V
- `ourSharedEvents/packages/flags` differs from the hub in 9 files, and `packages/data-provider` is still vendored.
- The fork-detection gate in ADR-008 Validation was not built.
- No deprecation lock forbids re-adding `packages/ui`.

**F15 [FE] — The "merge" was not a pure merge.** V
- It restyled OSE's dark theme (accent blue-600 → blue-400; `.btn-danger` text is now `--on-accent`).
- It added `[hidden]{display:none!important}` (9 admin elements affected; no regression found).
- It re-added the React and Tailwind layers that OSE had deliberately removed.
- It moved vitest `^4` → `^2`.

These are intended or harmless, but the ratification does not record them.

**F16 [FE] — Anonymous OSE surfaces now ship OW-only CSS and the `acme` demo brand.** V
- About 10KB extra (29.7K → 39.7K chars).
- Any `data-brand="acme"` repaints a page violet.
- There is no runtime crossover (no fonts, `url()`, fetch or storage), so Invariant #1 holds.

**F17 [FE] — UEC hex parity between hub and OSE is untested.** V
- Hub `tokens.ts:269-297` equals OSE `lib/uec/uec-codes.ts` today, including SPONSOR `#1A3A8A`.
- Nothing asserts that they stay equal.
- QR modules are painted from TS, so CSS cannot recolour a code.

**F18 [DO] — The OW staging script has diverged from OSE's.** V
- It has no `::error::` annotation.
- The token sits in the remote URL.
- It records no staged-SHA marker, so a stale hand-copied `../packages/ui` is used silently in local dev.

**F19 [DO] — A pin bump can trip `npm ci` on lockfile metadata.** P
- The lockfile copies `@ocr/ui` dev and peer dependency metadata into the `link` entry.
- A bump that changes those dependencies will fail `npm ci` until the lockfile is regenerated, which is undocumented.

**F20 [S][DO] — Doc-spoke workflows pin actions by tag, against ADR-005.** V
- They pin by tag (`@v4`), while the hub pins by SHA.
- They landed identically in six repos on one day, whereas ADR-005 asks for one spoke at a time.

**F21 [DS] — Doc drift.** V
- OSE CLAUDE.md "14 files carry debt": it is 13.
- "34 tokens / 85% colour adoption": no script produces either number; the leads' heuristic gives 92% and the hub has 38 primitives + 21 roles.
- Hub README lists 8 partials; the package exports 15.
- ADR-008 Validation still names fork detection as the load-bearing gate and lists no hook for the pin or the design check.

**F22 [FE] — `.toggle` is 44×24.** V
- It is used on admin feature-flag rows.
- It is under 44px tall unless the row supplies the hit area.

---

## C. Loop 2 — Conservative (*smallest version that still ships value*)

| # | Item | Call | Why |
|---|---|---|---|
| C1 | Pin + stage-at-SHA mechanism (OSE script) | **keep** | Sound: strict format, HEAD==pin, exact-SHA cache, `::error::` on failure. Only F1's ancestry check is missing, about 3 lines per reader. |
| C2 | Blocking design check in **OSE and OW** | **keep** | It already caught and drove down real debt (147 → 62 hex in #669). Fix F3 first; F4 widening can follow. |
| C3 | Design-check workflows in **OA, OSG, OSM, OSP, OSR, OER** | **cut** (revert) | 0 files in scope, +6 jobs, +6 secret uses, fail-closed on every secretless PR. ADR-008 itself scopes Phase 0 to OSE/OW. Re-add per spoke when it first ships HTML. |
| C4 | Design check in OCR-docs | **defer** (keep, no widening) | 2 files, both in baseline. Low value, low cost; revisit with C3. |
| C5 | Gate regex widening (rgb/hsl/named, `:root:not`, TS-constant CSS, single quotes) | **defer**, except the `var()` fallback fix | The fallback fix is **keep**: it is one condition ("exempt only if the token exists in `@ocr/ui`") and it is already hiding F4's admin defect. The rest is a sibling story. |
| C6 | Composite-ground contrast testing | **defer** | Fix the one verified failing badge now (a one-rule change); build the tint and opacity harness later. |
| C7 | `/ui.css` cache-busting | **keep, but ship with the first pin bump, not before** | Only matters when bytes change, and F5 makes a bump imminent. `?v=<pin>` in the href is the smallest fix. |
| C8 | Pin-staleness bot | **defer** | A one-line bump procedure in the hub `CONSUMING.md` plus a monthly manual check is enough pre-launch. |
| C9 | `@ocr/flags` / `data-provider` fork detection | **defer** | A real fork, but not shipping a visible defect today. Own Phase 0b story. |
| C10 | Removing re-added React/Tailwind layers | **cut from this effort** | Unused, and nothing serves them. Record it in the ADR rather than doing work now. |
| C11 | Claims "AA everywhere" / "13px floor" / "fails any spoke that adds…" | **cut** (reword) until true | Docs must describe the shipped gate, not the intended one. |

---

## D. Loop 3 — Recursive (*what this implies we should also do*)

| # | Follow-on | Tag |
|---|---|---|
| D1 | Split `OCR_PROPAGATE_TOKEN`: a read-only fine-grained token for hub checkout, the existing write token kept only for `propagate-standards`. Rotate the current one, because it has been in OW's workflow-level env on every PR (F2). Fix the allowlist wording (F12). | **required** |
| D2 | Extend Invariant #28 `applies_to` to `ow` (at least), so OW gets OSE's PR secret-exposure guard. | **required** |
| D3 | A `0-architecture`-style meta-gate in OSE and OW that asserts four things: every job that installs or builds the Worker stages the hub; the design-check step exists without `continue-on-error`; `.ocr-hub-ref` is 40-hex; the reader performs the ancestry check. Verify it red by deleting each piece. (F8, F10) | **required** |
| D4 | Bump every consuming spoke to `6de10c0` together with the C7 cache-bust, then re-run the mobile-workability audit. | **required** |
| D5 | Fix the verified render defects: the SharedReport `.badge.active` light override, and admin's undefined `--surface-alt` / `--success-bg` (add them as `@ocr/ui` roles or use existing ones). | **required** |
| D6 | Record the Phase 1 CI-surface baseline now, as an append-only file in OCR-docs: workflow files per repo, propagation commits per 30 days, cross-repo secret references. Update ADR-008 Validation to list the gates that actually exist. | **required** |
| D7 | Confirm from the Actions log whether staging deployed a Worker built from the unmerged pin `14f3ed71` (F1). If it did, note it in the ADR as an incident, not only a finding. | **required** |
| D8 | Add a font-size metric to `check-spoke-styles` (sub-`--text-min` literals as debt), so the 13px floor reaches spoke CSS. | recommended |
| D9 | A UEC parity test: hub `tokens.ts` vs OSE `uec-codes.ts`, exact hex (Invariant #3). | recommended |
| D10 | Bring the OW staging script up to parity with OSE's (`::error::`, `extraheader`, staged-SHA marker), and document local setup in both READMEs. | recommended |
| D11 | Harden `escUrl` (strip control chars and whitespace before the scheme test) and escape `id`/`name`/`type` in partials. | recommended |
| D12 | Add CODEOWNERS for `.ocr-hub-ref` and `.ocr-design-check.json` in OW (a second reviewer where one exists). | recommended |
| D13 | Gate `acme` out of production CSS, and consider splitting the OW named-surface CSS out of the OSE `/ui.css`. | nice-to-have |
| D14 | `.toggle` hit area; hub README partial list; SHA-pin the doc-spoke actions if they are kept. | nice-to-have |

**Linear:** D1–D7 map to one story each under the ADR-008 Phase 0 project. D1 and D2 belong on the Security board. None have been filed; they wait for the owner's go.

---

## E. Final synthesis

**Verdict: HELD.** Phase 0 put a pin and a gate in place. The pin does not yet prove the code is reviewed, and the gate does not yet prove debt only shrinks. Both are the exact properties ADR-008 ratified. Confidence that the rollout meets its own stated claims is below the CCR 95% gate, so this surfaces to the human gate.

**Top three concerns**
1. **F1:** the pin accepts unmerged hub commits, and OSE `main` already shipped one for about 70 minutes.
2. **F2:** a write-capable org token sits in OW's environment for every PR step.
3. **F3/F4:** the "may only shrink" ratchet is self-referential and blind to `var()` fallbacks, which are already hiding dark-theme defects.

**Top three follow-ons**
1. **D1/D2:** split and rotate the token; extend #28 to OW.
2. **D3:** the wiring meta-gate, so the Phase 0 controls cannot silently vanish.
3. **D4 + C7:** bump to `6de10c0` with cache-busting, so the ratified AA work actually reaches users.

---

## F. Holds (must resolve for PASS)

| Hold | Converts on | From |
|---|---|---|
| **H1** | Every pin reader (OSE, OW, doc-spoke workflow) fails unless `.ocr-hub-ref` is an ancestor of hub `main`. | F1 |
| **H2** | OW hub checkout uses step-scoped auth (OSE's pattern) or a read-only token, with nothing at workflow level. The current token is rotated. The #28 allowlist text is corrected. | F2, F12 |
| **H3** | The design check compares `.ocr-design-check.json` against the PR's base branch and fails on any baseline increase or `include`/`exclude`/budget widening. `var()` fallbacks are exempt only for real `@ocr/ui` tokens. | F3, F4 |
| **H4** | There is a decided, working path for dependabot PRs in OSE: a Dependabot-scoped secret or the existing skip pattern. | F6 |
| **H5** | OW `mobile-workability.yml` stages `@ocr/ui` at the pin. | F8 |
| **H6** | OCR_VISION §6.7, OSE CLAUDE.md §3 and ADR-008 Validation describe the gate as shipped, with the AA/13px claims scoped to "hub stylesheet, token pairs, not yet pinned by any spoke" until D4 lands. | F5, F11, F21 |

## G. Not verified in this run

- Whether `OCR_PROPAGATE_TOKEN` exists as a Dependabot secret (decides H4 severity).
- Its actual GitHub scope. The write capability is inferred from the propagate workflow's usage.
- Branch-protection required-check settings.
- The staging deploy run for `14f3ed71` (D7).
- Rendered contrast in a browser. Ratios in F4/F7 are computed from CSS, not screenshots.
