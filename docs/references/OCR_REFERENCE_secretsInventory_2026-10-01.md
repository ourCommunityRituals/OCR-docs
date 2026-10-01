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
| ourSharedEvents | 28 | 5 / 2 | 9 | 16 |
| ourWKRP | 6 | 3 / 1 | 5 | 5 |
| OCR-docs | 10 | 0 / 0 | 3 | 2 |
| hub (ourCommunityRituals) | 5 | org reusable workflow on `@v1` | 4 | 1 |
| OA, OSG, OSM, OSP, OSR | 3 each | 0 / 0 | 1 each (`docs-ci.yml`) | 2 each |
| OER | 1 | 0 / 0 | 0 | 1 |
| robot-knowledge | 1 | 0 / 0 | 1 | 1 |

First-party `actions/*` references are on tags everywhere except the hub (18 of 19 SHA-pinned). The standard allows first-party tags.

### Findings, most severe first

1. **The write-capable org PAT `OCR_PROPAGATE_TOKEN` is readable from pull-request code.**
   - 33 workflow files reference it.
   - **18 checkouts in 10 PR-triggered workflow files across 9 repos leave it in `.git/config`.** PR code or PR-lockfile installs run later in the same job:
     - `brain-contract-check.yml` in OSE, OW, OA, OSG, OSM, OSP, OSR;
     - `oursharedevents-ci.yml` `gate-tests-sub`;
     - `inv22-cross-repo-gate.yml`;
     - `OCR-docs/brain-location-audit.yml` (8 checkouts).
   - Being an org secret, it is reachable from any same-repo PR anyway (Standard §1.1). Persisting it also exposes it to dependencies installed from the PR.
2. **OSE production reads staging values.** Doppler `oursharedevents/stg` syncs to OSE *repository* secrets (`docs/doppler/CF-ACCESS-SECRETS-SOURCE-OF-TRUTH.md:23-24,36`). The `production` environment's gate (`oursharedevents-ci.yml:2171`) therefore guards no distinct secret. `smoke-production` (`:2342`) has no environment at all.
3. **One Cloudflare token (`CLOUDFLARE_API_TOKEN_OSE`) covers deploy and D1 writes for staging and production.** It is a repository secret, so it is reachable from any same-repo PR.
4. **Production accepts a static admin header.** `ALLOW_OCR_INTERNAL = "true"` sits in `[env.production.vars]` (`workers/oursharedevents/wrangler.toml:324`). If `X_OCR_INTERNAL` is set on the production Worker, that header is a production admin credential that bypasses Cloudflare Access. If it is unset, the check refuses everyone (`src/auth/admin.ts:269-273`).
5. **Three `workflow_run` workflows check out `head_sha` and inject admin and Access secrets, with no same-repo check:** `red-team-adversarial.yml:33`, `security-finale.yml:32`, `post-t6-security.yml:33`.
6. **Script injection in `robot-knowledge/.github/workflows/robot-commit.yml:28-50`.** `workflow_dispatch` inputs are interpolated into the shell next to `ROBOT_PAT`. Only someone who can dispatch can exploit it.
7. **Third-party actions on tags with secrets in scope:**
   - `dopplerhq/cli-action@v3` (OW, with `DOPPLER_TOKEN_*`);
   - `anthropics/claude-code-action@v1` (OW);
   - `dorny/test-reporter@v3` (OSE, `checks: write`);
   - `step-security/harden-runner@v2` (OSE).
8. **11 OSE Worker secrets are outside `scripts/set-secrets.sh`**, which provisions only 4 (`ADMIN_KEY`, `FORMS_ENCRYPTION_KEY`, `FORMS_HASH_PEPPER`, `SHARED_REPORT_SIGNING_SECRET`). The 11 are the §2.3 names, other than those four and `LINEAR_TEAM_ID`. Each is read by `workers/oursharedevents/src/` (grep for `env.<NAME>`). None of them has a rotation procedure. `SPONSOR_INVITE_SIGNING_SECRET` is not even listed in `wrangler.toml`. Rotating `FORMS_ENCRYPTION_KEY` is documented as destroying data (`docs/runbooks/RUNBOOK-SECRETS.md:106-107`).
9. **OW declares Last.fm credentials as empty `[vars]`** (`wrangler.toml:95-96,155-156`). Doppler cannot deliver them there, and `wrangler secret put` collides with the var name.
10. **Hygiene:**
    - a URL stored as a secret (`STAGING_BASE_URL`);
    - a duplicate admin secret (`STAGING_ADMIN_KEY` vs `ADMIN_KEY`);
    - `OSE_ADMIN_BEARER`, unset since May;
    - stale `ADMIN_KEY_ROOT` still marked required in `.github-secrets-required.json`;
    - dead GAS/Sheets names in `.github/workflow-archive/`;
    - no repo has `.github/dependabot.yml`, although two docs say "bump via Dependabot".

---

## 2. Per-secret map

Zone per ADR-012. "Today" is where the value is held now; "Target" is where it moves.

### 2.1 Org and CI identity

| Secret | Repos | Today | Zone | Target | Phase |
|---|---|---|---|---|---|
| `OCR_PROPAGATE_TOKEN` (reads) | all 10 | org secret, classic or fine-grained PAT, write-capable | Z0 | `ocr-ci-reader` App token, minted per job, `contents: read` on named repos | 1 |
| `OCR_PROPAGATE_TOKEN` (writes: propagate-standards, conformance PR) | OCR-docs, OSE | same PAT | Z4 | `ocr-automation` App token in environment `automation` | 1 |
| `OCR_PROPAGATE_TOKEN` (OSM issue) | OSE `notify-osm-flag-change.yml:45` | same PAT | Z4 | `ocr-automation`, `issues: write` on OSM only | 1 |
| `LINEAR_API_KEY`, `LINEAR_TEAM_ID` | OSE, OW, OCR-docs, 5 spokes; OSE Worker | repo secrets; personal key | Z1 for the drift-ticket bots (they run on PRs today) | a Linear **bot/app key**, not a personal key, synced from `ocr-platform`; PR-time ticketing moves to a `push`/`schedule` job | 2 |
| `ANTHROPIC_API_KEY` | OSE, OW | repo secret | Z0 (review bots run on PRs by design) | keep, with an Anthropic **spend limit** and a 90-day rotation; move to OIDC federation when available (OW `claude.yml:43-47` notes the plan) | 1 |
| `BRANCH_PROTECTION_READ_TOKEN` | OSE `oursharedevents-ci.yml:2500` | repo secret | Z0 | `ocr-ci-reader` App with `administration: read` on OSE only, or drop it and use `GITHUB_TOKEN` | 2 |
| `ROBOT_PAT` | robot-knowledge | repo secret, user PAT | Z4 | `GITHUB_TOKEN` with `contents: write` (same repo), and fix the injection | 0 |

### 2.2 ourSharedEvents CI

| Secret | Today | Zone | Target | Phase |
|---|---|---|---|---|
| `CLOUDFLARE_API_TOKEN_OSE` | repo secret (Doppler `stg` sync); deploy plus D1 for both environments | Z2/Z3 | `CF_DEPLOY_STG` (env `staging`) and `CF_DEPLOY_PRD` (env `production`), each expiring in ≤90d; `CF_READ` for `secret list` and the canary | 1 |
| `CLOUDFLARE_ACCOUNT_ID` | repo secret | not secret | repository **variable** | 2 |
| `ADMIN_KEY` | repo secret (stg value); also sent by `smoke-production` | Z1 | env `staging` only. Production smoke uses the production Access service token | 1 |
| `X_OCR_INTERNAL` | repo secret; prod Worker accepts it (`ALLOW_OCR_INTERNAL=true`) | Z1 | env `staging` only. Production: flag off, secret deleted | 1 |
| `CF_ACCESS_CLIENT_ID` / `_SECRET` | repo secret; one value used against staging and production | Z1 / Z3 | one Access service token per environment, in env `staging` / `production`, duration ≤1y | 1 |
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

### Phase 0 — code only, no owner action (hours)

Small, behaviour-preserving PRs. Each one closes a live read path.

| # | Change | Repos |
|---|---|---|
| 0.1 | `persist-credentials: false` on every token checkout outside a pushing job (the 18 in §1, finding 1) | OSE, OW, OA, OSG, OSM, OSP, OSR, OCR-docs |
| 0.2 | Same-repo guard on `workflow_run` head checkouts | OSE (3 workflows) |
| 0.3 | Move dispatch inputs to `env:`; replace `ROBOT_PAT` with `GITHUB_TOKEN` + `permissions: contents: write` | robot-knowledge |
| 0.4 | Top-level `permissions: contents: read` where missing (§1 counts) | all |
| 0.5 | SHA-pin the four tag-pinned third-party actions that run with secrets; add `.github/dependabot.yml` (`github-actions`) | OSE, OW |
| 0.6 | `${{ secrets.* }}` out of `run:` scripts (`claude-code-review.yml:42`) | OW |

### Phase 1 — owner actions in dashboards, plus small wiring PRs (days)

These need a person with org, Doppler and Cloudflare admin.

- **1.1** Create the two GitHub Apps (`ocr-ci-reader`, `ocr-automation`), install them on the repos in Standard §4.1, and store their private keys in Doppler `ocr-platform`.
  - Wiring PRs switch the 33 workflow files to `actions/create-github-app-token`.
  - Then **revoke `OCR_PROPAGATE_TOKEN`** and delete the org secret.
  - Until then: rotate the PAT once, as a fine-grained token with an expiry (the interim step in ADR-012 Alternative A).
- **1.2** GitHub environments:
  - `production`: required reviewer (the PO) and deployment branch rule `main` + tags.
  - `staging`: deployment branch rule `main`.
  - `automation`: branch rule `main`.
- **1.3** Doppler:
  - point the `oursharedevents/stg` sync at **environment `staging`**;
  - add `oursharedevents/prd` → environment `production`;
  - stop syncing to repository secrets, then delete the repository copies.
- **1.4** Cloudflare: create `CF_DEPLOY_STG`, `CF_DEPLOY_PRD` and `CF_READ` with 90-day expiries. Create one Access service token per environment. Revoke the shared token after the wiring PR lands.
- **1.5** Set `OCR_CI_EDGE_TOKEN` (env `staging`) and its WAF skip rule.
- **1.6** OSE production admin: CI's production smoke switches to the production Access service token. Then set `ALLOW_OCR_INTERNAL` off in `[env.production.vars]`, with a config test, and delete the production `X_OCR_INTERNAL`.
- **1.7** Provider caps: an Anthropic spend limit; Google Maps key restrictions.

### Phase 2 — enforcement and runtime (one to two sprints)

- **2.1** `.github/secrets.manifest.yaml` in every repo, plus the fleet checker (Standard §5) shipped from OCR-docs. Brain: extend invariant #28 `applies_to` to the fleet with the checker as enforcement.
- **2.2** Deploy jobs write Worker secrets from Doppler (`wrangler secret bulk`) and check the manifest's required list per environment (OSE, OW). Retire `scripts/set-secrets.sh` and the hand list in `.github-secrets-required.json`.
- **2.3** Keyrings for the data-protection keys (Standard §2.1), starting with `FORMS_ENCRYPTION_KEY` (INFRA-4) and the two signing secrets.
- **2.4** Cleanup:
  - non-secret IDs and URLs become variables;
  - delete duplicates and dead names;
  - Linear bot key;
  - PR-time ticketing moves to push or schedule jobs.
- **2.5** `harden-runner` in audit mode on every job that holds a Z2+ secret.

### Phase 3 — decisions for the owner (later)

- **3.1** A separate Cloudflare account for production (ADR-012 Alternative C).
- **3.2** `harden-runner` in block mode with an egress allowlist.
- **3.3** Canary credentials per zone (Standard §8).

### Owner decisions needed to start Phase 1

1. **GitHub Apps vs fine-grained PATs** for cross-repo access. Recommendation: Apps (per-run tokens, ≤1 hour, attributable).
2. **Who is the required reviewer** on `production` (and a second person for when the first is away).
3. **Production admin is Access-only.** Recommendation: yes, turn `ALLOW_OCR_INTERNAL` off in production in Phase 1.6.
4. **Doppler delivery pattern** for CI: sync to environment secrets (OSE style) or a per-config service token in the deploy job (OW style). The standard allows both. Recommendation: sync for CI test credentials, plus a service token only inside the deploy job for writing Worker secrets.

---

## 4. Scan script (reproducible)

Run against checkouts of each repo at `main`. It prints the per-repo counts in §1 and the persisted-token checkouts in finding 1.

```python
import glob, re, os, yaml
SHA = re.compile(r'@[0-9a-f]{40}$')
for root in sorted(glob.glob('*/')):
    for f in sorted(glob.glob(root + '.github/workflows/*.y*ml')):
        y = yaml.safe_load(open(f))
        if not isinstance(y, dict): continue
        on = y.get(True, y.get('on')) or {}
        trig = list(on) if isinstance(on, (dict, list)) else [on]
        pr = 'pull_request' in trig or 'pull_request_target' in trig
        if 'permissions' not in y: print('NO-PERMISSIONS', f)
        for jn, j in (y.get('jobs') or {}).items():
            for s in j.get('steps') or []:
                w = s.get('with') or {}
                if str(s.get('uses','')).startswith('actions/checkout') and 'OCR_PROPAGATE_TOKEN' in str(w.get('token','')) \
                   and str(w.get('persist-credentials','true')).lower() != 'false':
                    print('PERSISTED-TOKEN', f, jn, 'PR-triggered' if pr else '')
                u = str(s.get('uses',''))
                if u and not u.startswith(('./','docker://','actions/','github/')) and not SHA.search(u):
                    print('THIRD-PARTY-ON-TAG', f, u)
```
