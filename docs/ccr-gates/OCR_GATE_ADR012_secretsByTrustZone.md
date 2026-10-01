# CCR Gate Review — ADR-012: secrets by trust zone (credential isolation)

> **Verdict:** **HELD (in progress: Loop 3 of 5 complete).** The design is right, and every lens agreed on that. It is not launch-ready: a write-capable token is still live, production admin may accept a static header, production data keys have been reachable through a deploy-capable token since production was first deployed on 2026-09-22 (N2), so they count as exposed, and the tests are static only.
> **Human gate (CCR v3 §2.3):** each loop has scored below 95%, and Loop 3 scored lower than Loop 2, so the protocol's human gate is open. It was surfaced to the PO after Loop 1, and the PO directed on 2026-10-01 that all five loops run before the solutioning is written ("This plan is devised once completing all loops"). Loops 2-5 therefore run as review loops under that direction. They do not advance the verdict: it stays HELD until the human-gate items in §D close and two consecutive loops score ≥95%.
> **Loop discipline:** this touches multiple services, so CCR v3 requires 5 or more loops (§2.4), and a score only counts when it holds across two consecutive loops. The solutioning to 95% (§E) is **devised after all loops complete**. Until then §E is a draft hypothesis, and Loops 4-5 attack it.
> **Reviewed:** 2026-10-01
> **Reviewer:** CCR v3, extended Scrum team. Four lenses ran in parallel, read-only:
> - **Director of Security**;
> - **Director of Data Science**;
> - **CI/CD + Sr SDET + SRE** (AI engineering and the test pyramid);
> - **DevOps Manager**.
>
> Each returned HELD. Their highest-impact claims were re-checked against the code before admission (marked **V**).
> **Under review:**
> - ADR-012, `docs/standards/OCR_STANDARD_secretsAndTokens.md`, and `docs/references/OCR_REFERENCE_secretsInventory_2026-10-01.md` (OCR-docs#151, #152);
> - the first Phase 0 implementation, ourSharedEvents#743.

---

## Loop log

| Loop | Layer focus | Who | Score (§D method) | Movement | Key finding |
|---|---|---|---|---|---|
| 1 | Critical: what would break this? | Four lenses in parallel (Security, Data Science, CI/CD-SDET-SRE, DevOps) | 3/38 = 8% readiness | — | Design kept; the live token, the static production admin path, deploy-token reach to data keys, and static-only tests |
| 2 | Conservative: what did Loop 1 assume but never verify; what did all lenses miss? | Verifier + adversary, read-only; every new High re-checked in code before admission | 2/62 = 3% readiness | **−5 points, from scope growth, not regression.** Ten holds added and two re-weighted; nothing that was closed reopened | Agents act as the owner, so review and tag rules cannot tell them apart (M1); a `v*` tag or dispatch ships unmerged code to production (M2); agent sessions hold owner-level connectors (M3); OCR-docs runs PR code on the self-hosted runner (M4). Four Loop 1 holds were narrower than stated (D3, T3, S6, D5) |
| 3 | Recursive: is the register complete and stable? Is any confidence inflated? | Completeness reviewer + inflation red-team, read-only; every new High re-checked live (`gh api`) | 0/75 = 0% readiness | **−3 points (decay).** R5 reopened: its corrections were not merged and left drift. Five holds added | CODEOWNERS is inert (GitHub cannot resolve `@mzdano`); production was already deployed on 2026-09-22 with staging-valued admin credentials; a dispatch deployed unmerged code to staging; an in-workflow ancestry check cannot close the tag path; the guard had 11 bypass classes, now fixed in #743 |
| 4 | Attack the draft solutioning (§E) | — | | | |
| 5 | Stability: re-score with no decay | — | | | |

## A. What the four lenses agree on

- **Keep:**
  - the trust-zone model;
  - environment secrets, never repository secrets, for anything above Z0;
  - per-environment Cloudflare and Access credentials;
  - Doppler as the only writer;
  - fresh production data keys;
  - credential isolation as a launch gate;
  - extending the existing `check-pr-secret-exposure` guard rather than a new checker.
- **The biggest single lever:** rotate the live token and close the production static-admin path. These are owner actions, about 30 minutes, and every lens names them first.
- **Defer past launch:** the two GitHub Apps and the GitHub Packages migration (they rewrite build wiring three weeks before launch), keyrings for every key, harden-runner block mode, canaries, and manifest tooling in the five docs-only repos.
- **Cut:** required reviewers as a precondition. ~~For one owner, a self-approval is a click~~ **(corrected in Loop 2):** GitHub never counts an author's own approval, so with one identity a required review either deadlocks every PR or forces the admin bypass the ADR forbids. The wall is branch and tag rules **plus a separate identity for agents** (R16).

## B. Findings by lens (High first)

### Director of Security

| # | Finding | Sev | |
|---|---|---|---|
| S1 | Phase 0 code does not close the main read path: `OCR_PROPAGATE_TOKEN` is still `env:`-injected in PR-reachable jobs (`oursharedevents-ci.yml:198,446,911,1032…`). Until it is rotated and split, the exposure record stays open | H | V |
| S2 | The inventory's "not exposed" row overclaims. A token with Workers edit can deploy code that reads `env.FORMS_ENCRYPTION_KEY` and the peppers | H | V |
| S3 | `ALLOW_OCR_INTERNAL = "true"` in `[env.production.vars]` (`wrangler.toml:324`), and the production Worker exists | H | V |
| S4 | Guard blind spots: sampled branch names, `toJSON(secrets)`, `secrets: inherit`, workflow-level `env:`, case | M | **closed in #743** (`efbaa44`) |
| S5 | `wrangler secret bulk` can overwrite data keys with a wrong Doppler value | M | |
| S6 | Swarm: no rate-limit rules planned on admin, sponsor and forms; sponsor links have no revocation | M | |
| S7 | The Doppler workspace owner has no recovery path or second human | L | |

### Director of Data Science

| # | Finding | Sev | |
|---|---|---|---|
| D1 | Same as S2: for real data, a deploy token is key access, not ciphertext access | H | V |
| D2 | BigQuery: every environment uses pool `cf-workers-pool` and subject `ose-worker` (`wrangler.toml:115,222,337`; `src/google/auth.ts:95`), so staging and production may map to one GCP principal. The scope also asks for `bigquery.readonly`, which the export does not need (`auth.ts:40`) | H (verify in GCP) | V (code) |
| D3 | `hashEmail` falls back to bare SHA-256 when `FORMS_HASH_PEPPER` is missing (`src/lib/pii.ts`), and the email hash is unversioned | M | V |
| D4 | **Doc drift:** `FORMS_ENCRYPTION_KEY` already has a keyring (`pii.ts`: a `{"v1","v2"}` map, version-prefixed ciphertext, `reencrypt-pii.ts`). The inventory's "rotating destroys data" is stale. No AAD, no key-strength check | M | V |
| D5 | A yearly `ANON_ID_HASH_PEPPER` rotation is a yearly cliff in return counts. Make it compromise-only, and mark epoch changes in the export | M | |
| D6 | The Cloudflare audit log likely records configuration, not D1 query reads, so the exposure window may be permanently unknowable | M (verify) | |

### CI/CD + Sr SDET + SRE

| # | Finding | Sev | |
|---|---|---|---|
| T1 | The pyramid is lopsided: everything is level 1-2 (static). The §10 attack classes are dynamic and have no level 5-7 home | H | |
| T2 | "Sandbox repo, test-only creds" has no spec (repo, owner, credentials, cadence, teardown). A PR-blocking job that depends on a second repo will be flaky and get switched off | H | |
| T3 | An agent can weaken the gate. CODEOWNERS binds only if "Require review from Code Owners" is on (unconfirmed). Fixtures live in the same file as the rules. The CI step and invariant spec need explicit protection | H | |
| T4 | Prompt-injection paths (PR text and comments reaching LLM workflows that hold keys) are missing from the attack list | H | |
| T5 | Canary and expiry monitoring have no alert route, owner or runbook | M | |
| T6 | "Born red" and "mutation-checked" are attestations with no recorded artifact | M | |

### DevOps Manager

| # | Finding | Sev | |
|---|---|---|---|
| O1 | **Launch-day trap:** `deploy-staging` runs on `refs/tags/v*` and `full-pipeline/*` PRs under `environment: staging` (`oursharedevents-ci.yml:1001-1008`), and `deploy-production` needs it. A `main`-only rule on `staging` blocks the launch tag | H | V |
| O2 | The retargeting order is unwritten. Deleting repo-level secrets before the environment copies exist turns all of CI red | H | |
| O3 | The T2/T4 test jobs seed D1 with the Cloudflare token (`:1450-1520`, `:1710-1784`), which conflicts with "Z1 never holds deploy/D1 credentials" | H | |
| O4 | Doppler branch configs may inherit their root's secrets, which would carry runtime data keys into CI environments. Use root environments, or separate projects, and verify with a throwaway secret | M (verify) | |
| O5 | An expired-token **merge blocker** amplifies outages (a lapse blocks the PR that fixes it). Use a scheduled warning instead | M | |
| O6 | The GitHub plan and repo visibility decide whether environments, rulesets and required reviewers work on private repos | M (verify) | |

### Loop 2 — verifier: corrections to Loop 1

Each row was re-checked against the code at `main` (OSE PR #743 head for the guard). **N** = narrower than Loop 1 said; **W** = wider.

| # | Correction | Evidence |
|---|---|---|
| S1 | **W.** `OCR_PROPAGATE_TOKEN` is PR-reachable in 10 OSE jobs (guard `--report`), and also in OER `ci.yml`, the hub `ci.yml` and brain-contract-check in OA/OSG/OSM/OSP/OSR/OW. The `:1032` line is `deploy-staging`, which PRs reach only via `full-pipeline/*` | `node scripts/check-pr-secret-exposure.mjs --report` |
| S2/D1 | **W.** One `CLOUDFLARE_API_TOKEN_OSE` serves the staging tests, the staging deploy **and** the production deploy and migrate. The token that seeds staging D1 in test jobs can deploy production | `oursharedevents-ci.yml:1061,1450,1710,2231,2247` |
| S3 | **W.** `smoke-production` sends the repo-level `X_OCR_INTERNAL`/`ADMIN_KEY`, the same values staging uses. OSE `CLAUDE.md` contradicts itself on whether production is deployed (§3 DevOps vs §4) | `ci.yml:2383-2384`; whether a production `X_OCR_INTERNAL` exists needs `wrangler secret list --env production` |
| S4 | **W.** Rule P flags only checkouts with an explicit `token:`. A default checkout still persists `GITHUB_TOKEN`: `claude-review.yml:74,157` holds `pull-requests: write` and `issues: write` | `check-pr-secret-exposure.mjs:441-449` |
| S5 | Design guard only. No `secret bulk` exists in the repo; secrets go through `wrangler secret put` one at a time | `scripts/set-secrets.sh:99` |
| S6 | **N.** The Worker already rate-limits admin (60/min/IP, production only), `/sponsor`, sponsor respond/request and forms (10/min per IP+event, per isolate). Missing: WAF/edge rules, an admin limit in staging, a cross-isolate forms limit. Sponsor-link revocation is absent (30-day expiry, or rotate the shared HMAC secret, which revokes every link) | `router.ts:603-611,1510,1522`; `forms.ts:74`; `sponsor-home-auth.ts:48,128` |
| D2 | Providers differ (`cf-workers-oidc-stg` vs `cf-workers-oidc`); the subject is shared; local dev reuses production's provider ID | `wrangler.toml:116,223,338` |
| D3 | **N.** Write paths already pass `requirePepper: true` with 503 guards. The one remaining call without it is self-delete, which silently matches nothing when the pepper is missing | `forms.ts:250,260,507`; `pages.ts:2101`; gap at `forms.ts:338` |
| D5 | **N.** `ANON_ID_HASH_PEPPER` is already epoch-versioned (migrations 0091/0092), the export counts only the current epoch, and a purge runbook exists. No yearly cadence was found | `anon-id-hash.ts:51-57`; `shared-report-export.ts:419,498`; `RUNBOOK-DEPLOYMENT.md:332-338` |
| D6 | **W, time-critical.** The repo's runbook gives Cloudflare audit-log retention per plan (Free: 24 h). If that holds, R10's review window may already be gone | `RUNBOOK-SEC-1-CLOUDFLARE-ACCOUNT.md:272-300` |
| T3 | **N in Loop 2; W after Loop 3** (CODEOWNERS is inert, N1 below). CODEOWNERS already names the workflows dir, guard, allowlist and invariant spec, and a meta-gate spec exists. Open: its CI check is a regex a comment would satisfy, `continue-on-error` is not checked, fixtures are inline, and the "Require Code Owners review" setting is unconfirmed | `.github/CODEOWNERS`; `ci-approval-gate-safety.invariant.spec.ts:63-143` |
| T4 | **W.** OSE `claude-review.yml`'s `review` job has **no `if:`**, so every comment from anyone with access runs it with `ANTHROPIC_API_KEY` and write scopes, reading author-controlled PR text. OW `claude-code-review.yml` has no author gate and loads an external plugin; OW `claude.yml` uses unpinned `claude-code-action@v1` | `claude-review.yml:29-60` |
| T5 | **N.** `cf-access-canary.yml` runs every 6 h, fail-closed, with GitHub's failed-run notification as its alert route. Missing: expiry monitoring, an owner, a runbook | `cf-access-canary.yml:15-17` |
| T6 | **N.** Born-red is recorded for ledger threats (`red_birth`, enforced by `born-red-harness.spec.ts`); mutation testing uploads an artifact. Missing for the #743 guard rules | `tests/fixtures/threat-ledger.ts` |
| O3 | Ranges were incomplete: also `:1786-1792` (FORMS_DB) and `:1897-1908` (seed fixtures, not `continue-on-error`) | `oursharedevents-ci.yml` |
| S7, O4, O6 | Not checkable from the repo; they stay owner verifications | — |

### Loop 2 — adversary: missed risks (each High verified in code)

| # | Finding | Sev | |
|---|---|---|---|
| M1 | **Agents act as the owner.** Claude commits, opens PRs and dispatches workflows as the owner's GitHub account, `bereasonable13` (`gh api user` in an agent session; OSE ADR-020:49-54 names `@mzdano`, which GitHub does not resolve). Declared protection has `required_pull_request_reviews: null`, so CODEOWNERS is advisory, and turning on a required review deadlocks single-identity authorship. "No bypass" cannot tell an agent from the owner | H | V (`tools/ci/main-branch-protection.json`) |
| M2 | **Tags and dispatch deploy unmerged code.** `deploy-production` runs on any `refs/tags/v*` push or a `deploy_production == 'PRODUCTION'` dispatch, with no check that the commit is on `main`. A tag ruleset limits *who*; the agent is that who | H | V (`oursharedevents-ci.yml:2172-2173`; no `merge-base --is-ancestor`) |
| M3 | **Agent sessions hold Z6 credentials.** Interactive and scheduled sessions carry connectors that can delete or query production D1, query BigQuery, merge PRs and trigger workflows. Standard §9 says an agent never holds more than Z0. Prompt injection via Linear, PR text or a fetched page reaches them | H | Observed, not durable: the 2026-10-01 agent sessions' tool lists included these connectors. A tool list is session-scoped, so R17's closing evidence is a recorded per-session-type snapshot reviewers can re-check |
| M4 | **A self-hosted runner executes PR code.** OCR-docs `actions-selftest.yml` runs `on: pull_request` on `[self-hosted, windows]`, and its paths filter includes the workflow itself | H | V (`actions-selftest.yml:18-20,38`) |
| M5 | **Credentials can land in artifacts.** The UI-smoke Playwright config sends the Access secret and `ADMIN_KEY` as headers with `trace: 'retain-on-failure'`; T4 uploads `test-results/` for 14 days; the CI file has no top-level `permissions:` | M (H once secrets move to environments) | V (`playwright.ui-smoke.config.ts:43-48,122,137`) |
| M6 | **Hub `main` is in production's trust base.** The deploy bundles hub code at `.ocr-hub-ref`; whoever merges to hub `main` reaches production. The hub reads `OCR_PROPAGATE_TOKEN` on `pull_request`. `publish-flags` is not a production path today (OSE uses `file:`) | M | |
| M7 | **Z5 secrets beyond the data keys lack distinctness and dual-key checks:** `ADMIN_KEY`, `X_OCR_INTERNAL`, the sponsor-link HMAC, `WKRP_SERVICE_TOKEN`, `OSE_INTERNAL_BATCH_TOKEN` (single-value, no previous key). OW stores Spotify and Last.fm tokens **in plaintext** when `WKRP_ENCRYPTION_KEY` is absent | M | V (OW `src/lib/kv-storage.ts:107-110`) |
| M8 | **Orphans:** S6 and S7 map to no register item, nor does robot-knowledge's `ROBOT_PAT` input injection. Single-owner loss covers GitHub org owner and Cloudflare super-admin, not just Doppler | M | |

**Dismissed in Loop 2:** actions/cache poisoning (cache is ref-scoped; no `download-artifact` in deploy jobs); `id-token: write` in OW (no OIDC trust binding exists yet; the future binding must pin event and ref, Standard §4.4).

### Loop 3 — recursive: completeness, decay and inflation

Every High below was re-checked live (`gh api`, `gh run view`) before admission.

| # | Finding | Sev | |
|---|---|---|---|
| N1 | **CODEOWNERS is inert** in OSE (9 lines) and OCR-docs (6 governance lines): GitHub reports "Unknown owner … make sure @mzdano exists". Only `/ocr-docs-brain/ @bereasonable13` resolves. The human-review gate that the OCR-docs `CLAUDE.md` describes, and R4's premise, do not hold today | H | V (`gh api repos/ourCommunityRituals/{ourSharedEvents,OCR-docs}/codeowners/errors`: 9 and 6 errors) |
| N2 | **Production was deployed by CI on 2026-09-22** (run 35679613677, `workflow_dispatch` on `main`): Deploy → Production and Smoke → Production both succeeded. `smoke-production` has no `environment:` and sent the repo-level, staging-valued `ADMIN_KEY`, `X_OCR_INTERNAL` and `CF_ACCESS_*` to production. Production keys existed from that date | H | V (`gh run view 35679613677`) |
| N3 | **A dispatch deployed unmerged code to staging.** Run 35281104788 (2026-09-17, `workflow_dispatch` on `feat/epic-triangle-event-lifecycle`) ran T1 Deploy → Staging at `2058984`, which is not on `main` (53 ahead, 160 behind). `deploy-staging` admits `workflow_dispatch && deploy_staging == 'true'` from any ref. Other dispatchable workflows holding secrets have no ref check either, including OSE `conformance-report` and OCR-docs `propagate-standards` (write PAT) | H | V (`gh run view`; `gh api …/compare/main...2058984`) |
| N4 | M5 is wider: T3 smoke's security section uses `playwright.e2e-smoke.config.ts` (`trace: 'retain-on-failure'`) with Access and `ADMIN_KEY` headers, and uploads its report for 14 days; `playwright.e2e.config.ts` does the same with trace and video (npm scripts only) | M | |
| N5 | The fleet template `OCR-docs/.github/examples/spoke-ci-reference.yml` runs PR jobs on `[self-hosted, windows]` and deploys production with a repo secret and no `environment:`. Hub `security-bracket.yml` takes a caller-supplied `runs-on` | M | |
| N6 | R15's planned fix is unsound: a tag push runs the **tagged commit's** workflow file, which can delete an in-file `merge-base --is-ancestor` step. Production must be gated by a rule outside the deployed commit (environment admits `main` only; release by dispatch on `main`) | H | reasoning, accepted |
| N7 | `${{ inputs.* }}` in `run:` (boolean `force_clean` ×10 in OSE; `inputs.environment` in `deploy-spoke`); the PAT in a push URL in `conformance-report.yml:146` | L | |

**Narrowed:** T4's LLM step cannot run on `issue_comment` (its charter step needs `github.base_ref`, which is empty there); OSE `claude-review` and OW `claude-code-review` already pin `claude-code-action` by SHA, so only OW `claude.yml` is on `@v1`.

**Guard red-team (S4 reopened, then fixed in #743):** a read-only pass built workflows that leak a secret yet pass the guard: case-folded comparisons, `failure()` and `needs.<job>.result == 'failure'`, attacker-chosen head and base branches on the `pull_request` path, `pull_request_review` triggers, local reusable workflows, whitespace and case in secret references, and a non-success source conclusion on `workflow_run`. Each is fixed in #743 (`eff1539`, `7c19044`, `4d0bb11`) with a fixture born red against the previous guard and red again when its fix is reverted (40 fixtures). Still not modelled: unfiltered `push`, `issue_comment` jobs that check out PR code, `merge_group`, default-token checkouts with write scopes (tracked in R3 and R27).

**R5 reopened:** its closing evidence was "§C corrections merged", and they are not merged (PR #153). They also left drift: ADR-012's data-loss claim, the pepper-versioning claim, the yearly cadence for peppers, the bare-SHA-256 scope, the "self-approval is a click" line, the dependabot line, and "production never deployed". All are corrected in this change; R5 closes when #153 merges.

**Drift outside this PR (report only, to be filed in the owning repo):**
- OSE `CLAUDE.md`: §3 DevOps says both "the Worker exists" and "never been deployed"; §4 and §5 say production was never deployed (false, N2); §4 says the static-admin fallbacks are staging-gated (production has `ALLOW_OCR_INTERNAL = "true"`).
- OSE ADR-020:49-50 names `@mzdano`; the account is `bereasonable13`.
- OCR-docs `CLAUDE.md` "Enforcement": CODEOWNERS routes governance paths to a human reviewer. It does not today (N1).
- Brain invariant #28: treats `full-pipeline/*` gating as not reachable, relies on CODEOWNERS and required reviewers, applies to OSE only, and its spec regex misses `on: [pull_request_target]`. The proposed `credential_isolation` invariant needs sub-clauses for agent identity, deploy gating outside the deployed commit, dispatch, self-hosted runners, artifacts, reviewer validity (`codeowners/errors` empty), templates, runtime static admin, and out-of-org repos.

## C. Corrections applied in this change (reactive correction)

- **Inventory exposure record:** "not exposed" now says the data keys were not stored in GitHub, but were reachable through the Workers-edit token by deploying code. Production keys minted before the token split count as exposed (S2/D1).
- **Inventory §2.3 and finding 8:** the `FORMS_ENCRYPTION_KEY` keyring exists, so its rotation path is re-encrypt then retire, not data loss (D4). `FORMS_HASH_PEPPER` falls back to bare SHA-256 (D3).
- **Standard §2:** peppers rotate on compromise only, until hashes are versioned (D5).
- **Standard §3:** Doppler isolation uses **root environments or separate projects**, not branch configs (O4). `wrangler secret bulk` gets a data-key denylist (S5).
- **Standard §5:** expiry is a scheduled warning issue, not a merge blocker (O5).
- **Inventory §3 Phase 1:** the `staging` environment's branch rule must admit the release-tag path (O1). The rollout order and the D1-seeding move are added (O2, O3).
- **Loop 3:** ADR-012 (rotation facts, pepper versioning, the reviewer control, agent identity as a prerequisite, production gated outside the deployed commit); Standard (agent identity prerequisite, Z1 dispatch enforced by the branch rule, Z3 released by dispatch on `main`, yearly rotation for encryption and signing keys but never peppers, §9 agent sessions marked "not true today"); inventory (ANON pepper runbook, `requirePepper` scope, dependabot, production deployed 2026-09-22, the 2026-09-17 feature-branch deploy, decision 2, step 1.2's attack).

## D. Risk register and score

**Method (re-derivable):**
- Each hold has a weight: High = 3, Medium = 2.
- Credit: **closed with evidence** = 1. **Mitigated with an owner-signed documented assumption** = 0.5, for non-security items only. **Open** = 0.
- Security items get **no partial credit** (CCR v3, Security Critical tier).
- **Score = Σ(weight × credit) ÷ Σ weight.** For example, one closed weight-3 hold out of 38 scores 3/38.
- Per the protocol, PASS also needs the score to hold across **two consecutive loops**.

| # | Hold | Wt | Sec | Today | Closes when (evidence) | Who | Tranche |
|---|---|---|---|---|---|---|---|
| R1 | Live write-capable PAT (S1) | 3 | ● | open | The org audit log shows the old token's revocation (date recorded); `gh secret list --org` shows only the new names; guard `--report` shows no PR-reachable writer. Any read token left in PR jobs is a recorded Z0 exception with a removal date (or decision 5 removes it). Covers every repo in S1, hub and OER included, and the write-PAT dispatch paths (`propagate-standards`, `conformance-report`; see R27) | owner + code | B |
| R2 | Production static admin path (S3, N2) | 3 | ● | open | Production `X_OCR_INTERNAL`, `ADMIN_KEY` and `ADMIN_TOKEN` absent (`wrangler secret list --env production`). `ALLOW_OCR_INTERNAL` off with a config test. `smoke-production` runs in environment `production` on the production Access token. A refusal test runs **against production** | owner + code | A+B |
| R3 | Persisted checkouts and PR-sourced `workflow_run` (0.1, 0.2; S4) | 3 | ● | in #743 | #743 merged with CI green and its 40 born-red fixtures recorded. Rule P also flags default-token checkouts in jobs with write scopes. The guard scans every workflow-shaped file (incl. `.github/examples/`) and the not-yet-modelled classes (unfiltered `push`, `issue_comment` PR checkouts, `merge_group`) each have a born-red fixture. The same fix lands in OW, OA, OSG, OSM, OSP, OSR, OCR-docs, the hub and OER, each with its born-red SHA | code | A |
| R4 | Gate anti-weakening (T3) | 3 | ● | open | The meta-gate parses the workflow YAML and fails on a removed guard step or `continue-on-error`; fixtures in a separate file; "Require Code Owners review" on. **Needs R16 and R26 first** | code + owner | A+B |
| R5 | Doc overclaims and drift | 2 |  | **reopened (Loop 3)** | #153 merged with the Loop 2 and Loop 3 corrections, and a re-read finds no statement the loops disproved | code | A |
| R6 | Production data keys (S2, D1, D3, N2) | 3 | ● | open | Production keys minted after R25, from a production-gated step. Evidence: a new keyring version id or `pepper_epoch` fingerprint dated after the split, plus the Doppler activity-log date; staging/production fingerprints kept as manifest metadata (hash prefixes only), compared in a manifest check, not inside a Z3 job. Self-delete passes `requirePepper`; the bare SHA-256 fallback is removed in production | code + owner | A+B |
| R7 | BigQuery principal shared across environments (D2) | 3 | ● | open | A distinct `sub` per environment, IAM bound per subject (verified in GCP), `bigquery.readonly` dropped, local dev off production's provider. An attack shows the staging token cannot write the production dataset | code + owner | A+B |
| R8 | Rollout order and environment rules (O1, O2) | 3 |  | open | Runbook written. `staging` admits `main` (and `full-pipeline/*` only if decision 6 keeps it); `production` admits `main` only. Environment copies proven green before repo secrets are deleted. Each environment holds distinct values (fingerprint check) | code + owner | A+B |
| R9 | Test-pyramid gap (T1, T2, T4, T6) | 3 | ● | open | Offline dynamic PR tests; a nightly sandbox attack run with written pass criteria; attacks include a tag on an off-`main` commit carrying an edited workflow, a dispatch from a feature branch, and an agent-identity attack; born-red runs recorded; at least one attack run by an identity other than the agent that wrote the guard. **Needs the sandbox repo and R16** | code + sandbox | A+C |
| R10 | Exposure record and audit-log limits (D6, N2, N3) | 3 | ● | open | **Time-critical:** GitHub and Cloudflare audit logs exported now. The record names runs 35679613677 (production deploy and smoke with staging-valued admin credentials) and 35281104788 (feature branch to staging). Unobservable reads recorded as "unknowable". Record closed, dated | owner | B |
| R11 | Test jobs hold the deploy/D1 token (O3) | 3 | ● | open | D1 seeding moves into the `staging-deploy` job, or test jobs use a D1-only staging token. Guard `--report` shows no test job reaching a token that deploys production. **Needs R8 and R25** | code | A |
| R12 | Doppler isolation verified (O4, S5) | 2 | ● | open | A throwaway-secret test shows CI and deploy configs do not carry runtime keys. Bulk denylist in place. (Security since Loop 3: runtime data keys in CI configs are an exposure) | owner + code | B |
| R13 | GitHub plan and visibility (O6) | 2 |  | open | `gh api orgs/ourCommunityRituals --jq .plan.name` recorded, and the plan's limits written into the standard. robot-knowledge sits under a personal account, outside org rulesets: recorded | owner | B |
| R14 | Expiry and canary operations (T5, O5) | 2 |  | open | The scheduled expiry-warning job (issues at 21 and 3 days), a named owner, the break-glass runbook, and a production-credentials canary. **Needs the manifest (inventory Phase 2.1)** | code | A |
| R15 | Tags and dispatch deploy unmerged code (M2, N3, N6) | 3 | ● | open | `production` admits `main` only, verified with `gh api`; production is released by `workflow_dispatch` on `main`, not by a tag push. `deploy-staging` dispatch is limited to `main` by the `staging` rule. A sandbox test pushes a `v*` tag on an off-`main` commit **carrying an edited workflow** and dispatches from a feature branch; neither deploys. **Needs R8 and R16** | code + owner | A+B |
| R16 | Agents share the owner's identity (M1, N6) | 3 | ● | open | `gh api user` inside an agent session returns a bot login, not `bereasonable13`. The bot has no admin or bypass. Protection has `require_code_owner_reviews: true` with count ≥ 1 and a resolvable human owner (R26) | owner + code | B |
| R17 | Agent sessions hold owner-level connectors (M3) | 3 | ● | open | Recorded tool-list snapshots per session type: no `d1_database_delete`/`query`, `execute_sql`, `merge_pull_request` or `actions_run_trigger` on unattended routines; production-capable connectors on interactive sessions only by recorded exception. Standard §9 matches. **Needs R16** | owner + code | A+B |
| R18 | Self-hosted runners run PR code (M4, N5) | 3 | ● | open | `actions-selftest.yml` moves to a hosted runner or drops `pull_request`; `spoke-ci-reference.yml` fixed; a caller-supplied `runs-on` restricted. A guard rule fails on self-hosted with a PR or non-`main` trigger, fleet-wide, templates included | code | A |
| R19 | Credentials in CI artifacts (M5, N4) | 2 | ● | open | Traces, video and HAR off or headers redacted in every config that sends credentials (UI smoke, e2e-smoke, e2e). An induced-failure sandbox run's artifact is scanned and holds no credential. Top-level `permissions:` fleet-wide | code | A |
| R20 | Z5 secrets beyond data keys (M7) | 2 | ● | open | Distinctness check covers `ADMIN_KEY`, the sponsor-link HMAC and both service tokens; the service tokens accept current + previous. OW refuses to store tokens without `WKRP_ENCRYPTION_KEY` in staging and production, with a test | code + owner | A+B |
| R21 | LLM workflow gating (T4) | 2 | ● | open | OSE `claude-review` `review` job runs on `pull_request` only; OW review author-gated and its plugin pinned or removed; OW `claude.yml` pinned by SHA; no `${{ secrets.* }}` inside `run:` | code | A |
| R22 | robot-knowledge input injection (M8) | 2 | ● | open | Dispatch inputs reach `run:` through `env:`, never `${{ }}`; a guard rule added; personal-account scope recorded | code | A |
| R23 | Edge limits and link revocation (S6) | 2 | ● | open | WAF or rate-limit rules recorded for admin, sponsor and forms; the admin limit on in staging; sponsor links carry a revocable id. (Security since Loop 3: revocation is an auth control) | code + owner | A+B |
| R24 | Owner recovery (S7, M8) | 2 |  | open | Recovery codes escrowed; a second owner or break-glass account on GitHub, Cloudflare and Doppler, recorded; every identity listed | owner | B |
| R25 | Per-environment Cloudflare and Access credentials (S2, O3) | 3 | ● | open | `CLOUDFLARE_API_TOKEN_OSE` revoked; `CF_DEPLOY_STG`, `CF_DEPLOY_PRD` (and a D1-only staging token if R11 uses one) minted with expiry, per-Worker scope if offered; one Access service token per environment; each in its environment only | owner + code | B |
| R26 | CODEOWNERS validity (N1) | 3 | ● | open | `codeowners/errors` returns 0 in every repo, checked by a meta-gate; the owner named is a human who is not the agent's identity. **Needs R16** | owner + code | A+B |
| R27 | Dispatchable workflows holding Z1+ secrets (N3) | 3 | ● | open | Every `workflow_dispatch` workflow that holds a Z1-or-higher secret runs in an environment whose branch rule admits `main` only; a guard rule fails on one that does not | code + owner | A+B |
| R28 | Other long-lived Z0 secrets | 2 | ● | open | `LINEAR_API_KEY` (a personal key), `BRANCH_PROTECTION_READ_TOKEN` and `ANTHROPIC_API_KEY` each removed from PR jobs or recorded as a dated Z0 exception with a cap | code + owner | A+B |
| R29 | Third-party actions on tags in secret-holding jobs | 2 | ● | open | `dorny/test-reporter`, `step-security/harden-runner`, OW `dopplerhq/cli-action` and OW `claude-code-action` pinned by SHA; a guard rule fails on a tag-pinned third-party action in a job that holds a secret | code | A |

**Dependencies (Loop 3):** R4 ← R16, R26 · R26 ← R16 · R17 ← R16 · R9 ← sandbox repo, R16 · R15 ← R8, R16 · R8 ← R13, decision 6 · R6 ← R25, R12 · R11 ← R8, R25 · R2 ← R25 · R20 ← R6 · R14 ← manifest (Phase 2.1). **R16 is the root:** five holds cannot close until agents have their own identity.

**Loop 3 changes to the register:** R5 reopened; R12 and R23 marked security; R1, R2, R3, R4, R6, R7, R8, R9, R10, R11, R15, R16, R17, R18, R19 and R21 have corrected closing evidence; R25-R29 are new.

Total weight = 17×3 + 12×2 = **75** (method: sum the Wt column over the 29 rows of the table above).

**Score after Loop 3: 0 / 75 = 0% readiness.** Nothing is closed with evidence. Loop 2's 2/62 counted R5, which Loop 3 reopened.

The *design* is not what is scoring low here. All four lenses kept the model; the open items are execution and verification.

## E. Solutioning to 95% — DRAFT (input to Loops 4-5; finalized after Loop 5)

> **Superseded by Loop 2.** The draft below was sized against the Loop 1 register (38). Its tranche percentages no longer hold against 62, and it does not cover R15-R24. It is kept as the Loop 1 hypothesis. The re-draft follows Loop 3, and Loops 4-5 attack it.

95% of 38 is 36.1, so at most one **Medium, non-security** hold may remain, and only as an owner-signed documented assumption. In practice, every security hold must close with evidence.

### Tranche A — code (Claude; no dashboard access needed; about 2 to 3 days of PRs)

| Hold | Work | Evidence |
|---|---|---|
| R3 | Land #743. Port rules P and W plus `persist-credentials: false` to OW, OA, OSG, OSM, OSP, OSR and OCR-docs (the guard ships as a shared action from OCR-docs) | Each repo's guard born red, then green, with CI green |
| R4 (code) | CODEOWNERS entries; a meta-gate spec (guard plus self-test steps present, not `continue-on-error`); fixtures moved to `check-pr-secret-exposure.fixtures.mjs` | Meta-gate born red by deleting the step |
| R2 (code) | `ALLOW_OCR_INTERNAL` removed from `[env.production.vars]`, with a config test; `smoke-production` moved to the production Access token. Merges only after the owner mints that token (R2-B) | Config test born red; refusal test |
| R6 (code) | `requirePepper` on the production write path (no bare SHA-256 fallback in production); `scripts/check-prod-keys.mjs` (present, length, staging ≠ production fingerprint, from secret metadata only) | Tests born red |
| R7 (code) | `sub` = `ose-worker-<env>`; `bigquery.readonly` dropped | Unit test on the JWT claims |
| R8 (code) | Runbook `RUNBOOK-SECRETS-MIGRATION.md` with the safe order: add environment syncs → add `environment:` to jobs (non-breaking) → green → delete repo copies. Plus the tag-path rule | Doc + a dry-run checklist |
| R9 (code) | Offline dynamic tests in the T0 shard: a local bare repo plus `actions/checkout` semantics shows no credential persists; a `workflow_run` simulator over an adversarial branch corpus; a prompt-injection fixture set for the LLM workflows. Plus the sandbox spec document | Born red against the pre-#743 workflows |
| R11 | Move D1 seeding out of T2/T4 into the deploy job (or use a D1-only staging token) | Staging chain green |
| R14 | A scheduled expiry-warning workflow reading the manifest; the break-glass runbook; a production-credentials canary workflow | Dry run |

**After A** (counting only items that need no owner action): R3, R5, R11 and R14 closed → (3+3+2+2) / 38 = **26%**. R2, R4, R6, R7, R8 and R9 are code-complete, waiting on owner verification.

### Tranche B — owner (about 2 hours of dashboard work plus 1 to 2 hours of audit-log review; scriptable parts scripted in A)

1. **Today:**
   - rotate `OCR_PROPAGATE_TOKEN`: a read-only expiring fine-grained token for PR jobs, plus a separate write token for the three trusted writer workflows;
   - **delete** the old token;
   - check and delete production `X_OCR_INTERNAL`;
   - set `OCR_CI_EDGE_TOKEN` and its WAF rule (R1, R2).
2. Run the plan check (R13). Turn on "Require review from Code Owners" (R4).
3. Cloudflare:
   - mint `CF_DEPLOY_STG` and `CF_DEPLOY_PRD`, scoped per Worker if offered, with expiry;
   - mint `CF_READ`;
   - create one Access service token per environment (R2, R6).
4. Doppler: root environments for CI and deploy; a throwaway-secret inheritance test; syncs retargeted in the runbook order (R8, R12).
5. Fresh production data keys, after step 3 (R6).
6. GCP: bind IAM per environment subject (R7).
7. Review the audit logs, then record and close the exposure record (R10).

**After B:** everything except R9 → 35 / 38 = **92%**. Still HELD: correctly, the dynamic attack tests have not run.

### Tranche C — prove it (sandbox plus two CCR loops)

1. The owner creates `ocr-redteam-sandbox` with test-only secrets. The nightly attack suite runs and records its born-red and green runs (R9).
2. **Loop 4:** re-run the four lenses against the evidence. **Loop 5:** re-run again. PASS needs ≥95% in both, with no decay.

**After C:** 38 / 38 = **100%** register closure. The verdict is set by the two stable loops, and the target is **≥95%**.

### Deferred, with a documented post-launch plan (not counted against launch)

- the two GitHub Apps and the GitHub Packages migration (or decision 5: make OCR-docs and the hub public);
- harden-runner block mode;
- canaries beyond the production-credentials one;
- AAD on ciphertext;
- `kid` on signing secrets;
- the per-repo manifest metadata in the five docs-only repos.

## F. Owner decisions that change the path

- **Decision 5 (make OCR-docs and the hub public):** removes R1's read token entirely, and the Apps/Packages migration.
- **Decision 6 (retire `full-pipeline/*` PR deploys):** simplifies R8.
- **R13 (plan):** if the org is on Free, private-repo environments and rulesets are limited. Then the wall becomes repo visibility, or a plan upgrade, which is a cost decision under ADR-006.
