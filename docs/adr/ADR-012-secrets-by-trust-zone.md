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
  - **18 checkouts leave it in `.git/config`, in 10 workflow files that a pull request can trigger, across 9 repos.**
    Pull-request code or freshly installed dependencies run later in the same job:
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

  Rotation is written down for four ourSharedEvents secrets, at 90 days. There is no
  procedure for the data-protection keys. Rotating `FORMS_ENCRYPTION_KEY` today would make
  stored data unreadable.

- **The supply chain can read secrets.** Of 119 `uses:` lines in ourSharedEvents, 117 are pinned by tag.
  ourWKRP runs `dopplerhq/cli-action@v3` and `claude-code-action@v1` on tags, with Doppler and
  Anthropic credentials in scope.

- **Workflow inputs reach the shell.** `robot-knowledge/.github/workflows/robot-commit.yml:28-50`
  interpolates dispatch inputs straight into a shell script that holds `ROBOT_PAT`.

Invariant #28 (`ci_approval_gate_secret_surface`) already chose the right control for one repo
on 2026-09-26: environment secrets with required reviewers. It is `partial` and applies to OSE only.
The ADR-008 rollout gate (D1) already requires splitting and rotating `OCR_PROPAGATE_TOKEN`.
This ADR turns those point decisions into one fleet model.

## Decision

**1. Every secret belongs to exactly one trust zone, and a zone's secrets are only reachable from that zone.**
The zones follow the CI/CD pipeline, which already separates tiers:

| Zone | Who runs there | May hold |
|---|---|---|
| **Z0 Untrusted code** | Any job that runs pull-request code or freshly installed dependencies, on any trigger | Read-only, repo-scoped, ≤1 hour GitHub App tokens. Nothing that deploys, writes data, or authenticates as admin |
| **Z1 Trusted CI** | Jobs that run only `main` code (push to `main`, schedule) and test against staging | Staging *test* credentials, from GitHub environment `staging` |
| **Z2 Staging deploy** | The staging deploy job | Staging deploy and data credentials, from environment `staging` |
| **Z3 Production deploy** | The production deploy and production smoke jobs | Production credentials, from environment `production` with a required human reviewer and a `main`/tag-only deployment rule |
| **Z4 Org automation** | Cross-repo writers (`propagate-standards`, the conformance refresh PR) | A GitHub App token with write on named repos only, minted per run. Never in a workflow a pull request can trigger |
| **Z5 Runtime** | The deployed Workers | Worker secrets, a distinct value per environment, never stored in GitHub |
| **Z6 People** | Operators | Doppler and Cloudflare accounts with SSO and two-factor. Personal tokens never enter CI |

**2. Credentials live as briefly as the job allows.**

- A credential that can be minted per run is: GitHub App installation tokens (1 hour), `GITHUB_TOKEN`, and OIDC.
- A long-lived API token is created with an expiry date (≤90 days) where the provider supports one,
  and otherwise rotated on a calendar.

- Keys that protect stored data are versioned and rotated with a dual-read window, never by a blind swap.

**3. Doppler is the only writer.** Each product has one Doppler project with `dev`, `stg` and `prd` configs.

- `stg` syncs to GitHub environment `staging`, and `prd` to environment `production`, never to repository secrets.
- Worker runtime secrets are written from the matching config by the environment-gated deploy job.
- Org-level automation credentials live in a separate project, `ocr-platform`.
- Setting a GitHub or Worker secret by hand is a drift event, as the OSE-349 doc already says.

**4. The rules are checked, not remembered.**

- Each repo keeps a secrets manifest: names, zone, owner, expiry. No values.
- A fleet checker fails CI when:
  - a workflow references a secret missing from the manifest;
  - a zone-Z2-or-higher secret is reachable from a pull-request-triggered job;
  - a token checkout persists credentials;
  - a third-party action is not SHA-pinned;
  - a workflow has no top-level `permissions:`.

  This is the fleet-wide form of invariant #28.

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

The strongest staging/production wall. Cloudflare API tokens can be limited to an account or zone,
but not to one Worker script or one D1 database.

**Deferred, not rejected:** it means moving DNS, D1, KV, R2 and Access apps. Separate per-environment
tokens with expiry come first. A second account is a Phase 3 decision for the owner.

### Alternative D: A hosted secrets vault with dynamic credentials (Vault, cloud KMS)

**Rejected for now:** Cloudflare and GitHub can't issue dynamic credentials from such a vault,
and the cost and operating load don't fit ADR-006 (free-forever guardrails). Doppler plus GitHub App and
OIDC tokens covers the same ground at this size.

## Consequences

### Positive

- A leaked pull-request token can read a few repos for up to an hour. It cannot push, deploy or reach production.
- Production credentials require a person to approve each production job. The staging values cannot reach production.
- Each automation run has its own identity (the App plus a run), so the audit log shows which run did what.
- Drift ends: one writer (Doppler), read-only mirrors, and a manifest that fails CI when a workflow strays from it.

### Negative

- Two GitHub Apps to create and own, and their private keys to protect. They are the new crown jewels.
- Production deploys wait for a reviewer. That is the point, but it is slower.
- Data-protection keys need key-versioning code before they can be rotated safely.
- More environment secrets to keep in sync. Doppler does the work, but someone must set the integration up once per environment.

### Neutral

- Cloudflare tokens still reach the whole account until Alternative C is decided.
- `GITHUB_TOKEN` stays the default for anything inside one repo; the Apps cover only cross-repo work.

## Implementation Notes

- **Affected repos:** all 11 in the inventory. ourSharedEvents and ourWKRP carry most of the work.
- **Brain invariant:** extend #28 `ci_approval_gate_secret_surface` to the fleet (`applies_to`), and add the manifest checker as its enforcement.
- **Standard:** `docs/standards/OCR_STANDARD_secretsAndTokens.md`.
- **Inventory and phased plan:** `docs/references/OCR_REFERENCE_secretsInventory_2026-10-01.md`.
- **Related:** ADR-005 (shared CI security bracket); ADR-006 (cost guardrails); ADR-008 rollout gate D1/F2/F6/F12; OSE ADR-020 (human approval on agent PRs); OSE-349 (Doppler as single writer); OW-116, OW-150, OW-153.
