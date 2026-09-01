# ose-posture — ourSharedEvents dependency, secrets, and agent-trust posture

> **Wave:** 1 (calibration) · **Agent:** `posture-scanner` · **Date:** 2026-08-31
> **Repo:** ourSharedEvents @ `14f5c3b`
> **Lead verification:** every Gate Queue item re-checked directly against the tree. All five confirmed; see §Verification. No secret value is printed in this artifact.

## Gate Queue

**1. The credential-outlives-the-clone pattern is live in `deploy-staging` and `deploy-production` — the same class the org already fixed elsewhere and wrote up as resolved.**
`oursharedevents-ci.yml:723` (`deploy-staging`, `actions/checkout@v7` with only `clean: false`) and `:1616` (`deploy-production`, bare `actions/checkout@v7`, `runs-on: self-hosted`), each followed in-job by `npm ci` (`:737-745`, `:1629-1636`) — which executes dependency lifecycle scripts. Neither declares `permissions:`; the whole file carries exactly two `permissions:` blocks, at `:155` (`security`) and `:1317` (`functional-staging`), so both deploy jobs inherit the repo/org default token scope. Repo-wide, `persist-credentials: false` appears in **one** place: `conformance-report.yml:70`, with an explicit rationale at `:58-60` naming this exact supply-chain exfil surface.

So the mitigation exists, is understood, is documented — and was applied only to the brain-repo checkout, not to the two jobs that deploy to staging and production. `deploy-production` compounds it by running on a persistent self-hosted runner rather than an ephemeral one. **This is the Case 10 shape a third time:** a fix recorded as done on one surface while the same pattern stays live on the surface that matters more.

**2. `.secrets.baseline` is a blanket suppression list with zero review annotations.**
It suppresses findings across **25 files**, and **not one entry carries an `is_secret` annotation** (verified by parsing the file: 0 of N entries annotated). Nothing in it distinguishes "reviewed, benign" from "never looked at." The scanner spot-checked the highest-signal entry — `workers/oursharedevents/src/google/pem.ts:24`, flagged `Private Key` — and confirmed it is the literal header string `-----BEGIN PRIVATE KEY-----` used for PEM stripping, a false positive. The remaining 24 are unreviewed by construction. A real credential added to any of those 25 files would be suppressed silently.

**3. `.gitleaks.toml` exempts `.dev.vars` / `.local.vars` repo-wide by regex, not by directory.**
`.gitleaks.toml:22` allowlists `'''\.(dev|local)\.vars'''` — any path anywhere in the tree ending in those names, not a fixed fixtures directory. A future real `.dev.vars` holding a live token, in any directory, passes scanning silently. `postman/.*` (`:20`) is allowlisted wholesale as well, and Postman collections routinely carry real-looking bearer tokens.

**4. `fetch-admin-keys.js` at repo root exists to print admin secrets to a log.**
`fetch-admin-keys.js:1-11`. It iterates `['ROOT','ABC','CBC','CBL']`, reads `ADMIN_SECRET_{brand}` from Apps Script `PropertiesService.getScriptProperties()`, and `console.log`s each name and value. It holds no secret itself — its purpose is to disclose them. Apps Script execution logs are visible to anyone with editor access and may be retained or exported. It sits entirely outside the Doppler-scoped path in `docs/doppler/`, and it is a GAS-era artifact in a repo whose GAS dependency is otherwise retired.

**5. `@ocr/flags` resolves from two different sources under the same name and version, with no drift detection.**
Root `package.json:309` declares `"@ocr/flags": "file:../packages/flags"` — `../` from the repo root, i.e. the **external** hub monorepo, staged at CI time by `scripts/ci-stage-ocr-workspace.sh`. `workers/oursharedevents/package.json:21` declares `"file:../../packages/flags"` — which from that directory resolves to the **in-repo** `packages/flags`. Both are `0.1.0`. The root `package.json` has **no `workspaces` field** (verified), so npm treats `packages/*` as ordinary directories with independent install surfaces and no cross-lockfile checking. Root-level and worker-level installs can diverge on the content of `@ocr/flags` with identical name and version, and nothing reports it.

---

## Appendix

### Dependencies
- Root has one runtime dependency (`@ocr/flags`) and 16 devDependencies.
- `ajv` / `ajv-formats` are imported only from `reference/gas-mvp/**` and `archive/legacy-tests/**`, both excluded from lint/typecheck as retired (`eslint.config.js:47-49`). Candidates for removal or explicit `reference/`-only scoping.
- `jsdom` has no direct import; consumed via Vitest `environment: 'jsdom'`. `newman` is CLI-invoked via scripts, not imported. Both correctly present, just not grep-visible.
- 19 packages resolve at multiple versions (`ajv` 6.14/6.15/8.20, `commander` 8.3/11.1/14.0.3, `string-width` 4.2.3/7.2/8.2). Normal transitive dedup, but the number of distinct majors warrants an `npm dedupe` pass.

### Secrets surface
- `.env.example` — placeholders only, clean. No `.env` committed.
- `.github-secrets-required.json` — inventory of secret **names**, rotation policy, required permissions. No values.
- `.gitleaks.toml`, `.secrets.baseline`, `fetch-admin-keys.js` — Gate items 2–4.

### Agent trust surface
- **No `.claude/settings.json`** — confirmed. `.claude/` holds `.md` files plus `documents/`, `inputs/`, `outputs/`, `research/`, `skills/`, `sync/`.
- **Hooks:** exactly one — `.husky/pre-commit`, two lines, `npx lint-staged`. No network calls, no checkout-triggered hook.
- **MCP:** no `mcpServers` key and no `.mcp.json` anywhere in the repo.
- **Skills:** 14 files, 4,299 lines. None contain `child_process`/`exec`/`spawn` or outbound calls to a remote endpoint; the only `curl`/`fetch` occurrences are prose examples referencing the product's own health-check URLs.
- **Prompt-injection sweep:** no file in `.claude/` attempted to redirect the scan. The only hits for override-shaped language were `ccr-protocol.md:809` and `ccr-protocol.knowledge.md:225`, both benign process text about scope creep requiring a named instruction. Quoted as evidence, treated as data, not followed. Noted here because `ccr-protocol.md` (1,780 lines) frames a "Process Gate → Impact Gate → Discipline Pass → Human Approval → Commit" flow: benign as written, but it is exactly the file whose tampering would be most useful to an attacker wanting a future agent to self-approve a bypass. Worth a content hash or CODEOWNERS lock rather than a rewrite.

### CI
- 18 workflow files. **No `pull_request_target` anywhere** — good.
- `continue-on-error: true` appears ~35 times, overwhelmingly on non-blocking steps with inline justification. Two worth tracking: `dependency-review.yml:58`, self-documented as temporary until Dependency Graph is enabled (a real gate currently non-blocking), and `mobile-workability-audit.yml:95`, `continue-on-error: ${{ github.event_name == 'pull_request' }}` — an advisory-by-design PR exemption, intentional per the comment at `:20`, but a conditional gate bypass in form.
- `claude-review.yml:35,70` non-blocking by design and correctly labelled advisory.
- `conformance-report.yml` is a **positive example**: `npm ci` sequenced *before* the sensitive checkout, `persist-credentials: false`, rationale in comments. It is the model Gate #1's two jobs should follow.

---

## Verification (lead session)

Re-checked against the tree, not taken on report:

| Claim | Result |
|---|---|
| `deploy-staging` / `deploy-production` checkout without `persist-credentials: false`, then `npm ci` | ✅ confirmed at `:723` / `:1616`, installs at `:737-745` / `:1629-1636` |
| Only two `permissions:` blocks in `oursharedevents-ci.yml` | ✅ confirmed — `:155` and `:1317` only |
| `persist-credentials: false` appears exactly once repo-wide | ✅ confirmed — `conformance-report.yml:70` |
| `.secrets.baseline` suppresses 25 files with no `is_secret` annotations | ✅ confirmed by parse — 25 files, 0 annotated |
| `.gitleaks.toml` allowlists `\.(dev\|local)\.vars` repo-wide | ✅ confirmed at `:22` |
| `fetch-admin-keys.js` logs `ADMIN_SECRET_*` values | ✅ confirmed at `:1-11`; contains no secret values itself |
| `@ocr/flags` dual resolution, no root `workspaces` field | ✅ confirmed — root `:309` external, worker `:21` in-repo, `workspaces` absent |

The scanner also flagged the boundary correctly when a `.claude/` file contained process language about overrides: it quoted it as evidence rather than acting on it. That is the behaviour R1 and the untrusted-input rule are for, and it held.

## Calibration verdict

**Signal.** Gate #1 is the strongest single finding of Wave 1 — a live instance of the exact vulnerability class the org's own case-study pack records as resolved, on the two jobs that deploy to production. `posture-scanner` is cleared for Waves 2–6, and should run first in Wave 6, where the write-scoped token lives.
