# CCR Gate Review — ADR-012: secrets by trust zone (credential isolation)

> **Verdict:** **HELD at the human gate (CCR v3 §2.3), with six review loops recorded.** On 2026-10-02 the scope widened to the full security posture (§D2). The score after Loop 6 is **12/184 = 6.5%**, down from Loop 5 because R5 reopened. The design is still right. The open items are execution: a write-capable token, a static production admin header, an anonymous id that the data model can link to named form rows, and pipeline walls that are not yet built. The solution plan in §E reaches 95.1% after Phase 7 and PASS after Phase 8.
> **Human gate (CCR v3 §2.3):** each loop has scored below 95%, and Loop 3 scored lower than Loop 2, so the protocol's human gate is open. It was surfaced to the PO after Loop 1, and the PO directed on 2026-10-01 that all five loops run before the solutioning is written ("This plan is devised once completing all loops"). Loops 2-5 therefore run as review loops under that direction. On 2026-10-02 the PO directed a further three-loop run on the widened scope ("run a CCR assessment lead by the Dr of security on a 3 loop run with the extended scrum team"); that run is recorded as Loops 4-6. **None of the gaps surfaced at the gate has been resolved by a human yet.** So Loops 2-6 are supplemental review loops run under PO direction, not protocol advancement past the gate. The verdict stays HELD until the human-gate items in §D and §D2 close and two consecutive loops, each run after that resolution, score ≥95%.
> **Loop discipline:** this touches multiple services, so CCR v3 requires 5 or more loops (§2.4), and a score only counts when it holds across two consecutive loops. Six review loops are recorded (see the human-gate note above). §E is the final plan, written after Loop 6 and corrected by it and by the PR review.
> **Reviewed:** 2026-10-01 (Loops 1-3); 2026-10-02 (Loops 4-6, combined register)
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
| 4 | Critical, on the widened scope (§D2) | Six lenses in parallel: Security (lead), Backend, FE, SDET/SRE, DevOps, Data Science | 14/174 = 8.0% | Scope widened from 75 to 174 | Raw anonymous id in four FORMS_DB tables (N-DS-1); second-precision join defeats the scan split (N-DS-2); full URL with tokens logged (N-SEC-1); S1, S2, S14, S15 closed in code |
| 5 | Conservative: verifier + adversary | Verifier re-checked every High in code; adversary hunted for what all six missed | 14/176 = 8.0% | Flat. Four items narrowed, two dropped, six added | Forgeable `ose_anon` and `/q/` without a rate limit (N-ADV-1); self-delete email oracle; no CSRF guard; workflow script injection |
| 6 | Recursive: completeness, inflation, red-team the plan | Director of Security, three passes | **12/184 = 6.5%** | **−1.5 points (decay): R5 reopened**; seven items added | Ten plan defects, including rotating before wiring (breaks CI), the audit-log export ordered too late, and A2 too destructive for one PR. Corrected order in §E |

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
- **Cut:** required reviewers as a precondition. ~~For one owner, a self-approval is a click~~ **(corrected in Loop 2):** GitHub never counts an author's own approval, so with one identity a required review either deadlocks every PR or forces the admin bypass the ADR forbids. The wall is protected `main` and environment branch rules set in repository settings (tags are labels only and never authorize a deploy), **plus a separate identity for agents** (R16).

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
- **Inventory §3 Phase 1:** ~~the `staging` environment's branch rule must admit the release-tag path (O1)~~ **superseded in Loop 3:** the tag trigger is retired instead, and every credential-bearing environment admits `main` only (tags are labels; N6). The rollout order and the D1-seeding move are added (O2, O3).
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
| R8 | Rollout order and environment rules (O1, O2) | 3 |  | open | Runbook written. `staging`, `staging-deploy` and `production` each admit `main` only: a `full-pipeline/*` PR branch is Z0 and never enters a credential-bearing environment. If decision 6 keeps PR-time previews, they run as a separate credential-free preview flow (no environment, no secrets), recorded as its own zone first. A PR-triggered job naming any of the three environments is refused. Environment copies proven green before repo secrets are deleted. Each environment holds distinct values (fingerprint check) | code + owner | A+B |
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

**Dependencies (Loop 3):** R4 ← R16, R26 · R26 ← R16 · R17 ← R16 · R9 ← sandbox repo, R16 · R15 ← R8, R16 · R8 ← R13 · R6 ← R25, R12 · R11 ← R8, R25 · R2 ← R25 · R20 ← R6 · R14 ← manifest (Phase 2.1). **R16 is the root:** five holds cannot close until agents have their own identity.

**Loop 3 changes to the register:** R5 reopened; R12 and R23 marked security; R1, R2, R3, R4, R6, R7, R8, R9, R10, R11, R15, R16, R17, R18, R19 and R21 have corrected closing evidence; R25-R29 are new.

Total weight = 17×3 + 12×2 = **75** (method: sum the Wt column over the 29 rows of the table above).

**Score after Loop 3: 0 / 75 = 0% readiness.** Nothing is closed with evidence. Loop 2's 2/62 counted R5, which Loop 3 reopened.

The *design* is not what is scoring low here. All four lenses kept the model; the open items are execution and verification.

## D2. Combined security register (Loops 4-6, 2026-10-02)

On 2026-10-02 the founder widened the scope of this gate. It now covers the full security posture: this register (R1–R29), the access-control CCR (OSE-1444, findings S1–S15, `ourSharedEvents/.claude/outputs/CCR-ACCESS-CONTROL-AUDIT-ISOLATION-2026-09-30.md`), the token-exposure epic (OSE-1469), and the gap areas filed under the umbrella epic OSE-1477. The founder's directives: "Security is always #1. Then we can get to the functionality." "If the platform is not secure, then the fundamental claim is no longer attainable."

**Lenses in Loop 4.** Six ran in parallel, read-only, on `ourSharedEvents` main `5f4381f`:

- Director of Security (lead);
- Lead Backend Architect;
- Lead FE Integration + Sr Design FE;
- Sr SDET + SRE;
- DevOps Manager;
- Director of Data Science.

**Loop 5.** A verifier re-checked every High in code, and an adversary looked for what all six lenses missed.

**Loop 6.** A recursive pass checked completeness and inflation, red-teamed the plan, and re-scored.

**Method.** The scoring method is unchanged from §D, with one addition: Low = 1.

### Changes to R1–R29

| # | Change | Evidence |
|---|---|---|
| R5 | **Reopened (Loop 6).** Loops 4-5 disproved more doc statements: `RUNBOOK-SEC-2.1` says "Active" but its tables are blank; root `CLAUDE.md` §4 says the X-OCR-Internal/Bearer fallbacks are "staging" only; the OSE-1080 "known gap" line is stale (`router.ts:629` guards object scope) | `wrangler.toml:325` sets `ALLOW_OCR_INTERNAL = "true"` in `[env.production.vars]` |
| R2 | Wider. A static `X-OCR-Internal` header is a `key:` actor, and `requireKeyActor` admits it, so its holder can write **production** global flags and run erasure. `set-secrets.sh:66` still provisions a dead production `ADMIN_KEY`. The deploy gate checks only that secrets are present | `auth/admin.ts:380-383`, `lib/admin-object-scope.ts:240-247`, `.github-secrets-required.json:130`, `oursharedevents-ci.yml:2236` |
| R6 | Wider. Self-delete hashes without `requirePepper`. The rate-limit pepper silently falls back to unpeppered SHA-256 when unset or under 32 characters. There is no key-strength check, and `FORMS_HASH_PEPPER` has no version | `forms.ts:338`, `lib/rate-limit.ts:113-125`, `lib/pii.ts:139-143,179` |
| R10 | Wider. The exposure record must also cover the window in which a browser extension (Pieces) could read the admin and Linear pages. The founder removed it on 2026-10-02 | OSE-1474 |
| R19 | Re-weighted 3→2 after Loop 5. The 30-day production upload does not contain the credentialed run. Staging uploads `test-results/` and the e2e-smoke report for 14 days. Spec-level headers and a minted `CF_Authorization` cookie also reach the browser context | `oursharedevents-ci.yml:1300-1311,2045-2059`; `tests/e2e/helpers/cf-access-auth.ts:45-50` |
| R20 | Wider. One `SHARED_REPORT_SIGNING_SECRET` signs sponsor-home, report and beacon tokens. There is no `kid`, no previous-value overlap and no `exp` cap. OW stores Spotify/Last.fm tokens in plaintext when its key is unset; that is split out as OW-1 | `sponsor-home-auth.ts:94`, `beacon-token.ts:111`, `shared-report-auth.ts:161` |
| R22 | Re-weighted 2→3. Shell injection in a job that holds `ROBOT_PAT`. Drops back to 2 if the PAT is scoped to that one repo | `robot-knowledge/.github/workflows/robot-commit.yml:28-50` |
| R25 | Unchanged. Note: closing it needs the split names wired in CI first (see the plan, Phase 5) | Loop 6 |

### OSE-1444 findings re-checked

**Closed with evidence:**

| # | Evidence |
|---|---|
| S1 | `requireKeyActor`, `router.ts:1290,1309`; test `global-flags-key-actor.invariant.spec.ts`. In production it has no security effect until R2 closes |
| S2 | `_platformOnly`, `router.ts:436` |
| S14 | `handlers/events.ts:499-536` |
| S15 | `router.ts:722-728,1125-1131`; test `platform-scope-tenant-writes.invariant.spec.ts` |

**Open:**

| # | Status and evidence |
|---|---|
| S3 | Roles are not enforced on destructive brand actions; `resolveAdminRoles` has one caller (`audit.ts:117`) |
| S4–S9, S11 | As in OSE-1444 |
| S10 | Merged with N-DO-3, H. `CF_ACCESS_AUD = ""` (`wrangler.toml:218,334`), so a JWT from another Access app on the same team (staging) validates on production. `ALLOWED_ADMIN_DOMAINS` admits every mailbox on the domain |
| S12r | H. Erase is now platform-scope, but one operator can run it with no second approver, so one stolen session can erase across every tenant (`router.ts:1321-1330`) |
| S13 | Wider. The response is `ok:true` on a partial failure (`data-subject.ts:264-273`). It also skips `form_surveys.anonymous_id` and `checkin_counts.last_anonymous_id` |

### New items (verified in code in Loop 5)

| id | Finding | Wt | Sec |
|---|---|---|---|
| N-SEC-1 | An unhandled error logs the full `request.url`, query included, with Workers Logs on. Live `/sponsor?t=` and `/sharedReport?token=` credentials land in the logs (`src/index.ts:54`, `wrangler.toml:79`) | 3 | ● |
| N-DS-1 | The raw `anon_<uuid>` cookie value is written to `form_registrations`, `checkin_counts`, `form_surveys` and `email_signups` (`forms.ts:276-288,397-401,454-457,531-541`) and to `scan_node_returns` (`scan-buffer.ts:89-93`). Retention is off by default. Anyone who can read both databases can link a named registration to a scan history. **This breaks the anonymity claim at the data model** | 3 | ● |
| N-DS-2 | Both split scan tables write `created_at` at second precision in one batch (`scan-buffer.ts:83-84,90-91`; `migrations/0062:16,35`). A join on `event_id` + `created_at` re-links WHO to WHERE, which defeats the OSE-798 split | 3 | ● |
| N-DO-5 | Three runbooks run `wrangler d1 delete` on the production DBs (`ROLLBACK_PLAN.md:92-93`, `DISASTER-RECOVERY.md:79`, `ROLLBACK.md:101,154`). The DR export dumps PII to `backup/*.json`, which `.gitignore` does not cover. A restore brings erased PII back. No drill has been run | 3 | ● |
| N-QA-2 | With `OCR_CI_EDGE_TOKEN` unset, T4 stops at `oursharedevents-ci.yml:1733-1745`. T4a–T4h are skipped, and red-team T5/T6 run only after a CI success, so level 7 and the adversarial layer are off and no story can reach Done (OSE-1443) | 3 | ● |
| G-GH | GitHub org security baseline (OSE-1479; absorbs 2FA/recovery OSE-1478) | 3 | ● |
| N-DS-3 | `logFormEvent` logs the raw `anonId` (`forms.ts:296,413,463,548`) | 2 | ● |
| N-DS-5 | Erasure persists, logs and returns `emailHash` (`data-subject.ts:236,253,266`) | 2 | ● |
| N-BE-1 | Flags `?eventId=` can be read across tenants, which is OSE-1088 (`router.ts:1256,1274`, `feature-flags.ts:76,128`) | 2 | ● |
| N-BE-5 | Production needs the founder's `ose-platform` membership row, or every platform route returns 404. No gate checks it (OSE-1415/837) | 2 | ● |
| N-QA-4 | Alerting fails silently: monitoring exits 0 without a Linear key (`security-monitoring.yml:530-534`), the canary sends GitHub email only, and there is no pager | 2 | ● |
| N-QA-5 | Checks that cannot fail: `dependency-review.yml:58` and the nightly `security-regression.yml:98` are `continue-on-error`; `T4_MAX_SKIP_RATIO` is unset; the drift checks skip when the brain is absent, Dependabot included; Bruno accepts 503 `CONFIG_ERROR`/`DB_ERROR` (`POST Register.yml:67-71`); the open-redirect test asserts only `endsWith` | 2 | ● |
| N-ADV-1 | The `ose_anon` cookie is unsigned, any `anon_[A-Za-z0-9_-]+` value is accepted, and `/q/` has no rate limit. K−1 forged scans reveal whether a real person scanned, and counts can be inflated (`anonymous-id.ts:31`, `router.ts:499-502`) | 2 | ● |
| N-ADV-2 | An unauthenticated self-delete returns `deleted:N`, which tells anyone whether an email registered for an event (`forms.ts:337-347`) | 2 | ● |
| N-ADV-3 | `GET /api/v2/maps/venue-image` is an unlimited public Google Maps proxy, open to billing and quota exhaustion (`router.ts:1605-1608`) | 2 | ● |
| N-ADV-4 | `${{ github.event.workflow_run.head_branch }}` is interpolated in `run:` (`security-triage.yml:52`) | 2 | ● |
| N-ADV-5 | Cookie-auth admin writes have no Origin / `Sec-Fetch-Site` guard. The content-type check uses `includes('application/json')`. Protection rests on an unrecorded SameSite setting in Access | 2 | ● |
| G-DNS | DNS and registrar: lock, DNSSEC, CAA (OSE-1481) | 2 | ● |
| G-MAIL | SPF, DKIM and DMARC (OSE-1482) | 2 | ● |
| 1471 | Access session hardening | 2 | ● |
| 1474 | Browser-extension policy for admin | 2 | ● |
| 1476 | Session kill switch | 2 | ● |
| G3 | K-anonymity composition across dashboards and snapshots (OSE-1186 G3) | 2 | ● |
| OW-1 | OW stores tokens in plaintext when `WKRP_ENCRYPTION_KEY` is unset (`ourWKRP/src/lib/kv-storage.ts:105-111`) | 2 | ● |
| N-FE-4 | `style-src 'unsafe-inline'` on every surface | 2 |  |
| G-IR, G-TM, G-PT | IR plan and tabletop (OSE-1485), threat model (OSE-1486), external pen test (OSE-1487) | 2 each |  |
| N-FE-1, N-FE-3, N-DS-4, N-ADV-6 | Low, security. In order: tokens stay in the URL and history (OSE-1475 is the fix); no `no-store` on the admin and report shells; on the corridor dashboard, a cell total minus its published flows reveals the suppressed remainder; the OW OAuth `state` is not bound to the browser | 1 each | ● |
| N-BE-4, 1472, 1473 | Low. In order: geocode has no per-actor limit; device posture; a separate admin hostname | 1 each |  |

**Dropped in Loop 5:**
- N-FE-2: showing a token to the admin who minted it is the intended flow.
- N-SEC-2 and N-BE-3: these are a decision, not a finding. They become decision D4 and are the same fix as R2.
- G-LCL: the launch checklist is derived from this register. It is the verdict conditions in §E, not a separate item.

**Clean, with evidence (Loop 5 adversary):**
- JWT verification is RS256 only, requires `exp`, and verifies the signature before any claim is read (`auth/admin.ts:139-192`).
- Secret comparisons use `constantTimeEqual`.
- SQL binds its values.
- CORS uses an exact allowlist and sends no credentials.
- Server-side fetches go to fixed hosts.
- `DEV_OPEN_ADMIN` is refused on staging and production.
- The tree holds no secrets.
- There are no install scripts.
- The OSE-1460 export and the OSE-1416 dataset scoping are sound.

### Score

Total weight = R items 76 + S items 39 + new items 69 = **184**. Method: `awk -F'\t' 'NR>1{t+=$2} END{print t}' OCR_GATE_ADR012_register_2026-10-02.tsv` (this folder; one row per item, H=3/M=2/L=1).

Closed with evidence: S1, S2, S14 and S15 (12). R5 was reopened.

| Loop | Score | Movement |
|---|---|---|
| 4 | 14/174 = 8.0% | scope widened from 75 |
| 5 | 14/176 = 8.0% | flat; weight grew, credit did not |
| 6 | **12/184 = 6.5%** | **decay**: R5 reopened |

**Production state, read live on 2026-10-02 (Cloudflare connector, read-only queries approved by the owner):**
- `ocr-db-production`: 77 of 92 migrations applied (latest `0077_node_hierarchy_disambiguate_legal_clearance_tier.sql`), 0 events, 1 admin membership (`root:brand_owner`), **no `ose-platform` row** (N-BE-5 confirmed).
- `ocr-forms-db-production`: 14 of 15 migrations applied (missing `0015_checkin_walk_in_count.sql`), 0 registrations, 0 email signups.
- The Worker `oursharedevents-prod` exists. Its secret names could not be read through the connector, so R2's "absent" evidence still needs `wrangler secret list --env production`.
- No attendee data exists in production, so the Phase 2b migration and the Phase 6 key mint cost nothing there today.

**Vetoes:**
- **DevOps:** no production launch while R15 or R25 is open.
- **Data Science:** no public "anonymous by construction" claim, and no production scans or registrations, until N-DS-1 and N-DS-2 close and the production keys are regenerated after the token split.

## E. Solution plan to ≥95% (final, written after Loop 6)

> This replaces the Loop 1 draft. The plan is ordered so that no step depends on something a later step builds, and Loop 6's ten plan defects are folded in. Every item closes only with the evidence named in §D or §D2. "Merged" is not closing evidence: per the OSE two-stage definition (OSE-1443), a code item closes when its born-red test is on `main` **and** the T1–T4 staging chain is green for that SHA.

### E.1 What ≥95% means here

| Dimension | What it measures | Exit bar |
|---|---|---|
| **Invariants** | The product's privacy and tenancy properties hold by construction, enforced by `tests/e2e/0-architecture/*.invariant.spec.ts` in the T0 `invariants` shard | Every invariant item in the register is closed, and each has a gate that was seen to fail (born red) before the fix |
| **Code** | Worker, OW and workflow code changes | Every code item is closed, with a born-red test at the right pyramid level |
| **CI/CD pipeline** | Walls between trust zones, release path, fail-closed checks, alerting | Every CI/CD item is closed. The meta-gate (R4) proves no wall can be removed silently |
| **Test pyramid** | Two cadences. **Per merge to `main`:** levels 1–7 run and can fail (T0 gates and unit, T1 deploy, T2 Bruno, T3/T4 Playwright, then T5 red-team on the same SHA). **Nightly:** the sandbox attack suite (R9) runs the attacks that need a separate repo with test-only secrets | Per merge: levels 1–7 and T5 green on one `main` SHA, no security step uses `continue-on-error`, and every new control has a recorded red run. Nightly: the R9 suite is green on two consecutive nights and was last run by an identity other than the guard's author. A nightly run does not replace any per-merge check |
| **Overall** | §D2 method | ≥95% in **two consecutive loops** with nothing reopened, **every High security item closed**, and both vetoes lifted |

The margin is thin: at the end of Phase 7 the score is 175/184 = 95.1%. Any High item left open drops it below 95%. So the plan treats every security item as mandatory.

### E.2 Readiness by phase

Projected weight closed after each phase, assuming each item closes with its evidence. Method: for each phase, sum the weight of rows in `OCR_GATE_ADR012_register_2026-10-02.tsv` whose `phase` is that phase or earlier (`DONE` < `P0` < … < `P8`), per `dimension` and overall.

| After | Invariants (27) | Code (60) | CI/CD (39) | Test pyramid (14) | Owner/ops (44) | **Overall (184)** |
|---|---|---|---|---|---|---|
| Today | 0% | 20% | 0% | 0% | 0% | **6.5%** |
| Phase 0 | 0% | 20% | 0% | 21% | 25% | 14.1% |
| Phase 1 | 7% | 37% | 13% | 21% | 25% | 23.4% |
| Phase 2 | 37% | 37% | 13% | 21% | 32% | 29.3% |
| Phase 3 | 78% | 65% | 13% | 21% | 32% | 44.6% |
| Phase 4 | 78% | 65% | 13% | 21% | 52% | 49.5% |
| Phase 5 | 78% | 70% | **100%** | 50% | 64% | 74.5% |
| Phase 6 | **100%** | **100%** | 100% | 50% | 68% | 88.6% |
| Phase 7 | 100% | 100% | 100% | 50% | **95%** | **95.1%** |
| Phase 8 | 100% | 100% | 100% | **100%** | 100% | **100%** |

Corrected after two PR reviews: R1, R2, R12 and R19 move to Phase 5, S10 to Phase 1, and the two logging fixes (N-DS-3, N-DS-5) to Phase 1, so no phase takes credit for work a later phase does.

PASS needs Phase 8. R9, the sandbox attack run, is a High security item. The pen test and two clean loops come after it.

### E.3 Owner decisions (needed before Phase 1 ends)

Ranked by how much each unblocks. Each comes with a recommended default.

| # | Decision | Unblocks | Recommended |
|---|---|---|---|
| D1 | Give AI agents their own GitHub identity (a GitHub App or machine user with no admin and no bypass) | R16 → R4, R26, R9, R15, R17 (15 weight) | Yes. Agents commit and open PRs as the bot. The founder stays the only code owner |
| D2 | GitHub plan, and whether OCR-docs and the hub go public | R13 → R8, R15, R27; removes R1's read token | Record the plan today. If it is Free, choose between making the docs repos public (they hold no secrets) and a plan upgrade |
| D4+D5 | How production global-flag writes and erasure are authorised once the static header is gone | R2 together with S12r and S13. Without a decision, deleting the static header leaves erasure uncallable in production | Global flags: a per-environment Access service token mapped to a `key:` actor by its JWT `common_name`, used only for that route, every use audited. Erasure: **two people**. One actor requests, a different named admin approves, and only then does the job run; a single actor is refused. S12r does not close without this, because one stolen credential must not be able to erase across tenants. If only one human admin exists at launch, erasure stays a manual, recorded runbook step until a second approver exists |
| D6 | The anonymous ID in FORMS_DB | N-DS-1 (OSE-1493), N-DS-2 (OSE-923), the S13 tail, and the Data Science veto | Replace it with a per-table, per-event HMAC id (`HMAC(key, table ‖ event_id ‖ anon)`). Never store the raw cookie value. Dedupe still works inside each table for one event. Rows in different form tables, or for different events, cannot be joined on the id. For the scan split, keep no row-level WHERE record: poster scans become counters per poster per hour, and the returns table keeps event and day only, so even a single scan in an hour cannot be joined one-to-one |
| D9 | Launch posture for Oct 24 | Whether Phase 8 must finish before launch | An invited-only launch on the E.5 bar. The public "anonymous by construction" wording waits until Phase 2b merges and production keys are regenerated (D8) |
| D3 | `full-pipeline/*` PR deploys to staging | R8 | Retire them |
| D7 | `ALLOWED_ADMIN_DOMAINS` | S10 | Remove it. Allow named emails only |

### E.4 The phases

**Promotion rule (PO, 2026-10-02): production is never fixed in place.** Every code, migration, config and data change lands on `main`, is proven on staging, and reaches production only by promoting that same SHA through `deploy-production`. Production-specific values live in `[env.production]` and its secrets; they are the only thing that differs. Production is 15 migrations behind `main` (77 of 92, read 2026-10-02). It catches up through the pipeline, never by running `d1 migrations apply` by hand as was done on 2026-09-21. There are two exceptions, both containment, and each is recorded in the exposure record: deleting or revoking a credential that is already exposed, and revoking sessions.

Each phase lists its work in four lanes: invariant gates (**INV**), code (**CODE**), pipeline (**CI**) and tests by pyramid level (**PYR**, using L1 Security, L2 Lint, L3 Contract, L4 Unit, L5 Integration, L6 API/Bruno, L7 E2E/Playwright). Linear ids are in brackets.

#### Phase 0 — Owner, today, about 2 hours. Order matters.

1. **Export the GitHub org and Cloudflare audit logs first.** The OSE runbook says Cloudflare keeps audit logs for only 24 hours on the Free plan. Then write the exposure record: the two runs named in R10, the Pieces window, and every read that cannot be observed listed as "unknowable" (R10).
2. Delete production `X_OCR_INTERNAL` and `ADMIN_KEY` from Worker `oursharedevents-prod`. **Freeze production deploys until Phase 1 merges**, because the deploy gate and `smoke-production` still expect both (R2, step 1).
3. Revoke every Access session. Delete existing CI run artifacts (traces and reports) from the last 30 days, because they may hold live cookies (R19 residue).
4. Record the GitHub plan (R13). Create the production Access app (OSE-1353) and send Claude its AUD tag (an id, not a secret) (S10).
5. Rotate **in place under the same secret names**:
   - `OCR_PROPAGATE_TOKEN` gets a **new value with the same write scope and an expiry**. The trusted writers (for example `propagate-standards.yml:288,303-311`) push branches and open PRs with it, so a read-only value today would silently stop them. Splitting it into a read-only token for PR jobs and an environment-gated write token is Phase 5 work, and R1 stays open until then;
   - `CLOUDFLARE_API_TOKEN_OSE` gets an expiry;
   - the Access service token is replaced;
   - staging `ADMIN_KEY` and `X_OCR_INTERNAL` are replaced.

   Revoke the exposed old values immediately; never keep one alive to keep a job running. New names come in Phase 5, because changing names now would turn every PR red (OSE-1467).
6. Set `OCR_CI_EDGE_TOKEN` and its WAF skip rule (OSE-1490). Evidence is a green T4 run on `main`, not just the secret being set (N-QA-2).
7. 2FA on every account, recovery codes escrowed offline, and one break-glass account each on GitHub, Cloudflare and Doppler (R24, OSE-1478). The founder's `ose-platform` membership row is **not** inserted by hand: it ships as a checked-in, idempotent seed that runs on staging first and then reaches production through the pipeline (N-BE-5, OSE-1415, OSE-837).
8. Write down the admin browser policy: a dedicated profile with no extensions (OSE-1474).

Secret values are never typed into chat or a ticket. Use `printf %s "$V" | wrangler secret put …` and the hidden prompt of `gh secret set`.

#### Phase 1 — Stop the bleeding (Claude, 1–2 PRs, days 1–2)

- **CODE:**
  - `src/index.ts:54` logs the pathname only (OSE-1492).
  - `ALLOW_OCR_INTERNAL` comes out of `[env.production.vars]`. `CF_ACCESS_AUD` is pinned in production from the Phase 0 tag.
  - `ALLOWED_ADMIN_DOMAINS` is removed, so only named emails are admins (D7). Refusal tests: a valid JWT from a different Access app on the same team, and an unlisted mailbox on the domain, are both refused (S10).
  - The two known logging leaks are removed here, before the gate below turns on: `anonId` in `logFormEvent` (OSE-1494) and `emailHash` in the erasure log, audit row and response (OSE-1495).
  - `set-secrets.sh` stops provisioning a production `ADMIN_KEY`, and the deploy gate asserts the static secrets are **absent** (R2, S10).
  - `security-triage.yml` passes the branch name through `env:` (OSE-1499).
  - `robot-knowledge` takes its inputs through `env:`, in its own repo (R22).
  - Doc corrections: the CLAUDE.md §4 fallback line, the OSE-1080 line, and the SEC-2.1 / SEC-1.2 status lines (R5, OSE-1402). These are governance edits and need human review.
- **INV:** new gates:
  - `prod-config.invariant`: no `ALLOW_OCR_INTERNAL`, `ALLOW_ADMIN_KEY_FALLBACK` or `ADMIN_SCOPE_ALL` in production vars, and a non-empty `CF_ACCESS_AUD`.
  - `log-redaction.invariant`: no `request.url`, `anonId`, `emailHash` or token-shaped field in any `console.*` call.
  - `workflow-injection.invariant`: no `${{ github.event.* }}` or `${{ inputs.* }}` inside `run:`, fleet-wide. The existing cases are converted to `env:` in the same change, before the gate blocks: OCR-docs `propagate-standards.yml:131` and `docs-ci.yml:31`, OSE `force_clean` (×10) and `deploy-spoke`'s `inputs.environment`, OSE `security-triage.yml:52` and `robot-knowledge`. A repo whose cases are not yet converted runs the gate in report mode, never silently skipped.
- **CI:**
  - Trace, video and HTML-report embedding are off in every Playwright config or spec that sends a credential.
  - An **artifact secret scan** runs before every `upload-artifact` and fails if a secret value, a `CF_Authorization` cookie or a `Bearer` header appears.
  - `smoke-production` moves into `environment: production`, runs read-only on the production Access token, and the release runbook is updated (R19, OSE-1470).
- **PYR:** each gate is L1/L2, and each was seen red. One sandbox run fails a test on purpose, and its downloaded artifact is scanned clean (L7).
- **Closes:** R5, R22, S10, N-SEC-1, N-ADV-4, N-DS-3, N-DS-5. R2 and R19 are code-complete here but close in Phase 5: R2 needs the per-environment tokens (R25) and the production Access token on `smoke-production`; R19 needs top-level `permissions:` fleet-wide and the clean sandbox artifact. Production deploys unfreeze.

#### Phase 2 — Anonymity by construction (Data Science veto), days 2–7

2a, additive and safe on live data:
- **CODE:**
  - The `ose_anon` cookie is HMAC-signed by the server; an unsigned or forged value is reissued, never trusted.
  - `/q/` and `/s/` get a rate limit keyed on a peppered IP hash plus the event (OSE-1496).
  - Signing alone does not stop someone from dropping the cookie and taking a fresh one. So the privacy floor does not rely on cookie dedupe. Each peppered IP hash counts at most once per poster per hour, and published scan counts are rounded down to multiples of 5, as the export already does. One real scan then cannot be told apart by adding K−1 scans of your own.
  - New scan writes stop storing a second-precision `created_at`. The WHERE side is written as a counter per poster per hour, not a row per scan; the WHO side (`scan_node_returns`) keeps event and day only.
  - `scan_node_returns` retention defaults to 90 days, keyed on `scan_bucket`.
  - Erasure covers `form_surveys` and `checkin_counts`.
- **Prerequisite for 2b** (OSE-1503):
  - Fix the DR and rollback runbooks: no `d1 delete`, Time Travel first, exports encrypted and outside the repo, `backup/` in `.gitignore`.
  - A durable erasure ledger that survives a database restore: one record per erasure (no PII, just the peppered subject key and a timestamp), kept outside the database being restored. After any restore, the ledger is replayed before restored data is served, then the lifecycle scrub and the pepper-epoch purge run. A lifecycle scrub alone is not enough, because it removes only expired rows.
  - The drill includes a registration that was erased but whose retention has not expired, and proves it stays gone after the restore.
  - Run one staging restore drill and record its RPO and RTO.

2b, destructive, and only after D6 and the drill:
- **CODE:**
  - A forward-only migration replaces the FORMS_DB `anonymous_id` columns with the per-table, per-event HMAC id and scrubs existing rows.
  - Existing rows move to the new shape: placement rows fold into per-poster-hour counters and are deleted, and `scan_node_returns` keeps event and day only (OSE-1493, OSE-923). Truncating both tables to the same hour is not enough: an event with one scan in that hour would still join one-to-one.
  - Production holds 0 events, so production is a no-op. Staging runs after a Time Travel bookmark is recorded.
- **INV:**
  - New `anon-linkage.invariant`, as a property test. Seed both databases through the real handlers, then assert that no FORMS_DB column equals any main-DB `anonymous_id`, that no join can link the two scan sides one-to-one, including for an event with a single scan in an hour (a singleton case is in the seed), and that the same browser registering, checking in and answering a survey for one event leaves ids that differ across the three tables.
  - Extend `anonymous-id` to require a signed cookie, and extend `scan-path-split` to cover timestamps.
- **PYR:**
  - L4: the HMAC id and the truncation.
  - L5 (workers pool):
    - a forged cookie cannot create a second dedupe bucket;
    - K−1 forged scans cannot reveal one real scan;
    - dropping and re-taking the cookie repeatedly cannot add more than one count per IP per poster per hour, and cannot reveal one real scan;
    - erasure leaves no row holding the id.
  - L3: a schema snapshot.
  - L7: staging scan → register, then read back that the stored id is not the cookie.
- **Closes:** N-DS-1, N-DS-2, N-ADV-1, N-DO-5. Lifts half of the Data Science veto; the other half is the Phase 6 key mint.

#### Phase 3 — Admin requests, erasure, audit (days 3–8, in parallel with Phase 2)

- **CODE, erasure:**
  - Erase needs two people (D4+D5): a request by one admin and an approval by a different named admin. A refusal test shows a single actor, the break-glass service token included, cannot both request and approve.
  - It becomes a persisted erasure job that reports `ok:false` with its errors when any phase fails, and covers every table (OSE-1458).
  - Self-delete returns the same response whether or not anything was deleted, and needs a mailed confirmation (OSE-1497).
- **CODE, requests:**
  - A CSRF guard on every non-GET admin and sponsor route: `Sec-Fetch-Site` must be `same-origin` or `none`, or `Origin` must be on the allowlist, and the content type must be exactly `application/json` (OSE-1500).
  - Flags `?eventId=` goes through the object-scope guard (OSE-1088).
  - `no-store` on the admin and report shells (OSE-1502).
  - The Maps proxy goes behind `publicReadLimited` and serves only venues of published events (OSE-1498). Geocode gets a per-actor limit (OSE-1504).
- **CODE, audit:**
  - Triggers reject UPDATE and DELETE on `admin_audit_log` and `pii_audit_log`.
  - Scoped-404 probes are audited, rate-limited.
  - A failed audit write raises an alert.
  - IP retention is masked after 90 days.
  - GET auditing becomes consistent (S4–S8).
- **INV:**
  - `csrf-guard.invariant`: every state-changing admin route is behind the guard, derived from the router.
  - `public-read-limit.invariant`: every public GET is wrapped or explicitly allowlisted.
  - `erasure-completeness.invariant`: every column named like `anonymous_id`, `email_hash` or `attendee_*` is in the erasure map.
  - `audit-immutability.invariant`.
- **PYR:**
  - L1: a refusal test per route.
  - L5: an erasure fault injection must return `ok:false`.
  - L6: Bruno cases for CSRF refusal and the constant self-delete response.
- **Closes:** S4–S8, S12r, S13, N-BE-1, N-BE-4, N-ADV-2, N-ADV-3, N-ADV-5, N-FE-3.

#### Phase 4 — Agent identity (owner and code, week 2)

- **Owner:**
  - Create the bot identity (D1).
  - Turn on "Require review from Code Owners", with the founder as the only human owner.
  - Snapshot each session type's tool list: unattended routines get no D1 delete or query, no merge and no workflow trigger (R16, R17, R26, OSE-1488, OSE-987).
- **CI:** a meta-gate fails when `codeowners/errors` is non-zero or when the owner named is the bot.
- **Closes:** R16, R17, R26.

#### Phase 5 — CI/CD walls (week 2)

- **CI, release path:**
  - Remove the `v*` tag trigger. Production is released by `workflow_dispatch` on `main` only.
  - `staging`, `staging-deploy` and `production` each admit `main` only. `full-pipeline/*` deploys are retired (D3).
  - Every dispatchable workflow that holds a Z1+ secret runs in an environment.
  - `RUNBOOK-DEPLOYMENT.md` is updated in the same PR (R8, R15, R27).
- **CI, tokens:**
  - Wire `CF_DEPLOY_STG`, `CF_DEPLOY_PRD` and a D1-only staging test token, each expiring and kept in its environment. Then revoke `CLOUDFLARE_API_TOKEN_OSE`.
  - D1 seeding moves into the deploy job.
  - The write PAT is split for the three trusted writers (R1, R11, R25).
- **CI, fleet:**
  - `persist-credentials: false` and the shared guard action in OW, OA, OSG, OSM, OSP, OSR, OCR-docs and the hub, each born red.
  - `brain-location-audit` is fixed.
  - Self-hosted runners never take PR code (R3, R18).
- **CI, hygiene:**
  - Top-level `permissions: {}` in every workflow.
  - Third-party actions pinned by SHA (R29).
  - The LLM review job runs on `pull_request` only, with secrets through `env:` (R21).
  - Long-lived Z0 secrets are removed from PR jobs or recorded as dated exceptions (R28).
- **CI, fail closed (N-QA-5):**
  - `dependency-review` blocks on high and critical (OSE-1489).
  - The nightly security regression can go red.
  - `T4_MAX_SKIP_RATIO` is set.
  - Drift checks fail when the brain is missing, Dependabot included (OSE-1126).
  - Bruno's `CONFIG_ERROR`/`DB_ERROR` tolerance is removed (OSE-1348).
  - The open-redirect test asserts the exact same-origin `Location` (OSE-1125).
- **CI, alerting (N-QA-4, R14, OSE-1484):**
  - A missing Linear key turns monitoring red.
  - The canary posts to Linear and a webhook.
  - An expiry-warning job runs at 21 and 3 days.
  - A production-credentials canary runs.
- **INV:** the `workflow-walls.invariant` meta-gate parses the YAML. It fails on:
  - a missing guard step;
  - `continue-on-error` on a security step;
  - a tag-triggered deploy;
  - a credential job with no environment;
  - a top-level `permissions` block missing.

  Its fixtures live in a separate file (R4).
- **PYR:** each wall is born red against the old workflow. The sandbox repo is created here for Phase 8.
- **Doppler isolation (R12), before any production key is minted:** a throwaway-secret test shows CI and deploy configs do not carry runtime data keys, and a bulk-upload denylist stops a sync from overwriting them.
- **Closes:** R1, R2, R3, R4, R8, R11, R12, R14, R15, R18, R19, R21, R25, R27, R28, R29, N-QA-4, N-QA-5. Lifts the DevOps veto.

#### Phase 6 — Keys, roles, composition (week 3)

- **CODE, keys:**
  - Pepper versioning (an epoch column) for `FORMS_HASH_PEPPER` and `IP_HASH_PEPPER`.
  - A boot-time key check: at least 32 bytes, distinct values, fail closed in staging and production.
  - No unpeppered fallback for rate-limit keys.
  - `requirePepper` on self-delete, and no bare SHA-256 in production (R6).
  - One signing secret per link kind, with a `kid` and previous-value overlap, a capped `exp`, and a `jti` with a revocation table for sponsor and report links (R20, R23).
  - The admin rate limit also runs on staging, not only production, with a test (R23).
- **Owner (R23):** WAF or rate-limit rules for the admin, sponsor and forms routes, recorded with their thresholds.
  - URL tokens are replaced by a one-time code redeemed into an `HttpOnly` cookie (OSE-1475, N-FE-1).
- **Owner:** mint the production keys **after** the token split and the R12 isolation test, while production still has 0 events, so the pepper reset costs nothing. This lifts the other half of the Data Science veto.
- **CODE, rest:**
  - Roles enforced on destructive brand actions (S3).
  - `If-Match` concurrency on admin writes (S9).
  - An audit viewer (S11).
  - Style nonces (N-FE-4, OSE-1391).
  - Access session length and re-auth (OSE-1471).
  - A kill-switch route and runbook (OSE-1476).
  - OW refuses to store tokens without its key, and binds OAuth `state` to a cookie (OW-1, OW-155).
  - Corridor-dashboard complementary suppression (N-DS-4, OSE-1468).
- **INV:**
  - `secret-hygiene.invariant`: strength, distinctness and `kid`.
  - A gating fast-check **K-anonymity composition** property across dashboards, snapshots and exports: no difference of two published views lands in 1–4 (G3, OSE-1186).
- **Closes:** R6, R20, R23, S3, S9, S11, N-FE-1, N-FE-4, N-DS-4, N-ADV-6, OSE-1471, OSE-1476, G3, OW-1.

#### Phase 7 — Platform hardening (owner, week 3)

- Per-environment WIF subject, with IAM bound per subject. Code sets the `sub` per environment (R7, OSE-61 rewritten).
- GitHub org baseline (OSE-1479).
- DNS: registrar lock, DNSSEC, CAA (OSE-1481).
- Mail: SPF, DKIM, DMARC (OSE-1482).
- Device posture and the admin hostname are optional (OSE-1472, OSE-1473).
- **Score after Phase 7: 175/184 = 95.1%.**

#### Phase 8 — Prove it (week 3 onward)

- Sandbox red-team repo with test-only secrets. The nightly attack suite covers:
  - a tag on an off-`main` commit carrying an edited workflow;
  - a dispatch from a feature branch;
  - an agent-identity attack;
  - artifact leakage;
  - the forged-cookie and CSRF attacks.

  It records its born-red and green runs, and is run by an identity other than the guard's author (R9).
- Threat model (OSE-1486).
- IR plan and tabletop on the leaked-CI-token scenario (OSE-1485).
- External pen test (OSE-1487).
- Then two CCR loops at ≥95% with nothing reopened. **That is PASS.**

### E.5 Launch posture for Oct 24 (decision D9)

PASS cannot be reached by Oct 24: the sandbox run, the pen test and two clean loops need more than 22 days.

**An invited-only launch is defensible only when all of these are closed with evidence:**
- Phase 0;
- Phase 1;
- Phase 2a and 2b;
- the erasure items of Phase 3, including two-person approval (S12r);
- R1, R2, R11, R12, R15, R19 and R25 from Phase 5;
- the Phase 6 key mint.

Until Phase 2b merges and production keys are regenerated, the public "anonymous by construction" claim stays off every surface.

### E.6 Tracking

Every item in §D and §D2 has a Linear ticket under OSE-1477, or a comment on the existing ticket that owns it. Each phase is tracked as a group of those tickets. The score is re-derived at the end of each phase. A review loop is run when Phase 3 merges, as supplemental analysis. The next **protocol** loop (Loop 7) runs only after a recorded human resolution of the gate gaps, not on a merge alone.

## F. Owner decisions that change the path

> Superseded by §E.3 for Loops 4-6; kept for history. Decision 5 is D2 there and decision 6 is D3.

- **Decision 5 (make OCR-docs and the hub public):** removes R1's read token entirely, and the Apps/Packages migration.
- **Decision 6 (`full-pipeline/*` PR deploys):** they cannot keep credentials under ADR-012, because PR code is Z0. The choice is retire them, or rebuild them as a credential-free preview flow (a separate zone, no secrets). Either way R8 admits `main` only.
- **R13 (plan):** if the org is on Free, private-repo environments and rulesets are limited. Then the wall becomes repo visibility, or a plan upgrade, which is a cost decision under ADR-006.
