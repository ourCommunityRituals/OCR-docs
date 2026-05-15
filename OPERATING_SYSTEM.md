# OCR Operating System

**Purpose:** One page. Answers the question *"where does X go?"* so output stops fragmenting.
**Not a constitution.** Invariants live in the Brain. Doctrine lives in memory. This document just **routes**.

**Last ratified:** 2026-05-15 (founder, mzdan)
**Relocated:** 2026-05-15 from workspace root → `OCR-docs/` (per self-placement row in §3)
**How to change:** edit + PR + ratify in description. No silent edits.

---

## §1 — The Fleet

| Surface | Owns | Identity mode |
|---------|------|---------------|
| `ourCommunityRituals/` (workspace root) | pnpm-workspace, `packages/*` (`@ocr/flags`, `ocr-ci-scripts`), self-hosted CI orchestration | n/a |
| `ourSharedEvents` (OSE) | Cloudflare Worker event platform; D1 + FORMS_DB; sponsor/corridor/anonymous-id system | anon |
| `ourSharedMagnets` (OSM) | Newman/Postman BE mock/demo/whitelabel engine | both |
| `ourSharedPulse` (OSP) | scaffold | tbd |
| `ourSharedRecords` (OSR) | scaffold | tbd |
| `ourSharedGames` (OSG) | scaffold | tbd |
| `ourAirwaves` (OA) | renamed from OWL | non-anon |
| `ourWKRP` (OW) | personal-network flag-planting (DJs/curators/chefs/bands/temporal events) | non-anon |
| `OCR-docs/` (docs hub, NOT a product) | Brain YAML contracts, fleet-level ADRs, standards, CCR gate records, dashboards, fleet discovery hub, fleet skill specs, **this document**, fleet inventory | n/a |

Fleet authority: workspace root + 7 product repos + 1 docs hub = **9 surfaces**.

---

## §2 — The Five Sources of Truth

Every artifact lands in exactly one of these. If it doesn't fit, ask before inventing a sixth.

| # | Source | Path | Owns |
|---|--------|------|------|
| 1 | **Brain** | `OCR-docs/ocr-docs-brain/*.yaml` | Cross-app architectural invariants. CI-enforced across all 7 product repos via `brain-contract-check.yml`. |
| 2 | **ADRs** | `<repo>/docs/adr/ADR-NNN-kebab.md` (MADR) | Single-repo architectural decisions. Fleet-wide decisions live at `OCR-docs/docs/adr/ADR-NNN-kebab.md`. |
| 3 | **Standards** | `OCR-docs/docs/standards/OCR_STANDARD_*.md` | Fleet-wide engineering standards ("how we do X"). |
| 4 | **Doctrine** | `~/.claude/.../memory/feedback_*.md` | Principles, ratified preferences, "always do X" rules. Runtime layer — every Claude session loads these. |
| 5 | **Code** | the repo itself | The ground truth of what's actually deployed. Everything above describes intent; code is reality. |

**Adjacent layers** (not sources of truth, but related):

- **Linear** — ticket-scope intent + execution state. Authoritative for "what work is in flight."
- **Memory project files** (`~/.claude/.../memory/project_*.md`) — running notes per product. Snapshot, not contract.
- **Features** (`<repo>/docs/features/*.md`) — per-feature design records. Snapshot, not contract.
- **Discovery** (`<repo>/docs/discovery/*.md`) — sales/interview artifacts. See §3 for routing.

---

## §3 — Routing Matrix

> Use this table before creating any new artifact. If you find yourself making a file that doesn't have a home here, **stop and add the row** (via PR to this doc).

| You have… | It lands at… | Why |
|-----------|--------------|-----|
| A cross-app architectural invariant | Brain YAML | CI-enforced across the fleet |
| A single-repo architectural decision | `<repo>/docs/adr/` (MADR) | OSE pattern; extend to all repos |
| A fleet-wide architectural decision | `OCR-docs/docs/adr/` (MADR) | **New.** Replaces the parallel `OCR_ADR_NNN_camelCase` format. |
| A fleet-wide engineering standard | `OCR-docs/docs/standards/` | Already exists |
| A doctrine / "always do X" rule | `memory/feedback_*.md` | Runtime layer |
| A project / product state note | `memory/project_*.md` | Snapshot per product |
| Ticket-scope intent + execution | Linear | Authoritative work tracker |
| A feature design (per-repo) | `<repo>/docs/features/` | Repo-local feature record |
| A discovery / interview artifact (per-repo) | `<repo>/docs/discovery/` | Repo-scoped interview output |
| A fleet-wide discovery hub or sales playbook | `OCR-docs/docs/discovery/` | **New.** Discoverable from any repo. |
| Pricing / tier-axis state | `<repo>/docs/features/TIERS.md` + cross-ref from `memory/reference_app_identity_map.md` | Per-product pricing lives with the product |
| "Where are we right now?" snapshot | `OCR-docs/STATUS.md`, **auto-regenerated** | **New.** Built by `/status-rollup` skill (planned). Lives in OCR-docs because the docs hub is where fleet-level snapshots belong. |
| Fleet operating system / routing matrix | `OCR-docs/OPERATING_SYSTEM.md` (this document) | **Self-placement, 2026-05-15.** Originally drafted at workspace root; relocated to OCR-docs because the matrix routes every fleet-wide artifact type into OCR-docs — incoherent for the matrix itself to live elsewhere. |
| Fleet inventory / gap audit | `OCR-docs/CURRENT_STATE_INVENTORY.md` | **Self-placement, 2026-05-15.** Travels with the OS doc. |
| CCR gate record | `OCR-docs/docs/ccr-gates/` | Already exists |
| One-shot session log | `OCR-docs/OCR_LOG_session.md` | Already exists |

---

## §4 — The Sales → Engineering → Sales Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  SALES SIDE                          ENGINEERING SIDE                       │
│                                                                             │
│  ① Discovery call ───────────► ② Discovery note                             │
│     (bar owner, sponsor,           <repo>/docs/discovery/INTERVIEW-…md      │
│      DJ, chef, band)               OR OCR-docs/docs/discovery/ if fleet     │
│                                                                             │
│                                    ③ Triage to one of:                      │
│                                       • Linear epic (ticket-scope)          │
│                                       • ADR (architectural decision)        │
│                                       • Brain contract (cross-app)          │
│                                       • Standard (fleet-wide pattern)       │
│                                                                             │
│                                    ④ Design (per-session, ratify Qs)        │
│                                       <repo>/docs/features/<NAME>.md        │
│                                                                             │
│                                    ⑤ Implement → PR → CI → merge            │
│                                                                             │
│                                    ⑥ Deploy → staging → smoke → prod        │
│                                                                             │
│  ⑨ Next sales call ◄─────────  ⑧ Measure: SharedReport / dashboard          │
│     (case study,                   anon_id_returns, corridor_density,       │
│      pricing validation,           sponsor_impressions                      │
│      tier signal)                                                           │
│                                                                             │
│                                    ⑦ Pricing/tier update                    │
│  ◄──────────────────────────────── <repo>/docs/features/TIERS.md            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Hand-off rituals** (the arrows in the diagram):

| Arrow | Ritual | Closing test |
|-------|--------|--------------|
| ① → ② | Within 24h of the call: write the discovery note from the template | File exists, references the call |
| ② → ③ | Within a week: triage decides home of each insight | Each bullet in the note has a destination link |
| ③ → ④ | Co-Architect drafts design questions; user ratifies | Design doc has a "Ratified" date in header |
| ④ → ⑤ | Sessioned PRs (≤ 1 PR per session) | PR title links to Linear story |
| ⑤ → ⑥ | Merge → auto-deploy staging → manual smoke → manual prod (per `feedback_no_auto_prod_deploy.md`) | Smoke checklist passes |
| ⑥ → ⑦ | After prod runs ≥ 30d, evaluate pricing/tier against real signal | `TIERS.md` updated with date |
| ⑦ → ⑧ | SharedReports measure what's flowing | Dashboard tile updates |
| ⑧ → ⑨ | Insights re-enter sales talk track | New case study in `OCR-docs/docs/case-studies/` (planned) |

---

## §5 — Cadence

| When | What | Where |
|------|------|-------|
| **Daily** | MVP-readiness review per `reference_mvp_review_prompt.md` | runtime (Claude session) |
| **Weekly** (Friday) | `STATUS.md` regenerated by `/status-rollup` skill | `OCR-docs/STATUS.md` |
| **Per-session** | Commit + PR with explicit Co-Author trailer | per repo |
| **Monthly** | Fleet audit: re-run `CURRENT_STATE_INVENTORY.md`; check for new gaps | `OCR-docs/CURRENT_STATE_INVENTORY.md` |
| **Per launch** | ADR retro: did the design hold? | `OCR-docs/docs/adr/` retro section |

---

## §6 — Anti-patterns (what NOT to do)

- ❌ Create a new top-level doc to capture an insight. Find its home in §3.
- ❌ Restate an invariant in a project memory file. Reference the Brain.
- ❌ Use two ADR formats. MADR (kebab-case) is the only format.
- ❌ Land a feature without an entry in `<repo>/docs/features/`.
- ❌ Run a discovery call without writing the note within 24h. The signal decays.
- ❌ Deploy to prod from a Claude session. Per `feedback_no_auto_prod_deploy.md`, prod deploys are a manual user action only.
- ❌ Skip ratification. Design questions get explicit user `ratify` before code.

---

## §7 — Forward-looking gaps

These are tracked in `CURRENT_STATE_INVENTORY.md` and will close as work proceeds:

| Gap ID | What's missing | Owner | Closes when |
|--------|----------------|-------|-------------|
| G1 | Auto-regenerated fleet `STATUS.md` | Co-Architect | `/status-rollup` skill ships |
| G3 | Fleet-wide ADR home | Co-Architect | First fleet ADR lands at `OCR-docs/docs/adr/` |
| G4 | ADR README index drift | Co-Architect | ADR README auto-regen step added to CI |
| G5 | Fleet-wide discovery hub | Co-Architect | `OCR-docs/docs/discovery/` directory + README |
| G9 | Two parallel ADR formats | Co-Architect | `OCR_ADR_001_repoScaffold.md` migrated to MADR |
| G10 | 5 of 7 repos on shared feature branches | User | Merge the shared-infra branches OR document why long-lived |
| G11 | OCR-docs working tree dirty | User | Commit + push the stale status files |

---

## §8 — Pointers

- **Inventory** (source for this doc): `./CURRENT_STATE_INVENTORY.md` (sibling at OCR-docs root)
- **Brain contracts**: `./ocr-docs-brain/`
- **Fleet ADRs**: `./docs/adr/`
- **OSE ADRs** (template for fleet adoption): `../ourSharedEvents/docs/adr/`
- **Standards**: `./docs/standards/`
- **Fleet discovery hub**: `./docs/discovery/`
- **Skill specs**: `./docs/skills/`
- **Doctrine memory**: `~/.claude/projects/C--Users-mzdan-AppData-Roaming-Linear/memory/`
- **Linear**: workspace "OurSharedEvents"

---

*This document is the smallest possible answer to "where does X go?" It should not grow without a clear reason. If you find yourself wanting to add a section, ask first: can this go in one of the existing homes instead?*
