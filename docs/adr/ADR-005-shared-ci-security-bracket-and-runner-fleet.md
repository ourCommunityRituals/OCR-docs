# ADR-005: Share the CI security bracket and self-hosted runner fleet across the hub-spoke fleet

**Status:** Proposed
**Date:** 2026-08-13
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

## Context

The OCR product line is a hub-spoke monorepo: the hub `ourCommunityRituals/ourCommunityRituals`
carries shared `packages/@ocr/*` (`flags`, `ui`, `data-provider`, **`runner-fleet`**) consumed by the
spokes (`ourSharedEvents`, `ourSharedGames`, `ourAirwaves`, `ourSharedMagnets`, `ourSharedPulse`, …)
via `file:` paths, with `OCR-docs` as the governance brain.

Two CI concerns are currently **duplicated and drifting per-spoke**, and both were exposed by a real
production incident on 2026-08-13 (P0 #323 / P1 #322 of the OSE sponsor-payment epic — see the OSE
runbook `workers/oursharedevents/docs/ops/ci-runner-watch-and-flake-runbook.md`):

1. **The security bracket (S0 pre-execution / S2 post-execution Semgrep SAST).** Every spoke hand-wires
   the same `pip install semgrep` + bare `semgrep scan` block in two places (S0 and S2). The bare
   invocation depends on the runner's PATH, which the self-hosted `BLOODRAVEN-2` runner does not
   reliably set — producing `exit 127` (`semgrep: command not found`) on ~1/3 of runs. This is
   duplicated logic AND a brittle invocation.

2. **The self-hosted runner fleet.** `@ocr/runner-fleet` already exists as a real fleet manager
   (registration-token rotation, health monitoring, auto-recovery restart→re-register, a static
   dashboard, a config-driven watchdog with `maxRestartAttempts`). But recovery/provisioning knowledge
   also lives in loose root scripts (`_bounce-runners-noelev.ps1`, `_fix-runner-env.ps1`,
   `_apply-runner-provisioning.ps1`, `reconfig-bloodraven2.ps1`), and `BLOODRAVEN-2` exhibits two
   distinct failure modes the fleet manager does not fully cover:
   - **No-log hang** — a job dispatches to `BLOODRAVEN-2` and sits `in_progress` far past baseline
     (30 min vs ~2 min) with no logs. The runner is `online + busy`, so an offline-based watchdog does
     not catch it.
   - **Env/PATH defect** — the Semgrep `exit 127` above (a provisioning gap, not a lifecycle event).

**Non-negotiable constraints:** the flow-brackets security convention (S0 opens / S2 closes every
flow) is preserved; secrets are never embedded (tokens via secret store, not code); audit/`#24`
traceability of gate outcomes is preserved; and — because org-wide shared CI means a bad change
reddens **every spoke at once** — all sharing is **pinned-tag versioned** with a **staged rollout**.

## Decision

Promote both concerns to **shared hub platform assets**, each in its natural home, consumed by every
spoke by **pinned version tag**:

- **Runner fleet → `@ocr/runner-fleet`.** Consolidate the loose root scripts and the CI-watch runbook
  into the package; it becomes the single, declarative (`fleet.config.json`) home for runner
  lifecycle, recovery, and **provisioning** (the fix for the `BLOODRAVEN-2` env/PATH defect lands here
  once, and every spoke's runners inherit it). The specific `BLOODRAVEN-2` remediation and the
  optimized runner flow are determined by the investigative fleet (see **Runner-2 remediation**, below)
  and recorded in the companion decision log.

- **Security bracket → a composite action inside a reusable workflow.** A hub composite action
  `.github/actions/security-scan/` owns Python + a **pinned** Semgrep + a **PATH-independent
  invocation** (`python -m semgrep` → PATH → `$pythonLocation/Scripts` fallback). A reusable workflow
  `.github/workflows/security-bracket.yml` (`workflow_call`) defines the **S0 + S2** bracket using that
  action. Each spoke calls
  `uses: ourCommunityRituals/ourCommunityRituals/.github/workflows/security-bracket.yml@v1`.

**Layering rationale:** a composite action shares a *step* (right granularity — S0/S2 are steps within
larger, per-spoke jobs); a reusable workflow shares the *bracket* (the flow-brackets convention wants
S0/S2 identical everywhere). A plain script is not versioned/referenceable cross-repo; an
`@ocr/security-scan` npm package adds CI-install friction for a GitHub-native concern. Hence: composite
action nested in a reusable workflow.

**Version contract (blast-radius control):** spokes reference `@v1`, **never `@main`**. The hub asset
carries its own CI. A new major (`@v2`) is cut only after it is proven green on the consumer-zero spoke
(OSE); spokes then adopt one pinned bump at a time.

## Rollout order (locked)

1. **OCR (`OCR-docs`, brain) — policy.** This ADR + governance invariants
   (`shared_security_bracket`, `shared_runner_fleet` in `architectural-invariants.yaml`, Security /
   Infrastructure groups) + the version/rollout contract. Declared before any code.
2. **OCR-org (hub monorepo) — implementation.** The composite action + `security-bracket.yml` +
   `@ocr/runner-fleet` consolidation, built against `@main`.
3. **OSE (`ourSharedEvents`) — consumer-zero / proving ground.** First spoke cut over; its green S0/S2
   justifies cutting `@v1`.
4. **OW (`ourWKRP`)** — second spoke.
5. **OSM → OA → OSG → OSR → …** — remaining spokes by importance, one pinned bump each.

## Alternatives Considered

### Alternative A: Fix Semgrep invocation in-place, per spoke
Apply the stashed `fix(ci): invoke semgrep binary directly` to each spoke's S0/S2 blocks.
**Rejected:** fixes the symptom but preserves the duplication and per-spoke drift; every future change
still touches N repos.

### Alternative B: Reusable workflow only (no composite action)
Share the whole S0/S2 jobs as one `workflow_call`. **Rejected as the *sole* mechanism:** spokes have
different surrounding pipelines; forcing a shared job shape is too coarse. The reusable workflow is
retained for the *bracket*, but built on the composite action for the *step*.

### Alternative C: Out-of-band scanning microservice
A hosted service the pipeline calls over the network. **Rejected:** Semgrep is a CLI SAST tool;
wrapping it in a network service adds auth, hosting, and latency for no benefit.

### Alternative D: Centralize everything up front (all spokes at once)
**Rejected:** org-wide blast radius demands a proven `@v1` and staged adoption; OSE is consumer-zero.

## Runner-2 remediation (determined by the investigative fleet)

> The best `BLOODRAVEN-2` remediation and the **optimized runner flow** (efficient · solidly
> functional · secure · easy to understand) are determined by a grounded investigative fleet
> (2 brainstorm + 2 solution cycles) reasoning over: this ADR, the CI-watch runbook, the invariant
> constitution, the existing codebase, and `@ocr/runner-fleet`. The fleet's synthesis and full
> **decision-flow log** are recorded in the companion doc
> `docs/decisions/runner-2-remediation-and-runner-flow.md` and folded back here on acceptance.

**Determined (2026-08-13) by investigative fleet `wf_1b03131c-39b` (35 agents; 2 brainstorm + 2 solution cycles). Full analysis + decision-flow log: [`docs/decisions/runner-2-remediation-and-runner-flow.md`](../decisions/runner-2-remediation-and-runner-flow.md).**

**Chosen: C1 (grafted)** — fix each bug at the layer it lives in, smallest surface, separating a same-hour unblock from the durable work:

- **Semgrep `exit 127` (fix first, same-hour):** replace the bare `semgrep scan` at S0/S2 with **module form `python -m semgrep scan …`** (resolves via interpreter site-packages, PATH-independent — so runner-2's Git-Bash-first `.env` that omits the Python `Scripts` dir stops mattering; **protects invariant #11**). Normalize the interpreter (`python` in both install and run), **pin the version**, and add a loud pre-flight `python -m semgrep --version || exit 1` so tool-unavailability fails traceably (**#24**), never as swallowed-green. Keep all `--config` + `--error` (security not weakened). Then lift into the ADR-005 composite `security-scan@v1`.
- **No-log hang:** the invariant **#12 janitor+probe is the single dwell-cap owner** (`hangOwner: 'janitor'`); the likely runner-2 root cause is that its out-of-band reconfig skipped `setup-runner.ps1`, so the janitor was never installed — reinstall it. The `@ocr/runner-fleet` busy-dwell detector is **armed only for janitor-incapable hosts** (off by default on the production runners) to avoid a split-brain double-bounce.
- **Fleet correctness + hardening (grafted):** fix `github.ts` hardwired **repo scope** (it cannot currently see the org-level BLOODRAVEN-2 → add `scope: 'org'` + org endpoints — a prerequisite); **fail-closed provisioning-on-recovery** (`provision-runner.ps1` → `verify-runner-env.ps1` gate before start, so an auto-recovered runner can never return mis-PATHed); **terminal `stopService`** (force-kill a wedged Listener scoped by path); env-sourced PAT + token-file registration + `execFile` arg-arrays; a schema-gated append-only **audit sink** (IDs + gate outcomes only, no PII — #24).

**Security-first (S0):** the fleet found a **live PAT + runner tokens hardcoded in `reconfig-bloodraven2.ps1`** — untracked (no history scrub), now **redacted on disk**; **rotate the `gho_` PAT on GitHub** and audit for unauthorized org-runner registration.

Rejected: **C2** (org-scoped runs/jobs API does not exist → its hang detector is non-functional for the org runner it targets), **C3** (ships a fleet hang detector its own janitor-owner thesis makes permanently dormant; primary fix hypothesis-gated), **C4** (~2wk/5-PR; Phase-0 quarantine creates a security-gate SPOF). Best parts of each grafted into C1.

## Consequences

- **Positive:** one place to fix the recurring Semgrep flake and the runner defects; uniform,
  invariant-respecting security bracket across the fleet; `@ocr/runner-fleet` becomes the single runner
  brain; new spokes get hardened CI by reference, not by copy.
- **Negative / risks:** org-wide blast radius (mitigated by pinned tags + staged rollout + hub CI);
  a migration cost per spoke; a one-time consolidation of the loose scripts.

## References

- OSE runbook: `ourSharedEvents/workers/oursharedevents/docs/ops/ci-runner-watch-and-flake-runbook.md`
- Package: `packages/runner-fleet` (`@ocr/runner-fleet`)
- Invariants: `OCR-docs/ocr-docs-brain/architectural-invariants.yaml`
- Trigger incident: OSE sponsor-payment epic PRs #322 / #323 / #324 (2026-08-13)
- Companion decision log: `docs/decisions/runner-2-remediation-and-runner-flow.md`
