# ADR-012: Hold every secret in one trust zone, issue it for the shortest life that works, and write it only from Doppler

**Status:** Proposed
**Date:** 2026-10-01
**Deciders:** mzdan (PO) — pending review
**Scope:** Fleet-wide

## Context

The fleet's credentials grew one workflow at a time. The 2026-10-01 inventory
(`docs/references/OCR_REFERENCE_secretsInventory_2026-10-01.md`) found these problems in the repos at `main`:

- **One write-capable personal access token reaches every repo.** `OCR_PROPAGATE_TOKEN`
  is an org secret referenced by 33 workflow files across the fleet. One workflow, `propagate-standards`,
  needs it to write, so it can write everywhere.
  - **18 checkouts persist it for later steps, in 10 workflow files that a pull request can trigger, across 8 repos.**
    In two of them, pull-request code or a PR-lockfile install runs later in the same job (`gate-tests-sub`, `brain-location-audit`); the rest are exposed because the PR controls the workflow file:
    - `brain-contract-check.yml` in OSE, OW, OA, OSG, OSM, OSP and OSR;
    - `oursharedevents-ci.yml` (`gate-tests-sub`, lines 943-948);
    - `inv22-cross-repo-gate.yml` (OSE);
    - `brain-location-audit.yml` (OCR-docs, 8 checkouts).
  - Method: a YAML scan of every `actions/checkout` step whose `token:` is this secret and whose
    `persist-credentials` is not `false`, at each repo's `main` on 2026-10-01
    (script recorded in the inventory reference).

- **Production is not separated from staging.** In ourSharedEvents, Doppler's `stg` config syncs into
  *repository* secrets. So `deploy-production` and `smoke-production` read the staging
  values, and the `production` environment gate protects nothing.
  - One Cloudflare token (`CLOUDFLARE_API_TOKEN_OSE`) both deploys and writes D1 data, for both environments.
  - Production accepts a static shared header for admin (`wrangler.toml:324`, `ALLOW_OCR_INTERNAL = "true"`).
- **Nothing expires on its own.** None of these has an expiry:
  - the PAT;
  - the Cloudflare and Anthropic keys;
  - the Linear personal key;
  - the Worker's signing secrets and peppers.

  Rotation is written down for four ourSharedEvents secrets, at 90 days. Of the data-protection keys,
  only two can rotate safely today: `FORMS_ENCRYPTION_KEY` has a keyring with a re-encrypt path, and
  `ANON_ID_HASH_PEPPER` is epoch-versioned with a purge runbook. The other peppers and the signing
  secrets have no versioning, so rotating them loses data or breaks links.

- **The supply chain can read secrets.** Of 117 action references in ourSharedEvents, 115 are pinned by tag.
  ourWKRP runs `dopplerhq/cli-action@v3` and `claude-code-action@v1` on tags, with Doppler and
  Anthropic credentials in scope.

- **Workflow inputs reach the shell.** `robot-knowledge/.github/workflows/robot-commit.yml:28-50`
  interpolates dispatch inputs straight into a shell script that holds `ROBOT_PAT`.

Invariant #28 (`ci_approval_gate_secret_surface`) chose environment secrets with required reviewers
for one repo on 2026-09-26. It is `partial` and applies to OSE only. The required-reviewer half cannot
work yet: agents act as the owner's account, and GitHub never counts an author's own approval (CCR gate, Loop 2).
The ADR-008 rollout gate (D1) already requires splitting and rotating `OCR_PROPAGATE_TOKEN`.
This ADR turns those point decisions into one fleet model.

## Decision

**0. Credential isolation is a privacy guarantee.** The platform's promise is that it never knows who you are. That promise also depends on who can change the code that keeps it, and who can read the stores behind it. So credential isolation becomes brain invariant **#29 `credential_isolation`** in the Privacy & Identity group. It is tested the way #1 and #8 are: blocking gates and red-team tests that are born red, mutation-checked and wired into CI. It is a **launch gate** (OSE-1251) and part of the Done definition.

**Prerequisites:** `main` is protected with no bypass (admins and agents included), and each environment's branch rule is set in repository settings, outside the deployed commit. Every zone below relies on these two. A tag ruleset limits who can create release tags, but only for release-label integrity: tags are labels and never trigger a deploy. **Agents act under their own identity** (a bot account or GitHub App), separate from the human who approves. Today they do not: agent sessions commit, open PRs and dispatch workflows as the owner's account (`bereasonable13`), so no review or bypass rule can tell the two apart (CCR gate R16).

**1. Every secret belongs to exactly one trust zone, and a zone's secrets are only reachable from that zone.**
The zones follow the CI/CD pipeline, which already separates tiers:

| Zone | Who runs there | May hold |
|---|---|---|
| **Z0 Untrusted code** | Any job whose workflow file or executed code comes from a pull request, including dependencies the pull request selects | **No long-lived secret.** `GITHUB_TOKEN` (read, plus `packages: read`), and by recorded exception a federated short-lived token. Cross-repo inputs come as packages or trusted checks |
| **Z1 Trusted CI** | Jobs that run only `main` code (push to `main`, schedule; `workflow_run` only when the source run was a `push` or `schedule` on this repository's `main` (`workflow_run.event` is `push`/`schedule`, `head_branch == 'main'`, `head_repository.full_name == github.repository`). A push to any other branch is not trusted: its code and artifacts are author-controlled, and the environment rule checks the triggered workflow's ref, not the source run's) | Staging *test* credentials from environment `staging`; the cross-repo reader App key from environment `ci-read` |
| **Z2 Staging deploy** | The staging deploy job | Staging deploy and data credentials, from environment `staging-deploy`, kept apart from the test credentials |
| **Z3 Production deploy** | The production deploy and production smoke jobs | Production credentials, from environment `production` with a `main`-only deployment rule, enforced outside the deployed commit (and a required reviewer once agents have their own identity) |
| **Z4 Org automation** | Cross-repo writers (`propagate-standards`, the conformance refresh PR) | A GitHub App token with write on named repos only, minted per run. Never in a workflow a pull request can trigger |
| **Z5 Runtime** | The deployed Workers | Worker secrets, a distinct value per environment, never stored in GitHub |
| **Z6 People** | Operators | Doppler and Cloudflare accounts with SSO and two-factor. Personal tokens never enter CI |

**2. Credentials live as briefly as the job allows.**

- A credential that can be minted per run is: GitHub App installation tokens (1 hour), `GITHUB_TOKEN`, and OIDC.
- A long-lived API token is created with an expiry date (≤90 days) where the provider supports one,
  and otherwise rotated on a calendar.

- Keys that protect stored data are versioned and rotated with a dual-read window, never by a blind swap.

**3. Doppler is the only writer.** Each product has one Doppler project:

- runtime configs `dev`, `stg` and `prd`;
- CI and deploy configs `stg_ci`, `stg_deploy` and `prd_deploy`, as separate root environments (not branch configs, which may inherit runtime keys).

How values leave Doppler:

- CI and deploy configs sync to the matching GitHub environments, never to repository secrets.
- Worker runtime secrets are written from the runtime config by the environment-gated deploy job. A CI or deploy credential therefore never lands in a Worker.
- Org-level automation credentials live in a separate project, `ocr-platform`.
- Setting a GitHub or Worker secret by hand is a drift event, as the OSE-349 doc already says.

**4. Every fix is proved by an attack.**

- **Static gates:** OSE's existing #28 enforcement (`check-pr-secret-exposure.mjs` and its allowlist) becomes a fleet-wide shared check. The allowlist grows into a per-repo manifest of names, zone, owner and expiry; no values. It fails CI on any rule in Standard §5.
- **Red-team tests:** each fix ships paired with the red-team test that proves it. The test is born red against today's `main`, mutation-checked, and blocking.
  - Static checks show the configuration looks right. The red-team tests show an attacker cannot actually reach a secret.
  - The pairs, in order, are the inventory's Phase 0 and Phase 1 tables.

The full rules are in `docs/standards/OCR_STANDARD_secretsAndTokens.md`.

## Alternatives Considered

### Alternative A: Keep one org PAT, rotate it on a schedule

Lowest effort; it is what the ADR-008 gate's D1 asks for as a first step.

**Rejected because:** rotation shortens how long a leaked token works, but it does not shrink what it can do.
A write-everywhere token readable from pull-request code stays a write-everywhere token.
It also names no actor, so a leak cannot be traced to a run. It is kept only as the **interim** step
until the GitHub Apps exist.

### Alternative B: Doppler service token in every CI job (`doppler run` everywhere)

One credential in CI, every value fetched at run time.

**Rejected because:** one token that unlocks a whole config becomes the most valuable secret in the job.
Every Z0 job would hold it. OSE's CCR for OSE-349 rejected this for the same reason. A per-config,
read-only Doppler token is still allowed **inside an environment-gated deploy job**, as ourWKRP does
today, because there the gate is the protection.

### Alternative C: Separate Cloudflare accounts for staging and production now

The strongest staging/production wall. Within one account, a token's reach depends on Cloudflare's resource scoping.
Per-Worker scoping for account-owned tokens was reported announced on 2026-09-15 (2026-10-01 review); confirm it in the dashboard, and use it.

**Deferred, not rejected:** it means moving DNS, D1, KV, R2 and Access apps. Separate per-environment
tokens with expiry come first. A second account is a Phase 3 decision for the owner.

### Alternative D: A hosted secrets vault with dynamic credentials (Vault, cloud KMS)

**Rejected for now:** Cloudflare and GitHub can't issue dynamic credentials from such a vault,
and the cost and operating load don't fit ADR-006 (free-forever guardrails). Doppler plus GitHub App and
OIDC tokens covers the same ground at this size.

## Consequences

### Positive

- A pull-request job holds nothing long-lived. What it can leak is its own `GITHUB_TOKEN`, valid for that job, plus any recorded exception (today: the review bots' Anthropic key, capped and dated). It cannot push elsewhere, deploy or reach production.
- Production credentials are reachable only from `main`, through a control the deployed commit cannot edit: an environment branch rule or a deployment protection rule. An ancestry check inside the workflow is not enough, because a tag push runs the tagged commit's own workflow file. The staging values cannot reach production.
- Each automation run has its own identity (the App plus a run), so the audit log shows which run did what.
- Drift ends: one writer (Doppler), read-only mirrors, and a manifest that fails CI when a workflow strays from it.

### Negative

- Two GitHub Apps to create and own, and their private keys to protect. They are the new crown jewels, and they live only in environments that pull requests cannot enter.
- The hub must publish `@ocr/ui` to GitHub Packages and the brain checks must become trusted `workflow_run` checks before the PAT can go. That is the larger part of Phase 1.
- Production deploys wait for a reviewer once agents have their own identity. That is the point, but it is slower.
- Data-protection keys need versioning before they can be rotated safely. `FORMS_ENCRYPTION_KEY` already has a keyring (`ourSharedEvents/workers/oursharedevents/src/lib/pii.ts`); `ANON_ID_HASH_PEPPER` is epoch-versioned (`pepper_epoch`); `FORMS_HASH_PEPPER`, `IP_HASH_PEPPER` and the signing secrets are not.
- More environment secrets to keep in sync. Doppler does the work, but someone must set the integration up once per environment.

### Neutral

- Cloudflare tokens still reach the whole account until Alternative C is decided.
- `GITHUB_TOKEN` stays the default for anything inside one repo; the Apps cover only cross-repo work.

## Implementation Notes

- **Affected repos:** all 11 in the inventory. ourSharedEvents and ourWKRP carry most of the work.
- **Brain invariants:**
  - new **#29 `credential_isolation`** (Privacy & Identity);
  - #28 `ci_approval_gate_secret_surface` stays as its CI-surface half, with `applies_to` extended to the fleet.

  This lands as Phase 0 item 0.9, in its own PR, after the brain's test levels run.

- **Launch gate:** OSE-1251 GO/NO-GO requires the Phase 0 pairs green and the exposure record (inventory §1) closed.
- **Standard:** `docs/standards/OCR_STANDARD_secretsAndTokens.md`.
- **Inventory and phased plan:** `docs/references/OCR_REFERENCE_secretsInventory_2026-10-01.md`.
- **Related:** ADR-005 (shared CI security bracket); ADR-006 (cost guardrails); ADR-008 rollout gate D1/F2/F6/F12; OSE ADR-020 (human approval on agent PRs); OSE-349 (Doppler as single writer); OW-116, OW-150, OW-153.
