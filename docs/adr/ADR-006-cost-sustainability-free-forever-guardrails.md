# ADR-006: Make free-forever a structural property, not a promise — cost-sustainability guardrails

**Status:** Accepted
**Date:** 2026-08-16
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

## Context

The OCR product line makes a **free-forever** commitment to community organizers: the core
ritual/event surface stays free indefinitely, funded by sponsors rather than by charging users. A
promise like that is only credible if it is **structurally** true — if the marginal cost of serving
one more user is bounded near zero by construction, and if nothing can quietly erode that bound
without a gate turning red.

On 2026-08-15 a three-angle, evidence-only cost audit (unit-cost / file-structure / CI-pipeline) was
run against the fleet and synthesized into seven recommendations (**R1–R7**). Its governing finding:

> **Runtime request-handling costs ~0 LLM tokens today.** The served-user path is Cloudflare Workers +
> D1 with no model API in the hot path. Free-forever is therefore *structurally sustainable — but only
> while the runtime stays LLM-free.* The lone model-adjacent module, `src/lib/ai-sanitization.ts`, is
> imported nowhere; it is the **canary**. The day a runtime path imports a model SDK, the unit
> economics invert and the promise breaks silently.

The audit also surfaced three integrity defects that made the promise *look* safer than it was:

1. **A CI false-green (R3).** The `brain-parity` and `shared-gate-drift` jobs could `exit 0` without
   actually running when the OCR-docs brain wasn't at the expected path — a silent pass on the exact
   checks meant to catch drift.
2. **A live invariant conflict (R2).** Sponsor allocation weights were documented as 3×/2×/1× in one
   place while the canonical brain contract (`sponsor-allocation.yaml`) said 7×/3×/1× — a Tier-Equity
   integrity gap.
3. **No cost observability (R5).** There was no telemetry to detect the 10×–100× cost regression the
   canary warns about; the audit was a one-time snapshot with nothing standing behind it.

The remaining recommendations addressed **CI waste with no security value** (R4: duplicate installs,
double-run invariants, cold caches), **a runner single-point-of-failure** (R6: three independent
downstream jobs serialized on one self-hosted executor), and **context/doc structural hygiene** (R7:
root-sprawl reports and >1.3k-line monster docs that inflate the context every agent must load).

This is a fleet-scoped decision: it governs shared CI gates (`security-bracket.yml`, brain-parity),
the shared brain contracts, and a cost posture that every current and future product repo inherits. It
satisfies fleet-ADR criteria 1, 3, and 4 (see `docs/adr/README.md`).

**Non-negotiable constraints, honored throughout:** no security gate was weakened and no re-scan was
removed without an equivalent guarantee elsewhere (the flow-brackets convention — S0 opens / S2 closes
every flow — was preserved on every story); all cost telemetry is **aggregate-only, never-who**
(K-anon: no user, actor, or committer identity may appear in a cost signal); and no user-facing
capability was removed to save money.

## Decision

**Adopt "free-forever by construction" as a fleet posture, and make each load-bearing property of it
an enforced structural invariant rather than a documented intention.** Concretely, the effort was
executed as a five-milestone Linear project — *Cost Sustainability & Free-Forever Guardrails* (OSE
team; Epics OSE-757..761, Features OSE-762..769, 20 stories OSE-770..789 / COST-101..504) — sequenced
**integrity-first**:

| Milestone | Rec | Load-bearing decision | Stories (COST- / OSE-) | Enforced by |
|---|---|---|---|---|
| **M1 — Integrity First** | R1 | Fail CI if any runtime path imports a model SDK; ratify `ai-sanitization.ts` as the *sole* sanctioned AI seam | COST-101/OSE-770, COST-102/OSE-771, COST-103/OSE-772 | T0 invariant `runtime-llm-free.invariant.spec.ts` (allowlist-of-one) + OSE `ADR-014` + CODEOWNERS lock + L7 contract |
| | R2 | Reconcile sponsor weights to the canonical brain contract 7×/3×/1× | COST-111/OSE-773, COST-112/OSE-774 | Brain `sponsor-allocation.yaml` + OSE-336 byte-equiv drift gate |
| | R3 | Make brain absence a **hard fail**; remove the silent `exit 0` false-green | COST-201/OSE-775 | Hardened `brain-parity` + `shared-gate-drift` (self-checkout the brain) |
| **M2 — Efficiency** | R4 | Collapse zero-security-value CI waste (one authoritative install + shared pnpm store; run invariants exactly once) — **never delete a gate** | COST-211/OSE-776, COST-212/OSE-777 | Hub meta-test `packages/flags/tests/ci-workflow.test.ts` |
| | R6 | Relieve the runner SPOF by adding a second always-on org executor; document the topology | COST-221/OSE-778, COST-222/OSE-779 | 2-org-executor fleet (downstream wall-clock 133s→61s, ~2×) + runbook |
| **M3 — Observability** | R5 | Emit an aggregate-only, never-who per-operation cost metric + a committed CI cost-history line | COST-301/OSE-780, COST-302/OSE-781, COST-303/OSE-782 | T0 invariant `cost-metric-never-who.invariant.spec.ts` + L7 contract + `ci-cost-history.jsonl` |
| **M4 — Hygiene** | R7 | Archive superseded root reports; split >1.3k-line monster docs; add a worker-scoped `CLAUDE.md` codifying the hot-path import bans | COST-401/OSE-783, COST-402/OSE-784, COST-403/OSE-785 | T0 invariant `worker-claude-md.invariant.spec.ts` |
| **M5 — Documentation** | synthesis | Canonize the effort: this master ADR, the pooled-audit evidence pack, the 100× scaling watch-item, and the runtime-LLM-free assertion in the test-pyramid standard | COST-501/OSE-786 *(this ADR)*, COST-502/OSE-787, COST-503/OSE-788, COST-504/OSE-789 | Governance review (S2) |

The unifying rule: **a property that protects free-forever is not "done" until a red gate defends it.**
Three of the four load-bearing properties are now T0 structural invariants (runtime-LLM-free,
never-who cost metric, worker-scoped context), each registered in the OSE CI invariants step and
enforced-to-exist by the OSE-350 enforcement-continuity meta-test (`infra-consistency.test.js`); the
fourth (weight equity) is a byte-equivalence drift gate against the brain.

## Alternatives Considered

### Alternative A: Document the free-forever thesis and trust discipline

Write the sustainability thesis (COST-103) and stop there — rely on code review to keep model SDKs out
of the runtime.

**Rejected because:** the canary is *already* in the tree (`ai-sanitization.ts`), and the failure mode
is silent — a single `import` in a hot path inverts the unit economics with no visible signal. A
promise defended only by human vigilance is not a structural property; it degrades to a hope the first
time an agent or contributor adds "just a little summarization." The whole point is to make the
regression *fail a build*, not to ask reviewers to catch it forever.

### Alternative B: Add runtime metering / budget caps to enforce cost

Instrument the runtime to measure token/CPU spend and hard-cap or sample it.

**Rejected because:** it inverts the model. Metering assumes cost exists and must be bounded; our
posture is that cost must be **structurally near-zero to begin with**. Worse, a per-request budget cap
is a user-facing degradation (drop or throttle real traffic to save money), which violates the "no
capability removed to save money" constraint. Sampling a cost signal would also fight the never-who
guarantee (per-user attribution). We chose an aggregate-only *observability* metric (M3) that watches
for regression, not a *control* that degrades service.

### Alternative C: Per-repo ADRs instead of one fleet master ADR

Record each recommendation's decision in the repo it touched (mostly OSE `docs/adr/`).

**Rejected because:** the cost posture is genuinely cross-cutting — it governs shared CI workflows, the
shared brain contracts, and a promise every future spoke inherits at creation (fleet criteria 1/3/4).
Scattering the reasoning across per-repo ADRs would lose the through-line that ties R1–R7 into a single
coherent thesis. Per-repo detail that *is* single-repo (e.g. OSE `ADR-014` for the AI-seam mechanics)
stays where it belongs and is referenced from here.

### Alternative D: One big-bang PR for the whole project

Ship all 20 stories together.

**Rejected because:** shared CI means a bad change reddens every spoke at once; the effort was
sequenced integrity-first (M1 before efficiency) and landed **one ticket at a time**
(build→green→land→next) so each gate change was validated in isolation and no milestone's risk bled
into the next.

## Consequences

### Positive

- **The free-forever promise is now falsifiable.** The day a runtime path imports a model SDK, or a
  cost metric grows a user identifier, or the worker-scoped context bans disappear, a specific named
  T0 gate turns red. The promise is defended by CI, not by memory.
- **The audit is no longer a one-time snapshot.** M3 leaves standing aggregate-only telemetry
  (`OPERATION_COST` runtime line + committed `ci-cost-history.jsonl`) so the 10×–100× regression the
  canary warns about is observable, not merely feared.
- **CI got cheaper without getting weaker.** M2 removed duplicate installs and double-run invariants
  and cut downstream wall-clock ~2× — with a meta-test proving no gate was deleted.
- **The context every agent loads got smaller and truer.** M4 archived dead root-sprawl, split monster
  docs, and pinned the hot-path bans into a worker-scoped `CLAUDE.md` — reducing per-session token cost
  (itself a sustainability line item) while removing drift.

### Negative

- **Ongoing discipline cost at the seam.** Every legitimate future change to the AI seam, the cost
  metric shape, or the worker context now has to move a T0 invariant and clear a CODEOWNERS lock. This
  is deliberate friction — but it *is* friction, and a contributor who needs to touch
  `ai-sanitization.ts` will feel it.
- **The guarantee is only as good as its allowlist.** `runtime-llm-free` is an allowlist-of-one; if a
  future model seam is legitimately added, someone must consciously widen the allowlist rather than
  route around the gate. A lazy widening re-opens the hole.
- **Aggregate-only telemetry has honest blind spots.** `wallMs` is wall-clock (a CPU-ms proxy, not
  true CPU time), `.first()` D1 rows are uncounted (no `.meta`), and external `fetch` subrequests are
  uncounted. The metric detects gross regression, not fine-grained attribution — by design, but a
  reader must not over-trust it.

### Neutral

- The COST- story numbering has intentional gaps (101/102/103, 111/112, 201, 211/212, 221/222,
  301/302/303, 401/402/403, 501–504) while the OSE- issue numbers are contiguous (770–789). The COST-
  scheme encodes milestone/feature; the OSE- scheme is sequential. Neither is an error.
- Three properties became T0 invariants; the fourth (weight equity) is a drift gate rather than a spec,
  because it compares two artifacts for byte-equivalence rather than asserting a code property.

## Implementation Notes

- **Affected repos:** `ourSharedEvents` (runtime + most invariants), the hub
  `ourCommunityRituals/ourCommunityRituals` (shared CI gates, `packages/flags` meta-tests, thesis +
  backlog docs), `OCR-docs` (this ADR). The posture is inherited fleet-wide.
- **Brain contract:** sponsor weights canonical in `OCR-docs/ocr-docs-brain/sponsor-allocation.yaml`
  (7×/3×/1×); reconciled by COST-111.
- **Structural invariants (OSE `tests/e2e/0-architecture/`, all registered in the CI invariants step
  and enforced-to-exist by `tests/integration/infra-consistency.test.js` per OSE-350):**
  `runtime-llm-free.invariant.spec.ts` (COST-101), `cost-metric-never-who.invariant.spec.ts`
  (COST-301), `worker-claude-md.invariant.spec.ts` (COST-403).
- **Contracts / docs:** OSE `docs/adr/ADR-014-ai-sanitization-sanctioned-seam.md` (COST-102),
  `docs/monitoring/COST-METRIC-CONTRACT.md` (COST-303), hub
  `docs/cost-sustainability/FREE-FOREVER-THESIS.md` (COST-103) and `docs/cost-sustainability/BACKLOG.md`.
- **CI hardening:** hub `ci.yml` `brain-parity` + `shared-gate-drift` self-checkout the brain and hard-fail
  if absent (COST-201); hub branch protection enabled with 4 required checks, deadlock-safe for
  docs-only PRs.
- **PRs — OSE:** #328 (101), #329 (111), #330 (102), #331 (112), #332 (222), #333 (301), #334 (303),
  #336 (302), #337 (402), #338 (403). **PRs — hub:** #22 (201), #23/#24 (thesis+backlog), #25
  (211/212), #26 (protection deadlock fix), #27 (222 banner), #28 (401).

## References

- Linear project **Cost Sustainability & Free-Forever Guardrails** (OSE, `e03abc1b-…`); Epics
  OSE-757..761, Features OSE-762..769, Stories OSE-770..789.
- Every COST- story: **COST-101, COST-102, COST-103, COST-111, COST-112, COST-201, COST-211, COST-212,
  COST-221, COST-222, COST-301, COST-302, COST-303, COST-401, COST-402, COST-403, COST-501, COST-502,
  COST-503, COST-504** (= OSE-770..789).
- Hub `docs/cost-sustainability/FREE-FOREVER-THESIS.md` and `docs/cost-sustainability/BACKLOG.md` (the
  evidence + milestone record — COST-502 publishes the full pooled-audit evidence pack).
- Prior fleet ADRs: **ADR-003** (Self-Checking Infrastructure — the L1 machinery these invariants ride
  on), **ADR-005** (shared CI security bracket + runner fleet — the CI substrate M1/M2 hardened).
- OSE `ADR-014` (AI-sanitization sanctioned seam — single-repo mechanics of the M1 guardrail).

## Revisit Criteria

- **A model seam is legitimately added to a runtime path.** If a served-user feature genuinely requires
  an LLM call, this decision's core premise (runtime is LLM-free) no longer holds; the allowlist widening
  must be paired with a new ADR that re-derives the unit economics and states how free-forever survives it.
- **Cost observability shows a sustained regression toward the 10×–100× watch-item** (COST-503): revisit
  whether structural invariants alone suffice or whether a control (not just a metric) is warranted.
- **The fleet migrates off the Workers + D1 substrate**, or a spoke adopts a fundamentally different
  cost model (e.g. always-on compute), invalidating the near-zero-marginal-cost assumption.
- Otherwise: **no expected revisit; this is a foundational posture.**
