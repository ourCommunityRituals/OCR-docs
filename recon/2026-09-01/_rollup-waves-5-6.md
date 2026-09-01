# Waves 5 + 6 rollup — the brain, the hub, and OSE's pipeline

> **Date:** 2026-09-01 · **Workers:** 5 (OSE pyramid; hub posture + pyramid; brain drift + invariants)
> **Reports:** [`ose-pyramid`](./ose-pyramid.md) · [`hub-posture`](./hub-posture.md) · [`hub-pyramid`](./hub-pyramid.md) · [`brain-drift`](./brain-drift.md) · [`brain-invariants`](./brain-invariants.md)
> **Five items for the wave, not five per report.** Every one re-verified by the lead against the tree before landing.
> **Ranked for a pre-data system** — no live events, no attendees, no sponsors. Severity follows what is actually exposed.

## Gate Queue

**1. The fleet's own read-only rail does not exist. R1 is prose.**
Two workers dispatched through the checked-in definitions, asked separately from their audits to report every Bash command and any refusal, independently reported full unscoped `Bash`. One executed `python3 run_all.py`; the other ran `git log --all -p`, `find`, `grep -r`. Neither was refused. The `Bash(git log:*)` scoping is parsed and displayed at registration and **not enforced at call time** — the silent-open direction. Bash writes files, so the six repo-committed definitions carry no mechanical read-only guarantee at all. Nothing was written this round only because the prompts said not to.

First, because it governs every other use of the fleet. Fix: containment comes from the agent type, not from `tools:`. Full evidence in runbook §8.7.

**2. Production is reachable on S0 + T0 alone, through an unprotected tag push.**
`deploy-production` declares `needs: [security, gate]` and nothing else — not staging deploy, not the Newman contract, not E2E smoke, not the T4 functional tier, not the S2 tamper tripwire. It triggers on a `refs/tags/v*` push, and **no tag protection is codified anywhere in the repo**. Merge through a normal PR, push a tag later, ship. Whether any downstream tier ever passed is not checked and structurally cannot be — separate workflow runs, no state carried.

Pre-data lowers the consequence of a bad deploy today; it does not change that the path exists and will be the path when data arrives.

**3. `S2 Post-Execution Security` is a required check that no workflow produces.**
Required in `tools/ci/main-branch-protection.json:7`; the string appears in exactly two places repo-wide, both documentation. The job that emitted it was retired 2026-08-28 and re-homed into `functional-staging`, which `if:`-skips on PRs. Either GitHub still requires the dead context and every PR is stuck pending, or it was edited out-of-band and the versioned source of truth is now fiction — the exact failure its own README exists to prevent. **The drift detector that would catch this is wired into no workflow.** Ten minutes to determine which state you are in; do that before anything else on this list.

**4. The brain asserts LIVE invariants on repos its own checker is told to skip.**
`check_brain_contract.py:405` short-circuits on `code_present: false` — PASS, exit 0, before any check runs. The skip is honest and documented. But `applies_to` binds **status: live** invariants to those same repos: five to `osm` (#1 `anonymous_id`, #3, #10, #11, #12), four to `oaw` (#10, #11, #12, #22). The register defines `live` as *"currently enforced in CI."* The brain claims enforcement and instructs its checker not to look, in the same system.

Two more in the same family: the banned-term lexicon exists nowhere in the register — OSE enforces it, and OSE migrations already cite a number for a law the registry does not contain. And `docs/CHOICE-INVARIANTS.md` is a whole second rule set with real enforcement code that no numbered invariant references, in which **B-4 — "shows the total only, never the split," the "never who, always how many" doctrine almost verbatim — is coded `INFO` and never actually scanned.**

**5. Four of five hub packages, and one whole OSE test tier, are wired to nothing — and one README lies about it.**
Hub: `tokens`, `ui`, `runner-fleet`, `data-provider` all have real test suites that no workflow invokes; `packages/runner-fleet/README.md:100-104` claims a `runner-fleet` job in `ci.yml` that does not exist. Semgrep never runs on hub PRs, and L0 secret scanning covers `packages/flags` only. `publish-flags.yml` has zero `needs:` and can publish `@ocr/flags` from any ref via `workflow_dispatch`. OSE: `tests/red-team/` (1,847 lines) has no CI root, and five of ten raw Playwright call sites lack the zero-discovery guard — including `T0 Gate (invariants)`, a required merge check.

---

## Corrections this wave forced

- **"Wiring the red-team suite is one workflow step" — withdrawn.** Its config targets live staging and needs `ADMIN_KEY`, `X_OCR_INTERNAL` and a seeded `SMOKE_EVENT_ID`. It is blocked on the same credentialed-staging precondition as OSE-349, not on a missing step. Wave 1's rollup called it the cheapest item; it is not.
- **Three items collapse into one root cause.** OSE-349, invariant #5's unproven covenant, and the red-team suite are all waiting on live, credentialed staging. T3 has additionally not run on *any* trigger since 2026-05-19, because it is hard-gated on the Newman job that token blocks. One expired credential silently removed an entire tier. Fix that once; three items move.
- **§8.5 superseded by §8.7.** Registration displaying the scoped `tools:` line was read as partial reassurance. It was not evidence of anything.

## What is actually cheap and unblocked

1. Determine the live state of `S2 Post-Execution Security` (item 3). Minutes.
2. Fix `runner-fleet/README.md`'s false CI claim. One line, zero risk.
3. Wire `tokens:test`, `tokens:check:generated`, `tokens:check:raw` into `ci.yml`'s gate. Scripts exist and work.
4. Register deltas — add `schema-lexicon` and `cost-metric-never-who`; fix `status`/`applies_to` on the code-empty repos; reconcile #21 and #25's self-contradictions.
5. `persist-credentials: false` + a `permissions:` block on OSE's two deploy jobs, copied from `conformance-report.yml`.

Blocked on staging credentials, and therefore not on this list: red-team wiring, OSE-349, invariant #5's covenant proof.

## Fleet economics for this wave

Five workers, ~625k subagent tokens, ~6½ minutes wall clock in parallel, against three repos. Compare Waves 3–4: six repos, zero workers, two commands. The measure-first rule is what made both correct. Recon across the estate is now **complete** — every repo except ourWKRP, which is out of scope by R3 and needs its own session.
