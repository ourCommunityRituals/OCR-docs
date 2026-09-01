# Proposal — the reconciliation loop as agent rings, not an agent chain

> **Status:** proposal · **Date:** 2026-09-01 · **Evidence:** Wave 1 (`recon/2026-08-31/`), Waves 3–4 (`recon/2026-09-01/`)
> **Question it answers:** can the reconciliation process run as agents, each owning its own part of a loop — Brain → BE → DB → FE → CI/CD → Test Pyramid → Automation Matrix → Results → Dashboard → process → Brain?

**Short answer: yes, but not as that chain.** Mapped one agent per arrow, it fails in two specific ways this session already produced evidence for. Restructured as rings around the brain, it works, and most of it is already built.

## 1. Why the chain shape fails

**The stages named are not peers.** The Shared Brain is *state*, not a stage — every agent reads it and the reconciliation writes it, so it cannot also be a node in the sequence. BE, DB and FE are *surfaces* of one system. CI/CD, the test pyramid and the automation matrix are *one mechanism at three resolutions* — the pyramid is what the matrix enumerates and what CI executes. Results and Dashboard are *projections* of artifacts, not producers of them. A 1:1 agent-per-arrow mapping therefore creates agents that duplicate each other and agents with nothing to do.

**Agents with nothing to do is not hypothetical.** Waves 3 and 4 measured six repos: five byte-identical documentation scaffolds and one nearly empty repo, zero code files between them. A stage-shaped fleet would have dispatched ~30 workers to produce thirty reports whose shared content is "this repo has no code." That is kill condition 6 arriving by construction. The estate has **one substantial application** (OSE), one shared-package hub, and a brain; a per-stage agent for DB or FE has no object in seven of ten repos.

**A chain compounds error; a ring catches it.** Of twenty worker findings in Wave 1, one was wrong (OSE-349 read as abandoned; a search over full commit messages rather than subjects found the root-cause fix ten days before HEAD) and one was overstated (~11 docs pointing into a deleted *tree*, not 9 repeating one *path*). Each took one command to catch. In a chain, stage N consumes stage N−1's output directly, so a bad finding is laundered into the brain and becomes durable memory. **The loop's product is memory, so a wrong entry is worse than a missing one.** Verification cannot be a stage in the sequence — it has to be the boundary between every ring.

## 2. The shape that works

### Ring 0 — the spine (state)
The brain: `architectural-invariants.yaml`, `.ocr-standards/`, and the dated `recon/<date>/` series. Read by everything. **Written only by the lead session** (R2). Not a stage.

### Ring 1 — lenses (parallel, read-only, one repo each)
Six agents, each cutting *vertically* through BE, DB, FE and CI rather than owning one of them. This is what produced signal in Wave 1:

| Lens | The question only it answers |
|---|---|
| `drift-auditor` | Do the docs and the code agree, in both directions? |
| `invariant-sweeper` | Is each invariant MECHANICAL, PROSE, or ABSENT — and what is enforced that the register does not know about? |
| `board-reconciler` | Does declared priority match actual queue position? |
| `posture-scanner` | Dependencies, secrets, agent-trust surface, gate bypasses. |
| `pyramid-tracer` | Does a written test reach a blocking gate, and does a required gate rest on a real assertion? Four traversals. |

Vertical lenses are why a single agent found that OSE's covenant is enforced at four layers in code and unproven against a running worker for three months — a horizontal "test pyramid agent" would have seen the layers and not the covenant.

### The gate — verification (lead, mechanical, non-delegable)
Every claim that leaves Ring 1 gets one command run against the tree or the API before it enters Ring 2 or the brain. Not a review, not a second opinion — a command with an exit code. This is the only defence against the plausible-and-wrong finding, and it is cheap: two corrections out of twenty, one command each.

### Ring 2 — role assessment (parallel, consumes Ring 1's *verified* output)
`ccr-assessor` run once per role — Dr of Security, BE Architect, FE Designer, SR SDET/SRE, DevOps — reading the repo's own `.claude/skills/*.knowledge.md` definitions so the roles are the team's, not a generic reading. Each answers: what do I own, what did recon miss in my domain, **what do I veto**, what is the cheapest risk-moving change, and what must the next round check. The security veto is absolute on exploitable findings. Ring 2 never re-scans; it judges.

### Ring 3 — reconciliation (serial, lead) — **this is the loop closing**
Diff today's artifacts against the previous dated set. The diff, not any agent, is the reconciliation. It emits three things:
1. **Register deltas** — invariants to add, rescope, or retire. Wave 1 and Waves 3–4 already produced a concrete list: add `schema-lexicon` and `cost-metric-never-who`; rescope the 18 invariant-surface pairs assigned to repos with no code; fix #21's self-contradicting prose and #25's stale `test_file`.
2. **Prompt changes** — the learning. Wave 1 earned three: give `invariant-sweeper` two new explicit asks (enforcement absent from the register; entries whose prose and status disagree — both produced the wave's best findings unprompted), and require `board-reconciler` to search full commit messages before asserting inactivity.
3. **The rollup** — five items for the wave, not five per report.

### Projection — the dashboard
`dashboard/dashboard.py` reads the **artifact series**, never the repos. Derived, never authoritative. A dashboard that scans source directly becomes a second, unverified source of truth competing with the brain.

## 3. What makes it a loop rather than a series

A series is dated reports. A **loop** is dated reports where round N changes round N+1's prompts. That mechanism needs one file the brain does not yet have:

`recon/PROMPT-CHANGELOG.md` — every prompt change, the finding that earned it, and the round it takes effect. Without it, each round re-learns what the last one knew, and the fleet's memory lives in the operator's head, which §6 of the runbook says is the thing being replaced.

## 4. Trigger on condition, not on calendar

Waves 3 and 4 were scheduled by a wave list and closed by a measurement. Replace the calendar with a condition per repo:

- `git ls-files '*.ts' '*.js' '*.py'` returns zero → **no wave.** Re-open when it doesn't.
- HEAD unchanged since the last recon → **no wave.**
- Otherwise → the lenses that have an object in that repo. Not all six, every time.

That single rule would have closed both waves before any clone, and it scales as repos gain code without anyone maintaining a schedule.

## 5. Build order

1. `PROMPT-CHANGELOG.md`, seeded with Wave 1's three earned changes. Cheapest, and nothing compounds without it.
2. Ring 3 as an explicit step — the artifact-to-artifact diff. It exists informally in the Wave 1 rollup; make it a procedure.
3. Register deltas from Waves 1, 3 and 4. The register is currently wrong in both directions and every conformance number rests on it.
4. Ring 2 on OSE only. One repo has enough findings to be worth five role lenses; none of the others do yet.
5. The condition-based trigger, replacing the wave list.

Rings 1 and 0 are already built and proven. **Do not build the twelve-stage chain.** Today it would run nine of its stages against repos that contain no code, and its one real target is already covered by five lenses that work.
