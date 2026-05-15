# OCR Current-State Inventory

**Generated:** 2026-05-15
**Scope:** Where "what is true right now" lives across the OCR fleet.
**Purpose:** Input to a routing matrix. Map only; no recommendations.

---

## Section 1 — The 7 Repos (+ workspace root + docs hub)

Path root: `C:\Users\mzdan\dev\ourCommunityRituals\`

| Repo | Owns | Phase | Current branch | Last commit |
|------|------|-------|----------------|-------------|
| `ourCommunityRituals` (root) | pnpm-workspace + `packages/*` (`@ocr/flags`, `ocr-ci-scripts`) + self-hosted CI orchestration | Live (workspace consolidated) | `main` (dirty: `packages/flags/package.json` modified; untracked `.claude/`, `OCR-docs-fix-grep/`) | `bc0eccc feat(ocr-ci-scripts): add product_id aliases to TEAM_ROUTING` |
| `ourSharedEvents` (OSE) | Cloudflare Worker event platform; D1 + FORMS_DB; sponsor/corridor/anonymous-id system. Identity mode: anon | Phase 1 9/10 done (P1-10 = OSE-15 prod launch remains); Phase 2 canceled 2026-04-20; Phase 3 (Firebase+React) backlog | `ourcommunityrituals/ose-272-session-3-cron-materialization` (1 open PR) | `5a81dfb feat(OSE-272): SharedReport cron materialization — Session 3` |
| `ourSharedMagnets` (OSM) | Newman/Postman BE mock/demo/whitelabel engine. Identity mode: both | Stub (CLAUDE.md/README.md/SKILL.md only; no package.json) | `chore/centralize-brain-contract-scripts` | `80b5012 chore(ci): fix copy-paste step label on conformance step` |
| `ourSharedPulse` (OSP) | Unknown (no team in Linear yet) | Scaffold | `feat/brain-contract-check` | `655e5eb Add brain-contract-check using centralized scripts` |
| `ourSharedRecords` (OSR) | Records sibling | Scaffold (0 Linear stories) | `feat/brain-contract-check` | `2f2f37d Add brain-contract-check using centralized scripts` |
| `ourSharedGames` (OSG) | Games sibling | Scaffold (0 Linear stories) | `feat/brain-contract-check` | `2b82d2e Add brain-contract-check using centralized scripts` |
| `ourAirwaves` (OA) | Renamed from OWL/ourWhiteList. Identity mode: non-anon | Scaffold (not yet in Linear) | `chore/centralize-brain-contract-scripts` | `f2e49ef chore(ci): fix copy-paste step label on conformance step` |
| `ourWKRP` (OW) | Personal-network flag-planting platform (DJs/curators/chefs/bands/temporal events). Identity mode: non-anon | RED per 2026-04-12 status; OW-1 scaffold still in progress; 18 stories right-sized to Done; OW-30 boundary gate blocked | `chore/centralize-brain-contract-scripts` | `01548cf ci(security): add S0 Security tier — CodeQL SAST, npm audit, SBOM` |
| `OCR-docs` (docs hub, not a product) | Brain YAML contracts, ADRs(none here), dashboards, standards, CCR gates, propagated workflows | n/a | `chore/brain-invariant-12-runner-readiness` (dirty: `OCR_LOG_session.md`, `OCR_STATUS_project.md`, `dashboard/.gitignore`, `dashboard/README.md`) | `b129c0b feat(brain): invariant 12 - runner_pool_readiness_probe` |

**Fleet count:** 7 product repos (OSE, OSM, OSP, OSR, OSG, OA, OW) + workspace root + OCR-docs hub = 9 surfaces.

**Fleet-wide branch state:** 5 of 7 product repos sitting on shared feature branches (`feat/brain-contract-check` or `chore/centralize-brain-contract-scripts`) — none merged to `main` yet. Only OSE has truly diverged (in-flight OSE-272 work).

---

## Section 2 — Memory Files

Path: `C:\Users\mzdan\.claude\projects\C--Users-mzdan-AppData-Roaming-Linear\memory\`
Index: `MEMORY.md` (~38 entries). 4 categories.

### Project (10)

| Entry | Load-bearing? |
|-------|---------------|
| `project_oursharedevents.md` | LOAD-BEARING — phase truth source for OSE |
| `project_oursharedmagnets.md` | single-use |
| `project_ourwkrp_vision.md` | LOAD-BEARING — only source for OW product vision |
| `project_triangle_architecture.md` | LOAD-BEARING — 4 invariants / 5 personalities referenced fleet-wide |
| `project_tier_axes.md` | LOAD-BEARING — sponsor pricing × flag presets axis split |
| `project_ocr_flags.md` | LOAD-BEARING — anchors `@ocr/flags` package |
| `project_uniform_ci_governance.md` | LOAD-BEARING — 7-repo CI parity rule |
| `project_r2_deferred.md` | single-use |
| `project_registry_driven_dashboard.md` | LOAD-BEARING — anchors `product-registry.yaml` |
| `project_ose_surface_lifecycle_matrix.md` | LOAD-BEARING — doctrine at OSE scale |
| `project_ose_flywheel_coverage_baseline.md` | LOAD-BEARING — 8 gap baseline for SCRUM |
| `project_ose_ccr4_audit_2026_04_25.md` | LOAD-BEARING — 4-loop SCRUM audit results |

### Reference (9)

| Entry | Load-bearing? |
|-------|---------------|
| `reference_linear.md` | LOAD-BEARING — workspace identity |
| `reference_piecesos.md` | single-use |
| `reference_infra_map.md` | LOAD-BEARING — story↔system map |
| `reference_ocr_brain.md` | LOAD-BEARING — pyramid governance pointer |
| `reference_mvp_review_prompt.md` | LOAD-BEARING — invoked daily |
| `reference_app_identity_map.md` | LOAD-BEARING — identity-mode per product |
| `reference_workspace_root.md` | LOAD-BEARING — workspace structure |
| `reference_ose_surface_map.md` | LOAD-BEARING — 9 OSE surfaces |
| `reference_doppler.md` | LOAD-BEARING — secrets convention |
| `user_profile.md` | LOAD-BEARING — user identity |

### Feedback / Doctrine (15)

| Entry | Load-bearing? |
|-------|---------------|
| `feedback_flywheel_doctrine.md` | ⭐ FOUNDATIONAL — every change orients to it |
| `feedback_gate_then_pipes.md` | LOAD-BEARING — derived rule |
| `feedback_flywheel_completion.md` | LOAD-BEARING — 7-step OCR governance |
| `feedback_priority_hierarchy.md` | LOAD-BEARING — Q>S>M>P>F |
| `feedback_security_first_gate.md` | LOAD-BEARING — fleet pyramid rule |
| `feedback_security_unconditional.md` | LOAD-BEARING — S0 CI rule |
| `feedback_self_hosted_only.md` | LOAD-BEARING — CI runner rule |
| `feedback_no_onedrive_paths.md` | LOAD-BEARING — path convention |
| `feedback_private_until_launch.md` | LOAD-BEARING — repo visibility rule |
| `feedback_no_auto_prod_deploy.md` | LOAD-BEARING — deploy rule |
| `feedback_verify_brain.md` | LOAD-BEARING — verification rule |
| `feedback_sweep_evidence_hierarchy.md` | LOAD-BEARING — what counts as proof |
| `feedback_pii_new_columns.md` | LOAD-BEARING — schema rule |
| `feedback_sync_prefs.md` | LOAD-BEARING — md/Linear/PiecesOS sync |
| `feedback_briefing_scope.md` | single-use |
| `feedback_batch_cancel.md` | single-use |

### Feature (0)

No `feature_*.md` entries — feature truth lives in repo `docs/features/*.md` (see OSE) and Linear.

---

## Section 3 — Brain YAML Contracts

Path: `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\ocr-docs-brain\`

| Contract | Gates CI where |
|----------|----------------|
| `architectural-invariants.yaml` | All 7 product repos via `brain-contract-check.yml` (workflow now centralized to scripts in `packages/ocr-ci-scripts`) |
| `flags-contract.yaml` | OSE (runtime-bound via `@ocr/flags`); brain-contract-check across fleet |
| `tier-gates.yaml` | All 7 (brain-contract-check); also touched by OSE sponsor pricing |
| `event-phase-contract.yaml` | OSE (OSE-242 canonical phase resolver) |
| `product-registry.yaml` | OCR-docs dashboard (`sync_stories.py`); single source of truth for sibling list |
| `event-taxonomy.yaml` | OSE (taxonomy resolver) |
| `causal-identification.yaml` | OSE (research) |
| `census-integration-plan.yaml` | OSE |
| `construct-validity-map.yaml` | OSE |
| `corridor-definitions.yaml` | OSE (NCR v2; see ADR-009) |
| `irb-readiness.yaml` | OSE (regulatory) |
| `qualitative-validation-protocol.yaml` | OSE (research) |
| `research-questions-registry.yaml` | OSE (research) |
| `statistical-monitors.yaml` | OSE (research) |

**CI wiring evidence:** every product repo has both `brain-contract-check.yml` + `docs-ci.yml`. Workspace root has `ci.yml`. Brain contracts are loaded via centralized scripts in `packages/ocr-ci-scripts` (Python `check_brain_contract.py`, `open_drift_ticket.py`).

**Workspace root CI** (`.github/workflows/ci.yml`) runs on `packages/**` changes only; Brain parity is one of its gates.

---

## Section 4 — ADRs

Path: `C:\Users\mzdan\dev\ourCommunityRituals\ourSharedEvents\docs\adr\`

### Extant (4)

| # | Title | Status | Date |
|---|-------|--------|------|
| ADR-001 | Anonymous-identity architecture (DB ↔ FORMS_DB separation) | Accepted | 2026-05-14 |
| ADR-002 | Static-invariant gates as the load-bearing CI pattern | Accepted | 2026-05-14 |
| ADR-009 | NCR v2 Geographic Hierarchy & Corridor Model | (no date inspected) | — |
| ADR-010 | Templates = Breadth, Tiers = Depth | (no date inspected) | — |

> README table only lists ADR-001 and ADR-002 as Accepted. ADR-009 and ADR-010 exist as files but are not in the README status table — index drift.

### Planned (per ADR-001 + README "in progress" list)

- **ADR-003** — Cursor pagination over offset (locked by PR #155 invariant gate)
- **ADR-004** — Self-hosted runner pool readiness probe + watchdog architecture (Brain invariant 12)
- **ADR-005** — Co-Architect decomposition pattern: Option-C deferral and the halt-criterion discipline

### Scope rule (per README)

ADRs live only at `ourSharedEvents/docs/adr/`. No ADR directory exists in OSM/OSP/OSR/OSG/OA/OW or in OCR-docs. The README states ADRs are descriptive (the long-form "why"); Brain invariants + CI gates carry the "what" + enforcement; doctrine memory carries principles.

### Adjacent decision artifacts

- `OCR-docs/docs/decisions/OCR_ADR_001_repoScaffold.md` — older "ADR" naming, **not in OSE ADR sequence**. Naming-collision risk.
- `OCR-docs/docs/decisions/OCR_DECISION_mockDataProvider.md` — fleet-level decision doc.
- `OCR-docs/docs/standards/OCR_STANDARD_*.md` (6 files) — fleet-level standards.
- `OCR-docs/docs/ccr-gates/{OSE_GATE_OSE12_acAudit.md, OW_GATE_OW30_boundaryReview.md}` — per-story CCR gate records.

---

## Section 5 — Discovery / Sales / Pricing Artifacts

Path-scoped grep across the workspace (excluding `node_modules`, `actions-runner`, `_work`).

| Artifact | Path |
|----------|------|
| Interview guide (bar owners) | `ourSharedEvents/docs/discovery/INTERVIEW-GUIDE-BAR-OWNERS-2026-05-14.md` |
| Interview template | `ourSharedEvents/docs/discovery/INTERVIEW-TEMPLATE-2026-05-14.md` |
| Target list framework | `ourSharedEvents/docs/discovery/TARGET-LIST-FRAMEWORK-2026-05-14.md` |
| Discovery README | `ourSharedEvents/docs/discovery/README.md` |
| Sponsor pricing | `ourSharedEvents/docs/features/SPONSOR-PRICING.md` |
| (Tier model) | `ourSharedEvents/docs/features/TIERS.md` (per `docs/features/` listing) |

**All discovery and sales-tier artifacts live in OSE only.** None at workspace root, none in OCR-docs, none in other product repos. No `sales/`, `pricing/`, `interviews/` directories anywhere else.

No Linear-linked, dashboard-surfaced, or routing record of these documents exists outside the OSE filesystem.

---

## Section 6 — THE GAPS

### G1. No fleet-wide "where are we" document
There is **no single document** that answers "where are we across the fleet right now?"

- `OCR-docs/PROJECT-STATUS.md` claims to be the org-level snapshot but is dated **2026-04-12** (33 days stale) and lists 0 stories for OSR/OSG and no OSP at all.
- `OCR-docs/OCR_STATUS_project.md` is dated **2026-04-09** (36 days stale) and also predates OA's rename.
- `OCR-docs/OCR_LOG_session.md` is per-session, not fleet-state.
- `OCR-docs/dashboard/*.html` is per-product, not aggregated current-state.
- `MEMORY.md` indexes doctrine + project files but is itself flagged 19 days old.

**Gap:** the snapshot surfaces exist (`PROJECT-STATUS.md`, `OCR_STATUS_project.md`) but neither is wired to update on PR/push events; both went stale within weeks. No routing rule says which one is authoritative.

### G2. No routing rule for "where does a new architecture decision live"
- OSE ADRs at `ourSharedEvents/docs/adr/` (MADR format, ADR-001 through ADR-010 partial).
- Older `OCR_ADR_001_repoScaffold.md` at `OCR-docs/docs/decisions/` (different format, different scope).
- Standards at `OCR-docs/docs/standards/OCR_STANDARD_*.md`.
- Doctrine at `~/.claude/.../memory/feedback_*.md`.
- Brain invariants at `OCR-docs/ocr-docs-brain/architectural-invariants.yaml`.

No document routes between these. ADR-001 References section names some siblings ad-hoc but no canonical "decision goes here, principle goes here, contract goes here" matrix.

### G3. No fleet-wide ADR home
ADRs only live in OSE. No structure for fleet-level decisions (OSM, OW, cross-cutting). Workspace-root `packages/` decisions have nowhere to land as ADRs. `OCR_ADR_001_repoScaffold.md` exists but is not in the OSE ADR numbering, creating a parallel sequence.

### G4. ADR README index drift
ADR-009 and ADR-010 exist as files but the README status table lists only ADR-001 and ADR-002. README is the documented source of truth but is not auto-generated.

### G5. No surfaced map of discovery / sales / pricing artifacts
Discovery + sponsor pricing live in `ourSharedEvents/docs/discovery/` and `ourSharedEvents/docs/features/` only. They are not referenced from:
- `MEMORY.md` (no `project_discovery_*.md` or `reference_discovery_*.md`)
- `OCR-docs/` (no fleet-level discovery hub)
- The dashboard
- Any Brain contract

Asking "what discovery work exists?" requires knowing to look in OSE `docs/discovery/`.

### G6. No tier-axes routing surface
`reference_app_identity_map.md` and `project_tier_axes.md` describe the per-product axis split, but there is no per-product entry showing **what tier mode each repo is in right now** at a routing-matrix level. Only OSE has `SPONSOR-PRICING.md` and `TIERS.md`; OSM/OW/OA tier state lives only in memory files.

### G7. No routing for feature-level "where does this live"
OSE has 19 files in `docs/features/`. No equivalent in OSM/OSP/OSR/OSG/OA/OW. No fleet-wide feature inventory. Feature-name collisions (e.g., SPONSORS lives in OSE feature docs + OCR-docs feature docs?) are not detectable.

### G8. Workspace root has no Linear-style story tracker
`packages/flags/` and `packages/ocr-ci-scripts/` are first-class code surfaces but have no Linear team, no story IDs, no dashboard tile. Work on shared packages exists only as commits on root `main`.

### G9. Two parallel "decision" formats
- OSE: `ADR-NNN-kebab-case.md` (MADR-style)
- OCR-docs: `OCR_ADR_NNN_camelCase.md` (different convention)
Neither references the other; no rule for which to use when.

### G10. Branch-state divergence
5 of 7 product repos are sitting on long-lived feature branches (`feat/brain-contract-check`, `chore/centralize-brain-contract-scripts`) that have not landed on `main`. No surface aggregates "which repos are mid-flight on shared infra changes vs. on `main`."

### G11. OCR-docs working tree dirty + on feature branch
`OCR-docs` is on `chore/brain-invariant-12-runner-readiness` with `OCR_LOG_session.md`, `OCR_STATUS_project.md`, `dashboard/.gitignore`, `dashboard/README.md` modified. The two files purported to be the org-level "current state" snapshots are themselves uncommitted.

---

## Appendix — Quick path reference

- Memory: `C:\Users\mzdan\.claude\projects\C--Users-mzdan-AppData-Roaming-Linear\memory\`
- Brain contracts: `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\ocr-docs-brain\`
- ADRs: `C:\Users\mzdan\dev\ourCommunityRituals\ourSharedEvents\docs\adr\`
- Discovery: `C:\Users\mzdan\dev\ourCommunityRituals\ourSharedEvents\docs\discovery\`
- Features: `C:\Users\mzdan\dev\ourCommunityRituals\ourSharedEvents\docs\features\`
- Standards: `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\docs\standards\`
- Decisions (parallel): `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\docs\decisions\`
- CCR gates: `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\docs\ccr-gates\`
- Dashboard: `C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\dashboard\`
- Workspace CI: `C:\Users\mzdan\dev\ourCommunityRituals\.github\workflows\ci.yml`
- Linear: workspace "OurSharedEvents" (not inspected by this audit)
