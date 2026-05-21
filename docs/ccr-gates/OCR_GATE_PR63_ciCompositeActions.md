# CCR Gate Review — PR #63: Shared CI Composite Actions

> **Status:** BLOCKED for spoke adoption — must close the human gate before any spoke consumes these actions.
> **Merge note:** PR #63 itself MAY merge — the actions are additive with zero consumers today. The gate blocks *adoption*, not the merge.
> **Reviewed:** 2026-05-21
> **Reviewer:** CCR run (Scrum Team discipline, SDET / SRE / DevOps focus)
> **Run shape:** 4 loops, escalating Level — Local → Feature → Product → System

---

## A. Setup

**Discipline:** Scrum Team — does this work across all disciplines; are the
units sized, sequenced, and testable for the whole team? Focused through the
**SDET**, **SRE**, and **DevOps** contributions.

**What is under review:** the four shared composite actions and the example
spoke workflow introduced in PR #63 — the hub side of the hub-and-spoke CI
pattern.

**Why it matters:** every OCR spoke's CI pipeline will depend on these
actions. A defect in the hub is a defect in every spoke at once.

**In scope:**

- `.github/actions/universal-checks/` (action.yml + universal_checks.py)
- `.github/actions/identity-contract/` (action.yml + identity_contract_check.py)
- `.github/actions/brain-conformance/action.yml`
- `.github/actions/deploy-spoke/action.yml`
- `.github/examples/spoke-ci-reference.yml`

**Not in scope:** the internals of `check_brain_contract.py` and
`security_gate.py` — pre-existing, separately tested. This review covers how
the actions *invoke* them, not what they do.

**Who needs to approve:** Matt (PO / human gate).

---

## B. The Loops

### Loop 1 — Surface Pass · Level: Local

The action.yml files and bundled scripts in isolation.

**Critical — most dangerous assumption.**
The actions have never executed in CI — not once. Local smoke testing
covered the *Python logic* (`py` on Windows). The `action.yml` orchestration
layer is entirely unverified: `pwd -W` mixed-mode path resolution, and
`actions/setup-python` / `actions/setup-node` running *inside a composite
action* on the self-hosted Windows runner.

**Conservative — worst case if wrong.**
The first spoke to adopt gets a hard red CI on its first run. The failure
surfaces in the *spoke's* Actions tab, so it reads as the spoke's own bug.
Failure attribution is wrong, the rollout stalls, and trust in the hub
pattern erodes on day one.

**Recursive — score.** 78% — baseline.

- **SDET:** zero test coverage of the action.yml layer. No `actionlint`. The
  Python checkers were exercised on a single OS path.
- **DevOps:** `setup-node` is used nowhere in this repo's existing workflows
  (`docs-ci.yml` assumes Node is pre-installed). `setup-python` is proven at
  *job* level (`brain-validate.yml`) but not inside a *composite* action.

Decision: 78% < 95% → findings become the pressure input to Loop 2.

### Loop 2 — Pressure Pass · Level: Feature

The full pipeline wiring — the example workflow, chained jobs.

**Critical — assumed solved, never verified.**
The example itself. `spoke-ci-reference.yml` pins the actions at `@main`, but
the actions are not on `main` until PR #63 merges — circular for any spoke
adopting early. And `concurrency: cancel-in-progress: true` would cancel a
deploy job mid-`wrangler deploy`.

**Conservative — does the floor hold?**
No. `identity-contract`'s FAIL-level checks (A-7 named-auth coupling, I-4
insecure cookie) have no allowlist or inline pragma. `security_gate.py` ships
a `security-gate: allow <check>` pragma for exactly this reason. A
pure-anonymous spoke (OSE) containing the substring `firebase/auth` or
`spotify_user_id` *anywhere* — a test fixture, a mock, even a comment saying
"we deliberately do not use firebase/auth" — gets a hard FAIL with no escape
hatch. A partial fix that produces false documented closure is the
Conservative-layer anti-pattern by name.

**Recursive — score.** 74% — down 4 from Loop 1. A systemic finding (every
anonymous and `both` spoke is exposed). The drop is the protocol working: new
risk was uncovered that Loop 1 did not see.

- **SDET:** the no-pragma false positive is systemic, not isolated — per
  protocol, scope the full surface before any partial fix.
- **SRE:** `cancel-in-progress` killing an in-flight deploy can leave a
  half-published Worker.

### Loop 3 — Confirmation Pass · Level: Product

One spoke (OW) adopting the full pipeline end to end.

**Critical — rationalizing or verifying?**
Rationalizing, and caught: the prior reasoning was "the spoke runs its tests
before deploy, so deploy is safe." But health-check failure modes — cold
start, edge propagation, regional rollout — are precisely the deploy-time
risks that pre-deploy tests cannot catch. `deploy-spoke` deploys, runs the
health check, and on failure **cannot recover**: there is no `wrangler
rollback`, no captured prior deployment id, no documented manual path. The
bad version is already live and serving.

**Conservative — would I defend this if it shipped and broke?**
No. A DJ-facing OW Worker pushed broken on a Friday with no rollback is
indefensible.

**Recursive — score.** 80% — up 6 from the Loop 2 dip. The rollback gap is
now named and has a known fix; confidence rises because the unknown became a
known.

- **SRE:** the template's own DevOps/SRE question — "is it recoverable?" —
  answers *no*. This is the hardest finding in the run.
- **SDET:** the health check asserts HTTP 200 only. A stale 200 served by the
  *old* version passes the check; it does not prove the *new* build is live.

### Loop 4 — Confirmation Pass · Level: System

All spokes on the hub-and-spoke pattern — blast radius.

**Critical — still rationalizing anything?**
`@main` is a mutable ref. A single bad commit to OCR-docs `main` red-CIs
every spoke simultaneously. There is no `v1` tag, no changelog, no
deprecation path — renaming an input on `universal-checks` silently breaks
every consumer at once.

**Conservative — defensible under the worst case?**
A refactor of `universal_checks.py` argument names, merged to `main`,
instantly breaks the whole fleet's CI. The hub has no canary and no self-test
gate of its own. The fleet-wide coupling is *intended* (the propagate-
standards philosophy — spokes follow the hub), but intent does not remove the
need for a mitigation: tag the actions, have spokes pin tags, and gate the
hub with a self-test.

**Recursive — score.** 82% — stable with Loop 3.

- **DevOps:** needs action versioning (`v1` major tag) and an OCR-docs
  self-test workflow that exercises all four actions on every PR touching
  `.github/actions/**`.

---

## C. Results

### Loop Summary

| Loop | Level   | Score | Key finding |
| ---- | ------- | ----- | ----------- |
| 1    | Local   | 78%   | Actions never executed in CI; runner assumptions unverified |
| 2    | Feature | 74% ↓ | FAIL-level checks have no pragma → systemic false-positive risk |
| 3    | Product | 80% ↑ | `deploy-spoke` has no rollback — not recoverable |
| 4    | System  | 82%   | `@main` mutable ref = fleet-wide blast radius, no versioning |

**Confidence decay check:** 78 → 74 → 80 → 82. Dipped at Loop 2 (protocol
working — systemic risk uncovered), recovered, then plateaued at **82%**.
**Never crossed the 95% gate.**

### Verdict

**BLOCKED for spoke adoption.** The output does not earn "CCR Verified"
status. The score sits in the 70–84% band — scope mapped, gaps named, gaps
open.

PR #63 may still merge to OCR-docs `main`: the actions are additive and have
zero consumers today, so merging the hub side is low-risk. The gate blocks
*adoption by any spoke*, not the merge.

### Human Gate — what must be true before adoption (SCRUM backlog)

| Story | Role        | Size | What | Gate type |
| ----- | ----------- | ---- | ---- | --------- |
| G1 | SDET / DevOps | S | Live smoke run of all four actions on BLOODRAVEN — prove `pwd -W` resolution and composite `setup-python` / `setup-node` work on the self-hosted runner | **Human** — needs runner access |
| G2 | SRE         | M | `deploy-spoke`: add `wrangler rollback` on health-check failure, or capture the prior deployment id (`wrangler deployments`) and document a manual rollback procedure | Code |
| G3 | SDET        | M | `identity-contract`: add a `ccr: allow <rule>` pragma / allowlist to the FAIL-level checks, mirroring `security_gate.py`'s `security-gate: allow` mechanism | Code |
| G4 | DevOps      | M | Tag the actions `v1`; repoint the example from `@main` to `@v1`; add an OCR-docs self-test workflow that runs all four actions on every PR touching `.github/actions/**` | Code + process |

**Sequence:** G1 first — cheapest and de-risks the most; if composite actions
cannot run on the runner at all, G2–G4 are moot. Then G3 (false positives
block adoption hardest) → G2 (deploy is the final stage; spokes can adopt the
check actions before the deploy action) → G4 (required before broad rollout,
not before a first pilot).

### Risks accepted (for the merge of PR #63 only)

- **Hub merge with zero consumers** — accepted. The actions are additive;
  nothing invokes them until a spoke opts in. Merging the hub side now lets
  G2–G4 land as normal follow-up PRs against `main`.

### Verification after the gate closes

- [ ] G1 smoke run is green on BLOODRAVEN for all four actions.
- [ ] A pilot spoke (OW) runs the full reference pipeline green on a real PR.
- [ ] `identity-contract` proven not to false-FAIL on a spoke carrying a
      benign forbidden-token string in a test fixture.
- [ ] A forced health-check failure in `deploy-spoke` triggers a verified
      rollback.

---

## D. Prompt provenance

Per CCR §4 "Prompts are data": this gate was produced by the instruction
*"Run a 4 level CCR run with full SCRUM focusing on the SDET / SRE and DevOps
contributions"* against PR #63. The run reached 82% and stopped at the human
gate — an honest sub-threshold result, not a manufactured pass. The four
human-gate stories are the iteration path: they name where the PR #63 build
was under-specified (runner verification, rollback, pragma, versioning).

---

*Status: BLOCKED for spoke adoption pending G1–G4.*
*Reviewer: CCR run — Scrum Team discipline, SDET / SRE / DevOps focus.*
*Final confidence: 82% — below the 95% ship gate.*
