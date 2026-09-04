# ADR-008: Consolidate the OSE and OW workers into the hub monorepo — after the launch window, and without merging databases or identity

**Status:** Proposed
**Date:** 2026-09-04
**Deciders:** Matt (Co-Architect convener)
**Scope:** Fleet-wide (repository topology)
**Supersedes:** None
**Cross-refs:** ADR-001 (Docs-as-Code Scaffold), ADR-002 (Identity-Profile-Keyed Invariants), ADR-005 (Shared CI Security Bracket and Runner Fleet)

---

## Context

The founder asked the operative question directly: *"Am I making this a bigger pain by having OW and OSE in separate repos, if I'm just going to have a hybrid?"*

The premise worth separating first: **the identity boundary is not what the separate repositories buy.** OSE-anonymous and OW-named are held apart by three mechanisms, none of which is a repository split — separate D1 databases, the choice-token boundary (ADR-002), and CI invariant gates. OSE already enforces a two-database split *inside one worker* (`DB` / `FORMS_DB`, `tests/architecture.spec.ts`). Repository topology is orthogonal to Invariant #1.

What the split *is* costing, measured on 2026-09-04 against live checkouts:

1. **The shared packages have silently forked.** `ourSharedEvents/packages/` is a vendored copy of the hub's `packages/`. Comparing source trees, ignoring line endings: **`@ocr/ui` 16 of 22 files differ, `@ocr/flags` 7 of 9, `@ocr/data-provider` 1 of 1** — 24 of 32 files — while *both* copies are stamped `"version": "0.1.0"`. The version says identical; the code is not. There is no gate that catches this.
2. **OW cannot build without a second repository and an org secret.** `ourWKRP/package.json` declares `"@ocr/ui": "file:../packages/ui"`, a path outside the repo that does not resolve in a plain checkout. CI compensates by cloning the private hub with `OCR_PROPAGATE_TOKEN` (`scripts/ci-stage-ocr-workspace.sh`). A spoke's build therefore depends on cross-repo credentials.
3. **Propagation is a standing tax.** Twelve `chore: propagate OCR-docs standards update` commits across OSE and OW in the last 30 days; `.ocr-standards` vendored into both spokes; three copies each of `CLAUDE.md`, `README.md`, `SKILL.md`; **OW-128 exists solely to hand-port OSE's CI gates into OW**; 30 workflow files across three repositories.
4. **The failure mode is already visible in the product.** `@ocr/ui`'s own README records the origin: 51,313 characters of duplicated inline CSS across nine OW templates plus a different look inlined in OSE, so *"every UX fix had to be made many times, so it wasn't made."* The 2026-09-03 staging walkthrough found exactly that — the landing page on Tailwind blue while forms, the error page and admin used the platform indigo. The sharper version: **OSE-221 fixed this same drift on the admin surface in May 2026 and its own finding named `#2563eb` as the "Tailwind blue / Landing page accent"** — the landing was identified as the source and left unfixed for four months, because nothing structural connected the two surfaces. Fixed on branch `claude/content-market-fit-site-design-1lj7j8` (2026-09-04), but the structure that produced it is untouched.
5. **The doctrine already claims the target state.** ADR-005 opens by describing the fleet as *"a hub-spoke monorepo"* — the hub is a pnpm workspace, but the spokes are separate repositories consuming it by `file:` path. The word and the topology disagree.

The net: the separation is not producing isolation. It is producing a vendored fork in one spoke, a token-authenticated sibling clone in the other, and a manual propagation loop between all three — the cost of a monorepo without its guarantees.

## The objection that governs this ADR (founder, 2026-09-04)

*"Then we'll start making your whole effort about making CI work."*

Measured rather than assumed. **OSE `main`, last 60 days: 52 commits — 56% CI/test/chore, 37% product feat/fix, 4% docs.** Of the 60 most-recently-touched backlog issues, roughly half are test or pipeline machinery (mutation testing, DAST/ZAP, Schemathesis fuzzing, k-anon metamorphic properties, flake-vs-regression classifiers, per-flow security ledgers, named-job restructures, pw-guarded floors). Meanwhile staging serves one seeded event, a generic hero, and a poster that prints no code.

The objection is therefore not a risk this ADR introduces. It is a description of the present, and this ADR could make it worse. Two constraints follow, and they bind the decision:

1. **Consolidation is justified only as CI *reduction*.** The acceptance test for Phase 1 is a smaller pipeline surface — 30 workflow files across three repositories collapsing to one pipeline with path filters, propagation commits going to zero, `scripts/ci-stage-ocr-workspace.sh` and cross-repo secrets deleted. If a Phase 1 design does not measurably cut CI surface, Phase 1 is wrong and does not happen. The measurement is taken before and after; no reduction, no merge.
2. **Phase 0 is one gate, and it is honestly CI work.** The fork-detection check adds to the pile the founder is objecting to. Its only defense is narrow and must stay narrow: it catches a class of defect that has already shipped to a customer-visible surface (the landing accent, drifted for four months after OSE-221 named its source). CI that prevents a shipped product bug earns its place; CI that raises a sophistication score before the platform has a second real event does not.

**Corollary, outside this ADR's scope but recorded because the evidence demands it:** the queued test-sophistication backlog has overshot the product's stage. Before the Founding Six activate, the load-bearing question is whether a poster on a wall produces an honest report the next morning — not a mutation score trend. Sequencing that backlog behind launch is a separate decision for the founder; this ADR simply refuses to add to it without a reduction to show for it.

## Decision

**Consolidate the OSE and OW application workers into the hub repository `ourCommunityRituals/ourCommunityRituals` as workspace packages — after the Founding Six launch window, not before — while keeping databases, workers, deployments, wrangler configs and the identity boundary strictly separate.** One repository, one lockfile, one copy of the standards, one CI pipeline with per-package job filters; two workers, two database pairs, two domains, two identity models. Before that migration, and starting immediately, the spokes stop vendoring shared packages and consume the hub's canonical copies (Phase 0), so the fork stops widening whether or not the consolidation ever happens.

## Consequences

### Positive

- **The fork closes by construction.** One copy of `@ocr/ui`, `@ocr/tokens`, `@ocr/flags`, `@ocr/data-provider`. A token change is one pull request, not three plus a propagation commit.
- **A design-system fix reaches every surface at once** — the condition `@ocr/ui` was created to produce and has not yet achieved.
- **Propagation commits and `.ocr-standards` vendoring disappear.** The brain's standards live once, beside the code that must obey them (ADR-001's intent, better served).
- **Cross-repo CI credentials disappear.** OW builds without cloning a private sibling with an org secret — a smaller supply-chain and secret-sprawl surface (ADR-005's concern, structurally).
- **The 30-workflow sprawl collapses** to one pipeline with path filters; OW inherits OSE's mature gates by construction instead of by OW-128 hand-porting.
- **Atomic cross-surface changes become possible** — a shared-contract change and both consumers land in one reviewable commit.

### Negative / trade-offs

- **One CI blast radius.** A broken shared package can red the whole pipeline. Mitigation: path-filtered jobs and per-package `pnpm --filter` scoping, which the hub root scripts already use.
- **Larger checkout and longer cold CI.** Real; bounded by caching and filters.
- **Secrets consolidate into one repository.** Cloudflare, Doppler and Spotify credentials for two products in one settings page. Requires environment-scoped secrets per deploy job, not repo-wide.
- **Board and repository stop being 1:1.** Linear keeps separate OSE and OW teams against one repository. Branch naming and the traceability gate (`Closes OSE-###`) must carry the product prefix.
- **History migration is a one-way, risky step.** Requires subtree merges preserving history; a botched attempt is expensive to unwind.
- **Deployment isolation must be re-proved, not assumed.** Two products deploying from one repository need explicit guards that an OW change cannot deploy the OSE worker.

### Neutral / explicit — what this ADR does NOT decide

- **It does not merge databases.** OSE's `DB`/`FORMS_DB` and OW's D1 stay separate instances. Invariant #1 is untouched.
- **It does not merge workers or runtimes.** Two entry points, two `wrangler.toml`, two domains.
- **It does not weaken the identity boundary.** ADR-002's choice-token model and the structurally-impossible join between named rosters and anonymous aggregates are unchanged; "hybrid" continues to mean shared architecture and brand, never merged data.
- **It does not move OCR-docs.** The governance brain stays its own repository (ADR-001).
- **It does not decide the fate of the other spokes** (OSG, OSR, OSP, OSM, OA). They follow or do not on their own evidence.
- **It does not authorize the migration now.** Phase 1 is explicitly gated behind the launch window.

---

## Implementation

**Phase 0 — stop the bleeding (now, no migration).** Delete `ourSharedEvents/packages/` and consume the hub's canonical packages; give OW a resolvable dependency path. Reconcile the 24 forked files first — deciding, per file, whether the hub or the spoke copy is canonical, because some spoke edits are real fixes. Land the `@ocr/ui` / `@ocr/tokens` adoption OSE-231 already scopes, so literal hex values leave the templates. Add a fork-detection gate: fail CI if a vendored `packages/` copy diverges from the hub at the same version.

**Phase 1 — consolidate (after Beverly activation and the Founding Six ignition).** Subtree-merge `ourSharedEvents` and `ourWKRP` into `packages/` (or `apps/`) preserving history; one lockfile; one CI pipeline with path filters; per-environment deploy jobs with isolation guards; archive the spoke repositories read-only with a pointer.

**Phase 2 — retire the propagation machinery.** Remove `.ocr-standards` vendoring, the propagation workflow, and `scripts/ci-stage-ocr-workspace.sh`; close OW-128 as structurally satisfied.

Linear shape: a fleet-level **Initiative** ("Repository topology consolidation") with Phase 0 as a Project under the OSE team, Phase 1 as a Project under OCR-doc, Phase 2 as a small follow-up. Phase 0 stories are independently valuable and survive a decision not to proceed to Phase 1 — that is deliberate.

## Validation

An ADR without a self-check hook is doctrine without teeth (ADR-003). The structural locks:

- **Fork detection (Phase 0, the load-bearing gate).** A CI check comparing any vendored `packages/*` tree against the hub canonical at the declared version; divergence at an equal version fails the build. This is the gate whose absence produced the 24-file fork, and it is worth having *even if Phase 1 never happens*.
- **Deployment isolation (Phase 1).** A test asserting each deploy job's `--config` resolves to exactly one worker, so a change under one product cannot deploy the other.
- **The identity boundary is unchanged and must prove it.** `anonymous-id.invariant.spec.ts`, `tenant-isolation.invariant.spec.ts` and OSE's `architecture.spec.ts` two-database guard must pass, unmodified, on the consolidated tree. If consolidation requires editing an identity invariant, the migration is wrong and stops.
- **CI-surface budget (the Phase 1 go/no-go).** Count workflow files, propagation commits per 30 days, and cross-repo secret usages before and after. Phase 1 merges only if all three fall. This is the founder's objection turned into an acceptance criterion.
- **Standards single-source (Phase 2).** The brain-contract check reads one copy; a re-introduced `.ocr-standards` directory fails the deprecation-lock pattern (Invariant #10).

## Open questions

- **Which copy is canonical for each of the 24 forked files?** Tracked as the first Phase 0 story; must be resolved file-by-file before any deletion, since some spoke-side edits are genuine fixes that the hub lacks.
- **`packages/` or `apps/` for the workers?** Naming only; decide at Phase 1 in the migration story.
- **Do OSG, OSR, OSP, OSM and OA follow?** Deferred; each needs its own evidence. This ADR covers OSE and OW only.
- **Does the OSM + OA flywheel need the spokes to be independently forkable repositories?** OA provisions client instances by fork; if the fork unit must be a whole repository, Phase 1 must define what a client forks from a monorepo. This is the one open question that could invalidate the decision, and it is answered before Phase 1 starts, not during it.

## References

- Measurement, 2026-09-04: `ourSharedEvents/packages/` vs `ourCommunityRituals/packages/` — 24 of 32 source files forked at equal version `0.1.0`.
- `ourWKRP/.github/workflows/ci.yml` (`OCR_WORKSPACE_REPO`, `OCR_PROPAGATE_TOKEN`) and `scripts/ci-stage-ocr-workspace.sh`.
- `ourCommunityRituals/packages/ui/README.md` — the 51,313-character duplication that motivated the shared package.
- `ourCommunityRituals/pnpm-workspace.yaml` — the current rule that spokes are *not* workspace members.
- ADR-005 §Context — the fleet already described as "a hub-spoke monorepo".
- Staging walkthrough 2026-09-03: `docs/discovery/OCR_REFERENCE_stagingWalkthrough_2026-09-03.md` (the landing/forms accent drift).
- Linear: OW-128 (hand-port OSE's gates into OW), OSE-231 (harmonize the landing to the OCR design system), OSE-221 (admin accent drift, Done 2026-05-14 — its finding named the landing as the source).
- **Drift found while writing this ADR:** `pnpm-workspace.yaml` attributes the deferred pnpm-upgrade + dependency-trust work to OSE-1089, but OSE-1089 closed 2026-08-30 on a different scope (27 semgrep findings in the hub). The pnpm hardening is therefore untracked — file it rather than inheriting the stale pointer.
- `docs/OCR_VISION.md` §6.5 (OSE/OW platform symmetry — shared architecture, separate databases).
