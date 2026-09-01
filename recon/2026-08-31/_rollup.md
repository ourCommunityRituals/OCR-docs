# Wave 1 rollup — ourSharedEvents

> **Date:** 2026-08-31 · **Repo:** ourSharedEvents @ `14f5c3b` · **Workers:** all four
> **Reports:** [`ose-drift`](./ose-drift.md) · [`ose-invariants`](./ose-invariants.md) · [`ose-board`](./ose-board.md) · [`ose-posture`](./ose-posture.md)
>
> **Five items for the wave, not five per report.** Every one was independently re-verified by the lead session against the working tree or the Linear API before landing here. One worker finding did not survive that check and was corrected in `ose-board`; one was narrowed in `ose-drift`.

## Gate Queue

**1. Settle whether OSE-349 is fixed. It gates the commercial covenant's only live proof.**
Invariant #5 `tier_equity` has been mechanically enforced at the code-shape and unit layers, and **unproven against a running worker since 2026-05-19** — the T3 Newman covenant assertion (`postman/collections/ose-api.json` §11) is blocked by a CF Access service token. The probe is still in CI at `oursharedevents-ci.yml:1109`, labelled "diagnostic only, does not gate," warning *"fix the service token first."* But commit `96ba467` (2026-08-21) says *"Root cause of the recurring OSE-349/OSE-889 admin-auth failure — a code bug."* Either the fix landed and both the probe and the ticket are stale, or it was partial and the covenant layer is still dark. **Neither report settles it, and it is the single highest-consequence open question in the wave.** One person, ten minutes, one staging run.

**2. The credential-outlives-the-clone pattern is live on both deploy jobs — the third recorded instance of the same class.**
`oursharedevents-ci.yml:723` (`deploy-staging`) and `:1616` (`deploy-production`, on a persistent self-hosted runner) check out with credentials persisted and no `permissions:` block, then run `npm ci`, which executes dependency lifecycle scripts. Repo-wide, `persist-credentials: false` appears exactly once — `conformance-report.yml:70` — with a comment naming this precise exfil surface. The org understands the risk, wrote it up as resolved, and applied the fix to the brain-repo checkout rather than to the two jobs that deploy to production. Case 10 of the case-study pack, a third time. `conformance-report.yml` is the working template; copy it.

**3. The docs point a security reviewer at a file deleted five months ago, while telling them a closed hole is open.**
`docs/security/SECURITY_BASELINE-ROOT.md:52-53` maps both production Cloudflare zones to `worker/src/router.ts`. `worker/` was deleted 2026-04-05 (`0ebbb4b`); the real router is `workers/oursharedevents/src/router.ts`, 1,555 lines. About eleven live docs point into that deleted tree — note it is the **tree**, not one repeated path, so a single find-and-replace will not close it. Simultaneously `CLAUDE.md:139` and `:175` both describe object-level brand scoping as an open gap "tracked in OSE-1080" — which shipped 2026-08-29 as `src/lib/admin-object-scope.ts`. A reviewer following the docs as instructed scopes the wrong file and chases a fixed bug.

**4. A complete 1,847-line red-team suite is wired to nothing.**
`tests/red-team/` holds five specs — auth attacks, data exfiltration, input injection, live rate limiting, security headers — with `npm run test:red-team*` scripts. **No file under `.github/workflows/` references the suite, its config, or its directory.** Invariant #23 is `partial`/"in construction," which undersells it: the tests are written and runnable today. This is the cheapest item in the wave — it is one workflow step from being real enforcement, and it is the exact "guard in scripts, never invoked by CI is theatre" failure invariant #10's own text warns about.

**5. The register does not know about enforcement OSE actually has, so the conformance meter is measuring the wrong denominator.**
`schema-lexicon.ts` + `schema-lexicon.spec.ts` (OSE-801) read the live D1 schema and fail PRs on any identifier tokenizing to a banned term, with ticketed exemptions. `cost-metric-never-who.invariant.spec.ts` seals the cost-metric payload to seven aggregate keys and forbids identifier tokens. Both are PR-blocking. **The register mentions neither** — zero hits for `schema-lexicon` in `architectural-invariants.yaml`. Two register entries are also internally stale: #21's prose says "PARTIAL, not yet wired to CI" while its status says `live` and the code is wired; #25's `test_file` says "planned" for a covenant spec that exists, is 8,887 bytes, and is enforced. The law is out of date in both directions at once.

---

Not promoted, and worth your eye when you have budget: the board report's cycle findings — an Urgent issue whose own text reads "nothing can ship to production until these 5 items are complete," untouched since 2026-08-03 and sitting in the active cycle; a 91-day-overdue Urgent revenue epic that has never left Backlog while its subject area is the most active in the codebase; and a retroactive ticket cancelled 150 seconds after it was filed. See [`ose-board`](./ose-board.md).

## Calibration verdict — Wave 1 passes

The fleet is cleared for Wave 2. The prompts produced signal, not noise: the drift audit did **not** rediscover the dual-Worker problem — it established the problem was fixed five months ago and that the documentation of it is now the live risk, which is the inversion Wave 1 existed to detect.

Three prompt changes before Wave 2, all earned:
1. **`invariant-sweeper`** — add two explicit asks: enforcement present in the repo but absent from the register, and register entries whose prose disagrees with their status field. Both produced this wave's most valuable findings and neither was requested.
2. **`board-reconciler`** — require a search over full commit messages, not subjects, before asserting inactivity. Its one bad finding came from exactly that.
3. **All four** — the verification pass is not optional. Of twenty gate items, one was wrong and one overstated. Both were caught in a single command each. A worker report is a hypothesis until the lead session checks it.
