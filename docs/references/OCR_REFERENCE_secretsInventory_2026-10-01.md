# Secrets inventory and migration plan — 2026-10-01

> **What this is.** A dated snapshot of every credential the fleet uses, the zone each belongs in under ADR-012, where it lives today and where it moves, plus the phased plan.
> **Names only.** No value appears here or was read. GitHub secret *values* are not readable through the API, and none were requested.
> **Method.** Read-only scans of each repo at `main` on 2026-10-01 (OSE at `d0a7e21`, the rest at their `origin/main`):
>
> - `.github/workflows/*`, `wrangler.toml`, `doppler.yaml`, provisioning scripts, docs;
> - Worker code reading `env.*`;
> - a YAML scan for checkouts that persist a token, and for action pins and `permissions:` (script at the end).
>
> What a secret *can* do at its provider (its real Cloudflare or GitHub scope) is taken from repo docs. It was **not** read from the provider dashboards.

---

## 1. Fleet at a glance

| Repo | Workflows | Third-party actions tag / SHA | Workflows with no top-level `permissions:` | Secrets in workflows |
|---|---|---|---|---|
| ourSharedEvents | 28 | 4 / 2 | 9 | 16 |
| ourWKRP | 6 | 3 / 1 | 5 | 5 |
| OCR-docs | 10 | 0 / 0 | 3 | 2 |
| hub (ourCommunityRituals) | 5 | 0 / 2 | 4 | 1 |
| OA, OSG, OSM, OSP, OSR | 3 each | 0 / 0 | 1 each (`docs-ci.yml`) | 2 each |
| OER | 1 | 0 / 0 | 0 | 1 |
| robot-knowledge | 1 | 0 / 0 | 1 | 1 |

First-party `actions/*` references are on tags everywhere except the hub (18 of 19 SHA-pinned). The standard allows first-party tags.

### Findings, most severe first

1. **The write-capable org PAT `OCR_PROPAGATE_TOKEN` is readable from pull-request code.**
   - 33 workflow files reference it.
   - **18 checkouts in 10 PR-triggered workflow files across 8 repos persist it** for later steps. Older `actions/checkout` versions write it into `.git/config`; v6+ keep it in a credentials file under `$RUNNER_TEMP` that later steps can still read. The 10 files:
     - `brain-contract-check.yml` in OSE, OW, OA, OSG, OSM, OSP, OSR;
     - `oursharedevents-ci.yml` `gate-tests-sub`;
     - `inv22-cross-repo-gate.yml` (OSE);
     - `OCR-docs/brain-location-audit.yml` (8 checkouts).
   - **In two of them, pull-request code or a PR-lockfile install runs later in the same job:** `gate-tests-sub` (`npm ci` at `oursharedevents-ci.yml:936`, tests at `:950`) and `brain-location-audit.yml`. The other eight run only OCR-docs `main` scripts and read the PR as data.
   - All ten are exposed anyway, because a same-repo PR controls the workflow file (Standard §1.1). Persisting the token adds a second path, through dependencies.
2. **OSE production reads staging values.** Doppler `oursharedevents/stg` syncs to OSE *repository* secrets (`docs/doppler/CF-ACCESS-SECRETS-SOURCE-OF-TRUTH.md:23-24,36`). The `production` environment's gate (`oursharedevents-ci.yml:2171`) therefore guards no distinct secret. `smoke-production` (`:2342`) has no environment at all.
3. **One Cloudflare token (`CLOUDFLARE_API_TOKEN_OSE`) covers deploy and D1 writes for staging and production.** It is a repository secret, so it is reachable from any same-repo PR.
4. **Production accepts a static admin header.** `ALLOW_OCR_INTERNAL = "true"` sits in `[env.production.vars]` (`workers/oursharedevents/wrangler.toml:324`). If `X_OCR_INTERNAL` is set on the production Worker, that header is a production admin credential that bypasses Cloudflare Access. If it is unset, the check refuses everyone (`src/auth/admin.ts:269-273`).
5. **Three `workflow_run` workflows run pull-request code with secrets:** `red-team-adversarial.yml:23-60`, `security-finale.yml:32`, `post-t6-security.yml:33`.
   - They check out `head_sha` for `pull_request` runs on `full-pipeline/*` branches, and inject `ADMIN_KEY`, `CF_ACCESS_*` and `OCR_PROPAGATE_TOKEN`.
   - A `workflow_run` job runs with the default branch as its ref, so a `main` branch rule on an environment does **not** stop it.
   - A same-repo check only stops forks. Any branch author, agents included, can name a branch `full-pipeline/*`.
6. **Script injection in `robot-knowledge/.github/workflows/robot-commit.yml:28-50`.** `workflow_dispatch` inputs are interpolated into the shell next to `ROBOT_PAT`. Only someone who can dispatch can exploit it.
7. **Third-party actions on tags with secrets in scope:**
   - `dopplerhq/cli-action@v3` (OW, with `DOPPLER_TOKEN_*`);
   - `anthropics/claude-code-action@v1` (OW);
   - `dorny/test-reporter@v3` ×3 (OSE, `checks: write`);
   - `step-security/harden-runner@v2` (OSE).
8. **11 OSE Worker secrets are outside `scripts/set-secrets.sh`**, which provisions only 4 (`ADMIN_KEY`, `FORMS_ENCRYPTION_KEY`, `FORMS_HASH_PEPPER`, `SHARED_REPORT_SIGNING_SECRET`).
   - The 11 are the §2.3 names, other than those four and the `LINEAR_TEAM_ID` identifier. The `ADMIN_TOKEN` alias of `ADMIN_KEY` (`src/auth/admin.ts:211`) makes 12 names.
   - Each is read by `workers/oursharedevents/src/` (grep for `env.<NAME>`). None of them has a rotation procedure.
   - `SPONSOR_INVITE_SIGNING_SECRET`, `ADMIN_BRAND_MEMBERSHIP` and `ADMIN_TOKEN` are not listed in `wrangler.toml` at all. Rotating `FORMS_ENCRYPTION_KEY` is documented as destroying data (`docs/runbooks/RUNBOOK-SECRETS.md:106-107`).
9. **OW declares Last.fm credentials as empty `[vars]`** (`wrangler.toml:95-96,155-156`). Doppler cannot deliver them there, and `wrangler secret put` collides with the var name.
10. **Hygiene:**
    - a URL stored as a secret (`STAGING_BASE_URL`);
    - a duplicate admin secret (`STAGING_ADMIN_KEY` vs `ADMIN_KEY`);
    - `OSE_ADMIN_BEARER`, unset since May;
    - stale `ADMIN_KEY_ROOT` still marked required in `.github-secrets-required.json`;
    - dead GAS/Sheets names in `.github/workflow-archive/`;
    - no repo has `.github/dependabot.yml`, although two docs say "bump via Dependabot".

### Exposure record (opened 2026-10-01)

The findings above describe paths by which **real credential values** could be read. Names alone are not the issue. This record stays open until every item below is closed.

| | |
|---|---|
| **What** | `OCR_PROPAGATE_TOKEN` (write-capable, every repo in the org). OSE `CLOUDFLARE_API_TOKEN_OSE` (deploy + D1 read/write, staging and production). OSE `ADMIN_KEY`, `X_OCR_INTERNAL`, `CF_ACCESS_CLIENT_ID/SECRET`. OW `DOPPLER_TOKEN_STG/PRD` and `ANTHROPIC_API_KEY` through tag-pinned actions. `ROBOT_PAT` through script injection |
| **To whom** | Anyone who can push a branch to these repos (including agent sessions). Code that runs in those jobs: PR test code, dependencies installed from a PR lockfile, tag-pinned third-party actions. **Not** fork pull requests, which receive no secrets |
| **How long** | Not established. The persisted checkouts and repo-level secrets date back at least to the workflows' creation. The scheduled conformance runs show the PAT in use since at least 2026-08-30 |
| **What was not exposed** | The keys that protect stored personal data (`FORMS_ENCRYPTION_KEY`, the hashing peppers, the signing secrets) exist only as Worker secrets, never in GitHub. A database read through the Cloudflare token would return ciphertext and hashes. Production held 0 events and has never had real users (CLAUDE.md §3 DevOps) |
| **Evidence of misuse** | **Unknown.** The scans read code, not audit logs |
| **Open actions (owner)** | 1. Rotate `OCR_PROPAGATE_TOKEN` and **delete** the old token (Phase 1.1). 2. Check whether the production Worker has `X_OCR_INTERNAL` set; delete it if so. 3. Review the GitHub org audit log and the Cloudflare account audit log for unrecognised pushes, branches, PRs, deploys or D1 queries. 4. Record the outcome here, dated. 5. Rotate the Cloudflare, admin and Access credentials as per-environment values (Phase 1.3-1.5) |

---

## 2. Per-secret map

Zone per ADR-012. "Today" is where the value is held now; "Target" is where it moves.

### 2.1 Org and CI identity

| Secret | Repos | Today | Zone | Target | Phase |
|---|---|---|---|---|---|
| `OCR_PROPAGATE_TOKEN` (reads) | all 10 | org secret, classic or fine-grained PAT, write-capable | Z0 today; must leave Z0 | PR jobs: hub packages from GitHub Packages via `GITHUB_TOKEN`; brain checks as trusted `workflow_run` checks. Trusted jobs: `ocr-ci-reader` App token from environment `ci-read` | 1 |
| `OCR_PROPAGATE_TOKEN` (writes: propagate-standards, conformance PR) | OCR-docs, OSE | same PAT | Z4 | `ocr-automation` App token in environment `automation` | 1 |
| `OCR_PROPAGATE_TOKEN` (OSM issue) | OSE `notify-osm-flag-change.yml:45` | same PAT | Z4 | `ocr-automation`, `issues: write` on OSM only | 1 |
| `LINEAR_API_KEY`, `LINEAR_TEAM_ID` | OSE, OW, OCR-docs, 5 spokes; OSE Worker | repo secrets; personal key | Z1 for the drift-ticket bots (they run on PRs today) | a Linear **bot/app key**, not a personal key, synced from `ocr-platform`; PR-time ticketing moves to a `push`/`schedule` job | 2 |
| `ANTHROPIC_API_KEY` | OSE, OW | repo secret | Z0 by **recorded exception** (review bots run on PRs by design) | exception with `exception_until` and a spend limit and 90-day rotation; then OIDC federation (OW `claude.yml:43-47`, OSE-1109) or a trusted `workflow_run` review | 1 |
| `BRANCH_PROTECTION_READ_TOKEN` | OSE `oursharedevents-ci.yml:2500` | repo secret | Z0 | move the branch-protection audit to a trusted job (push/schedule) using `ocr-ci-reader` with `administration: read` on OSE; it cannot stay in a PR job | 2 |
| `ROBOT_PAT` | robot-knowledge | repo secret, user PAT | Z4 | `GITHUB_TOKEN` with `contents: write` (same repo), and fix the injection | 0 |

### 2.2 ourSharedEvents CI

| Secret | Today | Zone | Target | Phase |
|---|---|---|---|---|
| `CLOUDFLARE_API_TOKEN_OSE` | repo secret (Doppler `stg` sync); deploy plus D1 for both environments | Z2/Z3 | `CF_DEPLOY_STG` (env `staging-deploy`) and `CF_DEPLOY_PRD` (env `production`), each expiring in ≤90d; `CF_READ` for `secret list` and the canary | 1 |
| `CLOUDFLARE_ACCOUNT_ID` | repo secret | not secret | repository **variable** | 2 |
| `ADMIN_KEY` | repo secret (stg value); also sent by `smoke-production` | Z1 | env `staging` only. Production smoke uses the production Access service token | 1 |
| `X_OCR_INTERNAL` | repo secret; prod Worker accepts it (`ALLOW_OCR_INTERNAL=true`) | Z1 | env `staging` only. Production: flag off, secret deleted | 1 |
| `CF_ACCESS_CLIENT_ID` / `_SECRET` | repo secret; one value used against staging and production | Z1 / Z3 | one Access service token per environment, in env `staging` / `production`, shortest duration offered, rotated every 90 days | 1 |
| `OCR_CI_EDGE_TOKEN` | **missing** (main's T4 is red) | Z1 | env `staging`, plus a WAF skip rule for `stg` `/q/*` with header `X-OCR-CI` | 1 |
| `STAGING_ADMIN_KEY` | repo secret, duplicate of `ADMIN_KEY` | Z1 | delete; use `ADMIN_KEY` from env `staging` | 2 |
| `STAGING_BASE_URL` | repo secret | not secret | repository variable | 2 |
| `OSE_ADMIN_BEARER` | repo secret, unset since May | Z1 | delete, or env `staging` if the mobile audit needs it | 2 |
| `SECURITY_WEBHOOK_URL` | repo secret | Z1 | env `staging` / a monitoring environment | 2 |

### 2.3 ourSharedEvents Worker runtime (Z5)

All move to "**written from Doppler `stg` / `prd` by the deploy job, listed in the manifest, a distinct value per environment**" in Phase 2. The extra column is what each needs before it can be rotated safely.

| Secret | Class | Needs before rotation |
|---|---|---|
| `ADMIN_KEY` / `ADMIN_TOKEN` | shared auth | current + previous overlap; off in production (§6) |
| `X_OCR_INTERNAL` | shared auth | off in production |
| `OSE_INTERNAL_BATCH_TOKEN`, `WKRP_SERVICE_TOKEN` | service auth | current + previous overlap; per-caller logging |
| `FORMS_ENCRYPTION_KEY` | data key | keyring with a `v<n>:` ciphertext prefix and re-encrypt job (INFRA-4) |
| `FORMS_HASH_PEPPER` | data key | versioned hashes (data-subject lookup tries every live version) |
| `ANON_ID_HASH_PEPPER` | data key | already versioned: `pepper_epoch`, migration 0091 |
| `IP_HASH_PEPPER` | data key | versioned hashes |
| `SHARED_REPORT_SIGNING_SECRET`, `SPONSOR_INVITE_SIGNING_SECRET` | data key | `kid` in the signed token; verify against current + previous |
| `WIF_PRIVATE_KEY_PEM` | root (Worker's OIDC signing key for GCP) | publish two keys in the JWKS during rollover |
| `TURNSTILE_SECRET`, `GOOGLE_MAPS_API_KEY` | API key | 90d calendar, provider restrictions (referrer/API limits for Maps) |
| `LINEAR_API_KEY` / `LINEAR_TEAM_ID` | API key | bot key (2.1) |
| `ADMIN_BRAND_MEMBERSHIP` | unclear (store unknown) | confirm whether it is a secret at all |

### 2.4 ourWKRP

| Secret | Today | Zone | Target | Phase |
|---|---|---|---|---|
| `DOPPLER_TOKEN_STG` / `_PRD` | **environment** secrets, step-scoped in env-gated deploy jobs | Z2 / Z3 | **already the target pattern.** Add: expiry on each service token; pin `dopplerhq/cli-action` by SHA; required reviewer on `production` | 0 / 1 |
| `CLOUDFLARE_API_TOKEN` (in Doppler `stg` / `prd`) | Doppler only | Z2 / Z3 | confirm stg and prd are **different** tokens with an expiry | 1 |
| `OSE_INTEGRATION_TOKEN`, `WKRP_ADMIN_TOKEN`, `WKRP_ENCRYPTION_KEY` | Worker secrets, set by hand (`doppler run` does not set Worker secrets) | Z5 | written from Doppler by the deploy job (`wrangler secret bulk`); keyring for `WKRP_ENCRYPTION_KEY` | 2 |
| `LASTFM_API_KEY`, `LASTFM_SHARED_SECRET` | empty `[vars]` | Z5 | remove from `[vars]`; Worker secrets from Doppler | 2 |
| `ANTHROPIC_API_KEY` | repo secret; `claude-code-review.yml:42` puts it in a `run:` script | Z0 | as 2.1; move the presence check to `env:` | 0 |

---

## 3. Phased plan

Credential isolation is part of the privacy promise, not an ops appendix. If someone can change the code that enforces never-who, or read the data stores, the promise does not hold, however well the code behaves. So every fix ships **paired with the red-team test that proves it**, and the set is a launch gate.

### Ground rules for every pair

- **Born-red:** the test is written first and shown succeeding *as an attack* against today's `main`. Then the fix lands and the same test fails as an attack, which means it passes as a gate.
- **Mutation-checked:** each test is shown to go red when its fix is reverted or weakened, so it cannot pass vacuously.
- **Wired and blocking:** named in a CI workflow and blocking. A test that nothing runs is not coverage (the OSE-1244 trap).
- **Safe:** attacks use a sandbox repo and test-only credentials. No test ever tries to leak a real secret.
- **Fixed first:** `red-team-adversarial.yml`'s own `workflow_run` flaw (finding 5), because the suite runs through it.

### Phase 0 — close every leak path and prove it (code only; days)

| # | Fix | Paired red-team test (born-red today) | Repos |
|---|---|---|---|
| 0.1 | `persist-credentials: false` on the 18 token checkouts | A PR-time step searches every checkout's `.git/config`, `http.extraheader` and `$RUNNER_TEMP` credential files for a token; it must find none | OSE, OW, OA, OSG, OSM, OSP, OSR, OCR-docs |
| 0.2 | No secrets in any `workflow_run` run whose source event is `pull_request`, same-repo or not. The three red-team/finale/post-T6 workflows run on push/schedule, or treat PR files as data only | A `full-pipeline/x` branch in the sandbox triggers them; no job that holds a secret may execute its code | OSE |
| 0.3 | robot-knowledge: inputs through `env:`, `GITHUB_TOKEN` (`contents: write`) instead of `ROBOT_PAT` | Dispatch inputs containing `$(...)`, backticks and `"; curl …`; nothing may execute | robot-knowledge |
| 0.4 | SHA-pin every third-party action in a job that holds a secret; `.github/dependabot.yml` for `github-actions` | A gate fails on any tag-pinned third-party action in a secret-holding job (a mutable tag is the swap vector) | OSE, OW |
| 0.5 | No `${{ secrets.* }}`, `${{ inputs.* }}` or `${{ github.event.* }}` inside a `run:` script | Grep gate, plus an injection fixture per `workflow_dispatch` workflow | OW, robot-knowledge, all |
| 0.6 | Top-level `permissions:` on every workflow | A PR job's `GITHUB_TOKEN` tries to push, comment and open an issue; every attempt must fail | all |
| 0.7 | Production `ALLOW_OCR_INTERNAL` off, `X_OCR_INTERNAL` deleted from the production Worker, production smoke on the production Access token (needs 1.4) | Production `/admin` and `/api/v2/admin/*` are hit with `X-OCR-Internal`, Bearer `ADMIN_KEY`, the staging Access token and no credentials; all must be refused. Joins the CF Access canary (`access-app-routing`) | OSE |
| 0.8 | **Static gates, fleet-wide**, built on OSE's existing #28 enforcement (`scripts/check-pr-secret-exposure.mjs`, its allowlist, `ci-approval-gate-safety.invariant.spec.ts`) rather than a new checker. Rules: Standard §5 | Each rule is born red against today's `main` (18 persisted checkouts, staging values on production jobs, the static production admin path) | OCR-docs (shared action) + every repo |
| 0.9 | **Brain:** credential isolation becomes a new invariant, **`credential_isolation`** (proposed number 29), in the Privacy & Identity group. #28 stays as its CI-surface half, with `applies_to` extended to the fleet. Status is honest (`gap` / `partial`) with reasons. Its own PR runs the brain's levels 0-9 first | The conformance report gains its row, so the public proof of the privacy promise shows it | OCR-docs |
| 0.10 | **Launch gate:** the OSE-1251 GO/NO-GO requires 0.1-0.9 green and the exposure record closed. Root `CLAUDE.md` §5's Done definition gains: a story is not Done while a credential-isolation gate is red | — | OSE, Linear |

### Phase 1 — dashboards, rotation, and the tests that need them (owner + wiring PRs)

| # | Owner action | Paired red-team test |
|---|---|---|
| 1.1 | Rotate `OCR_PROPAGATE_TOKEN` now (treat as exposed), and **delete** the old one. Then take it out of PR jobs: hub packages to GitHub Packages, brain checks as trusted checks (Standard §4.1), the two GitHub Apps in environments `ci-read` / `automation`, and revoke the PAT | A reader token minted in a trusted job is used to push, open a PR, read an unlisted repo, and after expiry; all must fail |
| 1.2 | Protect `main`: no bypass for admins or agents, required checks. Add a **tag ruleset** so only the owner can create release tags | A sandbox push of a `v*` tag by a non-owner identity is refused |
| 1.3 | Environments: `staging` (tests), `staging-deploy`, `production`, each with a deployment branch rule (`main`; `production` also protected tags). Add required reviewers where the plan allows (decision 7) | A PR-triggered job that names each environment is refused before any step runs |
| 1.4 | Cloudflare: per-environment deploy tokens (scoped to one Worker if available), each expiring; `CF_READ`; one Access service token per environment | Staging credentials against production, and the reverse; all must fail |
| 1.5 | Doppler: `stg` → `staging`, `stg_deploy` → `staging-deploy`, `prd` → `production`; **separate configs for CI credentials and Worker runtime** so `wrangler secret bulk` never ships CI or deploy credentials into a Worker. Stop syncing to repository secrets, then delete the repository copies | A deployed Worker's secret list contains only the manifest's runtime names |
| 1.6 | `OCR_CI_EDGE_TOKEN` (env `staging`) and its WAF rule | — |
| 1.7 | Audit-log review and close the exposure record | Revoked and expired tokens fail closed in CI with a clear error, never falling back to another credential |
| 1.8 | Provider caps: Anthropic spend limit; Maps key restrictions | Canary credentials in each zone; any use raises an alert |

### Phase 2 — runtime and hygiene

- **2.1** Manifest metadata (`zone`, `owner`, `expires`, `exception_until`) added to the 0.8 checker's allowlist, per repo.
- **2.2** Deploy jobs write Worker secrets from the runtime Doppler config and check the manifest's required list. This retires `scripts/set-secrets.sh` and `.github-secrets-required.json`.
- **2.3** **Generate fresh production data keys at launch.** Keyrings (Standard §2.1) before the first rotation that has real data behind it.
- **2.4** Cleanup:
  - turn non-secret IDs and URLs into variables;
  - delete duplicates and dead names;
  - move to a Linear bot key;
  - move PR-time ticketing to push or schedule jobs.
- **2.5** `harden-runner` in audit mode on every secret-holding job.

### Phase 3 — later

- **3.1** A separate Cloudflare account for production.
- **3.2** `harden-runner` block mode with an egress allowlist.

### Owner decisions needed

1. **GitHub Apps vs fine-grained PATs** for cross-repo access. Recommendation: Apps.
2. **Who approves production,** plus a backup. With one owner, the real wall is branch and tag rules; a self-approval is a click, not a review.
3. **Production admin through Access only.** Recommendation: yes (0.7).
4. **Doppler delivery pattern.** Recommendation: sync to environments, with separate CI and runtime configs.
5. **Can `OCR-docs` and the hub be public?** If neither holds anything private, every cross-repo read credential leaves CI.
6. **`full-pipeline/*` PR-time staging deploys.** They put staging deploy credentials within reach of PR code. Recommendation: retire them; deploy only from `main` (the post-merge chain already exists). Note that root `CLAUDE.md` §5's Done definition reads the post-merge chain.
7. **GitHub plan and repo visibility.** Required reviewers on environments may need GitHub Enterprise for private repositories (reported by the 2026-10-01 review; not verifiable from this environment). The design does not depend on them, but confirm what the org's plan allows.

## 4. Scan scripts (reproducible)

Run each from a directory that holds one checkout per repo at `main` (Python 3 with PyYAML). The first prints every column of §1's table: workflows, first- and third-party pins (tag / SHA), workflows without top-level `permissions:`, the secrets referenced, and those referenced from PR-triggered workflow files. The second prints finding 1: the persisted-token checkouts and the count of workflow files that reference `OCR_PROPAGATE_TOKEN`.

Notes on how to read the output:

- **Counting is per `uses:` line**, anchored to the start of a line, so a `uses:` inside a comment or another key (e.g. `statuses: read`) is not counted. Local `./` actions are excluded.
- **"Reachable from PR-triggered workflows" is per workflow file.** It ignores job `if:` conditions on purpose (Standard §1.1).

```python
import glob,re,os,yaml,collections
# Run from a directory holding one checkout per repo at main.
roots={r: r for r in sorted(os.listdir('.')) if os.path.isdir(os.path.join(r, '.github', 'workflows'))}
SHA=re.compile(r'@[0-9a-f]{40}$')
for repo,root in sorted(roots.items()):
    fp_tag=fp_sha=tp_tag=tp_sha=0; noperm=[]; prsecrets=collections.Counter(); allsec=set(); tp_tag_names=set(); wfs=0
    for f in sorted(glob.glob(root+'/.github/workflows/*.y*ml')):
        txt=open(f).read()
        try: y=yaml.safe_load(txt)
        except Exception: continue
        if not isinstance(y,dict): continue
        wfs+=1
        on=y.get(True, y.get('on')) or {}
        trig=list(on.keys()) if isinstance(on,dict) else ([on] if isinstance(on,str) else list(on))
        pr=any(t in trig for t in ('pull_request','pull_request_target'))
        if 'permissions' not in y: noperm.append(os.path.basename(f))
        secs=set(re.findall(r'secrets\.([A-Z0-9_]+)',txt)); allsec|=secs
        if pr:
            for s in secs: prsecrets[s]+=1
        for u in re.findall(r'(?m)^\s*-?\s*uses:\s*([^\s#]+)',txt):
            if u.startswith('./') or u.startswith('docker://'): continue
            first=u.split('/')[0] in ('actions','github')
            sha=bool(SHA.search(u))
            if first: fp_sha+=sha; fp_tag+=(not sha)
            else:
                tp_sha+=sha; tp_tag+=(not sha)
                if not sha: tp_tag_names.add(u)
    allsec.discard('GITHUB_TOKEN')
    print(f"## {repo}: {wfs} workflows | first-party tag/sha {fp_tag}/{fp_sha} | third-party tag/sha {tp_tag}/{tp_sha}")
    if tp_tag_names: print("   third-party on tags:", ', '.join(sorted(tp_tag_names)))
    print("   no top-level permissions:", len(noperm), ', '.join(noperm))
    print("   secrets:", ', '.join(sorted(allsec)))
    pr_s={k:v for k,v in prsecrets.items() if k!='GITHUB_TOKEN'}
    print("   reachable from PR-triggered workflows:", ', '.join(f"{k}({v})" for k,v in sorted(pr_s.items())))
```

```python
import sys,glob,re,os
import yaml
# Run from a directory holding one checkout per repo at main.
roots={r: r for r in sorted(os.listdir('.')) if os.path.isdir(os.path.join(r, '.github', 'workflows'))}
tot_wf=0; rows=[]
for repo,root in sorted(roots.items()):
    for f in sorted(glob.glob(root+'/.github/workflows/*.y*ml')):
        txt=open(f).read()
        try: y=yaml.safe_load(txt)
        except Exception as e: continue
        if not isinstance(y,dict): continue
        on=y.get(True, y.get('on')) or {}
        trig=list(on.keys()) if isinstance(on,dict) else ([on] if isinstance(on,str) else on)
        pr='pull_request' in trig or 'pull_request_target' in trig
        uses_tok='OCR_PROPAGATE_TOKEN' in txt
        if uses_tok: tot_wf+=1
        for jn,j in (y.get('jobs') or {}).items():
            for s in j.get('steps') or []:
                u=str(s.get('uses',''))
                w=s.get('with') or {}
                if u.startswith('actions/checkout') and 'token' in w and 'OCR_PROPAGATE_TOKEN' in str(w['token']):
                    if str(w.get('persist-credentials','true')).lower()!='false':
                        rows.append((repo,os.path.basename(f),jn,pr))
print('workflows referencing OCR_PROPAGATE_TOKEN:',tot_wf)
print('persisted token checkouts:',len(rows))
for r in rows: print('  ',r)
```
