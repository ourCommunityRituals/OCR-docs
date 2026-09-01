# Recon prompt changelog

> **What this is.** The loop's memory. Every change to a worker prompt, the finding
> that earned it, and the round it takes effect. Without this file each round
> re-learns what the last one knew, and the fleet's memory lives in the operator's
> head — the thing the runbook (§6) exists to replace.
>
> **Rule.** A prompt change lands here *with its evidence* or it does not land. "This
> would probably help" is not an entry. A finding that a round produced, or failed to
> produce, is.

---

## Round 1 — Wave 1, ourSharedEvents, 2026-08-31

Four workers, twenty gate items, two corrections. Three prompt changes earned.

### 1.1 `invariant-sweeper` — add two asks it was never given
**Earned by:** the two most valuable findings of the wave came from directions the
prompt did not request.
- OSE has `schema-lexicon.ts` + `schema-lexicon.spec.ts` (OSE-801) and
  `cost-metric-never-who.invariant.spec.ts`, both PR-blocking. The register mentions
  neither — verified, zero hits for `schema-lexicon` in `architectural-invariants.yaml`.
- Invariant #21's `activation_note` says "PARTIAL, not yet wired to CI" while its
  `status` says `live` and the code is in fact wired. #25's `test_file` says "planned"
  for a spec that exists at 8,887 bytes and is enforced.

**Change:** add to §1.2 of the runbook, as explicit numbered asks —
1. *"Report enforcement present in the repo but absent from the register."*
2. *"Report register entries whose prose and status field disagree."*

**Why it matters:** the agent was built to find prose-without-enforcement. It also
found enforcement-without-record and record-that-contradicts-itself. The register is
wrong in **both** directions, which means every conformance percentage computed from
it rests on a denominator that does not match the estate.

**Effective:** round 2.

### 1.2 `board-reconciler` — search commit messages, not subjects
**Earned by:** the wave's one wrong finding. The agent reported OSE-349 as *"In
Progress since 2026-05-19, zero commits in 104 days."* A search over full commit
messages returns `96ba467` (2026-08-21), body: *"Root cause of the recurring
OSE-349/OSE-889 admin-auth failure — a code bug."* The finding inverts: not abandoned
work with a stale ticket, but completed work with a stale ticket in front of it.

**Change:** add to §1.3 — *"Before asserting inactivity, search full commit messages
(`--grep` over the message body, not the subject). State which search you ran."*

**Effective:** round 2.

### 1.3 All workers — absolute repo path and `git -C`
**Earned by:** `board-reconciler` self-reported git output that did not resolve in
ourSharedEvents. Verified: `git cat-file -t 0b3b646` fails there. The commits were the
**lead session's own hub commits**, reached because the worker's shell defaulted to
the lead's working directory. The worker caught it and discarded it, so no artifact
was corrupted.

**Change:** every worker prompt states the absolute path of the repo under scan and
requires `git -C <path>` for every git call. Never a bare `git`.

**Why it matters beyond hygiene:** this is the R3 mechanism. Here it crossed a
harmless boundary (hub → OSE). In a session holding both ourSharedEvents and ourWKRP
the same default cwd would cross the legal wall silently. R3's "separate sessions,
separate invocations" is not belt-and-braces — it is the only thing standing between
a default working directory and a wall breach. Attachment is the boundary, not
instruction.

**Effective:** immediately, all rounds.

### 1.4 Not a prompt change — the verification gate is mandatory
Twenty gate items, one wrong (1.2) and one overstated (~11 docs point into a deleted
*tree*, not 9 repeating one *path* — the distinction matters because find-and-replace
won't close it). Both caught in a single command each.

**Standing rule, not a prompt edit:** every claim leaving a worker gets one command
run against the tree or the API before it enters an artifact. A worker report is a
hypothesis until the lead session checks it. Recorded here because it is the cheapest
high-value habit the loop has, and the round that skips it will not notice.

---

## Round 2 — Waves 3 + 4, six spokes, 2026-09-01

**No workers dispatched.** Six repos measured directly: five byte-identical
documentation scaffolds (31 files, 0 code files, 27 markdown), one nearly empty repo
(2 files, dormant since 2026-04-19). Dispatching would have produced ~30 reports whose
common content is "this repo contains no code."

### 2.1 All waves — trigger on condition, not on calendar
**Earned by:** the wave list scheduled six repos that a two-command measurement closed.

**Change:** before any dispatch, per repo —
- `git ls-files '*.ts' '*.js' '*.py'` returns zero → no wave. Re-open when it doesn't.
- HEAD unchanged since the last recon → no wave.
- Otherwise → only the lenses that have an object in that repo. Not all of them, every time.

**Why it matters:** this rule would have closed both waves before the first clone, and
it scales as repos gain code without anyone maintaining a schedule.

**Effective:** round 3.

### 2.2 `invariant-sweeper` — check the register's scope against reality
**Earned by:** `applies_to` assigns 18 invariant-surface pairs to repos containing zero
enforceable code between them — 8 to `osm`, 7 to `oaw`, 1 each to `osr`, `osg`,
`oureventring`. Invariant #14 `mobile_workability` is scoped to two documentation
repos; #4 `ncr_data_accumulation` to a repo holding a README.

**Change:** add — *"For each invariant scoped to this repo, state whether the repo
contains any code capable of violating it. A surface that cannot carry the invariant
is a register defect, not a repo finding."*

**Effective:** round 3.
