# ose-board — OSE Linear team ↔ ourSharedEvents reconciliation

> **Wave:** 1 (calibration) · **Agent:** `board-reconciler` · **Date:** 2026-08-31
> **Team:** OurSharedEvents (`5c81d719…`) · **Cycle 12** (`1ea2ce56`), 2026-08-27 → 2026-09-10, 95 issues / 30 completed
> **Repo:** ourSharedEvents @ `14f5c3b`, 704 commits of bounded history (`fetch --depth=1000`)
> **Two-sided:** both Linear and git were available. Nothing here is one-sided inference.
> **Lead verification:** OSE-541 and OSE-173 re-fetched from Linear directly; the code-side claims re-checked against the tree. See §Verification — one finding is **corrected**.

## Gate Queue

**1. OSE-541 — "Infrastructure Provisioning Blockers" — Urgent, self-declared universal blocker, never started, sitting in the active cycle.**
Its own description opens: *"Nothing can ship to production until these 5 items are complete."* `status: Todo`, `startedAt: null`, `stateHistory` has exactly one entry — Todo since `2026-08-03T12:17:52Z`, last updated `2026-08-06`. It carries Cycle 12's `cycleId` and is parented under OSE-540. **If its own text is true, every issue marked Done in Cycle 12 shipped through a blocker nobody worked.** Either the text is false and should be corrected, or the cycle's Done column is not what it appears to be. Both readings are worth your attention; they cannot both be avoided.

**2. OSE-173 — "EPIC-02: Sponsor Wing — Revenue Pipeline" — Urgent, 91 days past due, never left Backlog.**
`dueDate: 2026-06-01`, `startedAt: null`, `status: Backlog` since creation `2026-04-13`. Labels `SPON`, `REVENUE`. Meanwhile sponsor work keeps shipping *outside* the epic that owns it — `14f5c3b` (OSE-1138, the frequency-not-position covenant, HEAD itself) and `259b1eb` (sponsor lifecycle). The Urgent revenue epic is the furthest thing from the front of the queue, while its subject matter is the most active area of the codebase.

**3. OSE-1046 — the retroactive ticket for an untracked shipped change was cancelled 2½ minutes after it was filed.**
`259b1eb` (2026-08-27) shipped a real schema and behaviour change — `sponsor_business.is_active` soft-delete semantics, two-sided placement acceptance — referenced only by internal migration number `0068`, with no `OSE-####` in subject or body. A ticket was auto-filed against the PR and then moved Done → Canceled inside `2026-08-27T18:50–18:53Z`. The paperwork existed for about 150 seconds. The shipped change remains untracked in practice, and the cancellation is the more interesting fact than the omission.

**4. Roughly 40% of Cycle 12 is unstarted, including 9 Urgent issues.**
Of ~89 non-cancelled issues carrying Cycle 12's `cycleId`, about 37 are `Todo`/`Backlog`. Nine of those are Urgent: OSE-804, OSE-286, OSE-540, OSE-284, OSE-920, OSE-796, OSE-628, OSE-631, OSE-541. Several (OSE-284, OSE-286, OSE-541) date from May–August with no forward motion — pulled into "current cycle" without corresponding work. Additional Urgent issues never pulled into any cycle: OSE-234 and OSE-241 (both Backlog since 2026-04-24), OSE-867, OSE-869, OSE-740 (all created 2026-08-17, all still Backlog) — while Medium/High work (OSE-790, OSE-953) occupies the actual In-Progress slots.

**5. OSE-654 — Urgent, marked Done, headline acceptance criterion has no code behind it.**
Acceptance required *"at least two themes (a neutral default + one example client palette) to prove the swap works"* and *"no raw hex in components."* `packages/ui/src/tokens.ts` implements light/dark mode only, not a swappable brand palette. The identifier `brandThemes` — which `workers/oursharedevents/docs/design/frontend-principles.md` claims OSE-654 shipped — **appears in exactly one file in the repo, and that file is the doc making the claim.** Zero occurrences in any `.ts`/`.tsx`/`.js`. The same doc concedes the no-raw-hex criterion is still violated (`admin.html`, ~172 raw hex). AA-contrast tests do exist (`color-contrast.spec.ts`, `landing-colorblind-safe.spec.ts`), so the story is partly backed — the swap-a-client-theme claim is not.

---

## Appendix

### In Progress with no commit activity in 14 days (cutoff 2026-08-17)
Six In-Progress issues checked. Five are within the window and not violations: OSE-865 and OSE-984 (`625b409`, 2026-08-23), OSE-897 (`32502bb`, 2026-08-27), OSE-953 (`5016aed`, 2026-08-28), OSE-790 (`2e979cd`, 2026-08-25). The sixth, OSE-349, is addressed in §Verification below — the agent's original finding on it does not survive checking.

### Commits with no corresponding Linear issue
- `259b1eb` (2026-08-27) — Gate #3.
- `6e124b0` (2026-08-22), `97f2d8d` (2026-08-19) — CI changes, no OSE reference in subject or body. Infra-only, low stakes.

### Done issues whose acceptance criteria lack test backing
- OSE-654 — Gate #5.
- Spot-checked and **solidly backed**, listed so the absence of a finding is on the record: OSE-878 (`display-sponsor-live.spec.ts`, `display-sponsor-overlay.spec.ts`, `sponsor-journey.spec.ts`) and OSE-661 (`tier-equity.invariant.spec.ts`, `sponsor-lifecycle.matrix.spec.ts`, `sponsor-covenant-authoring.spec.ts`, `sponsors.spec.ts`, `tier-equity-sort.spec.ts`, `sponsor-share-rotation.spec.ts`, `sponsor-scope.invariant.spec.ts`).

### Full unstarted Cycle 12 set (long tail)
OSE-114, -116, -208, -283, -285, -287, -290, -293, -296, -297, -299, -302, -542, -543, -555, -629, -630, -633, -634, -636–641, -795, -802, -815, -826, -892, -1059.

---

## Verification (lead session)

| Claim | Result |
|---|---|
| OSE-541 Urgent, Todo since 2026-08-03, in Cycle 12, "nothing can ship" text | ✅ confirmed — re-fetched from Linear; single `stateHistory` entry, `startedAt: null` |
| OSE-173 Urgent, `dueDate` 2026-06-01, Backlog since 2026-04-13, never started | ✅ confirmed — re-fetched; `startedAt: null`, one `stateHistory` entry |
| `brandThemes` absent from all code, present only in the doc claiming it shipped | ✅ confirmed — one file repo-wide, `frontend-principles.md` |
| `259b1eb` carries no OSE reference | ✅ confirmed |

**CORRECTED — Gate #3 as originally reported ("OSE-349 In Progress since 2026-05-19, zero commits in 104 days") does not survive verification and has been replaced above.**
The agent reported `292c429` (2026-05-19) as the only commit ever mentioning OSE-349. Searching commit messages rather than subjects returns three: `292c429` and `1c966ae` (both 2026-05-19), and **`96ba467` (2026-08-21)**, whose body reads *"Root cause of the recurring OSE-349/OSE-889 admin-auth failure — a code bug."* So OSE-349 is not abandoned work: a root-cause fix landed ten days before HEAD and the ticket was never moved.

That inverts the finding. It is not a stale ticket with no work behind it; it is **completed work with a stale ticket in front of it** — the same failure mode as `ose-drift` Gate #2 and #3, from the opposite direction. Still worth acting on, for a different reason than the one reported. The lesson for the fleet: a `--grep` over subjects is not a search over commit messages, and "no commit activity" claims need the wider search before they are believed.

## Calibration verdict

**Signal, with one caveat now fixed.** Item 5 of the prompt — stated priority contradicted by queue position — is what produced Gates #1, #2 and #4, and it produced them bluntly, which was the instruction. The OSE-349 error is the useful kind: a specific, checkable overclaim that verification caught in one command. Keep `board-reconciler` for Waves 2–6, and add to §1.3 an explicit instruction to search full commit messages, not subjects, before asserting inactivity.
