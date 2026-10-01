# CCR Gate Review — ADR-012: secrets by trust zone (credential isolation)

> **Verdict:** **HELD (in progress: Loop 1 of 5 complete).** The design is right, and every lens agreed on that. It is not launch-ready: a write-capable token is still live, production admin may accept a static header, production data keys would be reachable through a deploy-capable token, and the tests are static only.
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
| 2 | Conservative: what did Loop 1 assume but never verify; what did all lenses miss? | Verifier + adversary | *running* | | |
| 3 | Recursive: is the register complete and stable? Is any confidence inflated? | — | | | |
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
- **Cut:** required reviewers as a precondition. For one owner, a self-approval is a click; the wall is branch and tag rules.

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

## C. Corrections applied in this change (reactive correction)

- **Inventory exposure record:** "not exposed" now says the data keys were not stored in GitHub, but were reachable through the Workers-edit token by deploying code. Production keys minted before the token split count as exposed (S2/D1).
- **Inventory §2.3 and finding 8:** the `FORMS_ENCRYPTION_KEY` keyring exists, so its rotation path is re-encrypt then retire, not data loss (D4). `FORMS_HASH_PEPPER` falls back to bare SHA-256 (D3).
- **Standard §2:** peppers rotate on compromise only, until hashes are versioned (D5).
- **Standard §3:** Doppler isolation uses **root environments or separate projects**, not branch configs (O4). `wrangler secret bulk` gets a data-key denylist (S5).
- **Standard §5:** expiry is a scheduled warning issue, not a merge blocker (O5).
- **Inventory §3 Phase 1:** the `staging` environment's branch rule must admit the release-tag path (O1). The rollout order and the D1-seeding move are added (O2, O3).

## D. Risk register and score

**Method (re-derivable):**
- Each hold has a weight: High = 3, Medium = 2.
- Credit: **closed with evidence** = 1. **Mitigated with an owner-signed documented assumption** = 0.5, for non-security items only. **Open** = 0.
- Security items get **no partial credit** (CCR v3, Security Critical tier).
- **Score = credit ÷ total weight.**
- Per the protocol, PASS also needs the score to hold across **two consecutive loops**.

| # | Hold | Wt | Sec | Today | Closes when (evidence) | Who | Tranche |
|---|---|---|---|---|---|---|---|
| R1 | Live write-capable PAT (S1) | 3 | ● | open | Old token deleted (date recorded). PR jobs use a read-only expiring token. Writers use a separate token only in trusted workflows. Guard allowlist updated | owner + code | B |
| R2 | Production static admin path (S3) | 3 | ● | open | Production `X_OCR_INTERNAL` absent. `ALLOW_OCR_INTERNAL` off with a config test. Production smoke on the production Access token. Refusal test green | owner + code | A+B |
| R3 | Persisted checkouts and PR-sourced `workflow_run` (0.1, 0.2) | 3 | ● | in #743 | #743 merged with CI green. The same fix lands in OW, OA, OSG, OSM, OSP, OSR and OCR-docs | code | A |
| R4 | Gate anti-weakening (T3) | 3 | ● | open | CODEOWNERS covers the guard, allowlist, spec and CI steps. A meta-gate fails if the guard or self-test step is removed or made `continue-on-error`. Fixtures in a separate file. "Require Code Owners review" confirmed on | code + owner | A+B |
| R5 | Doc overclaims and drift (S2, D4, D5, O4, O5) | 3 | | **closed by this change** | §C corrections merged | code | A |
| R6 | Production data keys (S2, D1, D3) | 3 | ● | open | Fresh production keys minted **after** the Cloudflare split, from a production-gated step. A launch check passes (present, distinct from staging by fingerprint, minimum length). Production refuses to hash without `FORMS_HASH_PEPPER` | code + owner | A+B |
| R7 | BigQuery principal shared across environments (D2) | 3 | ● | open | A distinct `sub` per environment, IAM bound per subject (verified in GCP), `bigquery.readonly` dropped | code + owner | A+B |
| R8 | Rollout order and the tag path (O1, O2) | 3 | | open | Runbook written. The `staging` rule admits `main` plus release tags. Environment copies are proven green before repo secrets are deleted | code + owner | A+B |
| R9 | Test-pyramid gap (T1, T2, T4, T6) | 3 | ● | open | **Offline** dynamic PR tests (a local-repo credential-persistence test; a `workflow_run` simulator over an adversarial branch corpus). A nightly sandbox attack run with a written spec. The prompt-injection class added. Born-red runs recorded as artifacts | code + sandbox | A+C |
| R10 | Exposure record and audit-log limits (D6) | 3 | ● | open | GitHub and Cloudflare audit logs reviewed. Any reads that cannot be observed are recorded as "unknowable". Record closed, dated | owner | B |
| R11 | D1 seeding versus test-job zones (O3) | 2 | | open | Seeding moves into the `staging-deploy` job, or test jobs use a D1-only staging token | code | A |
| R12 | Doppler isolation verified (O4, S5) | 2 | | open | A throwaway-secret test shows CI and deploy configs do not carry runtime keys. Bulk denylist in place | owner + code | B |
| R13 | GitHub plan and visibility (O6) | 2 | | open | `gh api orgs/ourCommunityRituals --jq .plan.name` recorded, and the plan's limits written into the standard | owner | B |
| R14 | Expiry and canary operations (T5, O5) | 2 | | open | A scheduled expiry-warning job opens issues at 21 and 3 days. A break-glass runbook. A production-credentials canary (`workflow_dispatch`, `CF_READ`) | code | A |

Total weight = 10×3 + 4×2 = **38**.

**Score today: 3 / 38 = 8% readiness** (R5 only, closed by this change).

The *design* is not what is scoring low here. All four lenses kept the model; the open items are execution and verification.

## E. Solutioning to 95% — DRAFT (input to Loops 4-5; finalized after Loop 5)

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
