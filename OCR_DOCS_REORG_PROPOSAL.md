# OCR-docs Reorganization Proposal
## Birds-eye pass — April 14 2026

> **Purpose.** Make the org brain easier to read cold. Preserve every fact. No deletions — only restructuring, renaming, and merging of near-duplicates.
>
> **Status.** DRAFT. Nothing is overwritten. All proposed changes exist as `*_v2.md` drafts alongside the originals. Matt approves file-by-file before any replacement.

---

## 1. What I found

### Top-level file inventory (8 files, 1,027 total lines)

| File | Lines | Purpose | Issue |
|------|-------|---------|-------|
| `README.md` | 48 | Public entry point, product table | Clean, but duplicates product registry from VISION.md |
| `CLAUDE.md` | 110 | Claude session protocol, arch boundaries, NCR, CCR | Drifts from VISION.md on two points (flagged by Bloodraven, unresolved) |
| `SKILL.md` | 85 | 5 reusable skills for org-level work | Fine. No change needed. |
| `OCR_STATUS_project.md` | 143 | Status snapshot, maintained by **orc-doc-brain-floss**, as of 2026-04-09 | **Near-duplicate** of PROJECT-STATUS.md, different agent, different date |
| `PROJECT-STATUS.md` | 103 | Status snapshot, maintained by **Bloodraven**, as of 2026-04-12 | **Near-duplicate** of OCR_STATUS_project.md. Newer. Breaks `OCR_*_camelCase` convention. |
| `OCR_LOG_session.md` | 421 | Automated sync log, **orc-doc-brain-floss**, runs appended | **Near-duplicate** of SESSION-LOG.md |
| `SESSION-LOG.md` | 117 | Automated sync log, **Bloodraven**, 2026-04-12 run | **Near-duplicate** of OCR_LOG_session.md. Breaks naming convention. |
| `docs/OCR_VISION.md` | 230 | Org-level source of truth | Content is right. Structure wanders (see §3). |

### The two real problems

**A. Four files, two jobs.** Status reporting and session logging each have two files written by two different agents (Bloodraven, orc-doc-brain-floss). A first-time reader cannot tell which is authoritative. Naming is inconsistent (`OCR_STATUS_project.md` vs `PROJECT-STATUS.md`).

**B. VISION.md reads like memory, not architecture.** The content is all correct, but sections mix concerns (doctrine + business model + social mission), the product registry is a 75-line wall of indented prose instead of a scannable table, and the "Documentation as code" paragraph is one long run-on sentence stacking four separate ideas.

The docs/ subfolder structure (decisions/, standards/, corridors/, releases/, prompts/, ccr-gates/) is clean. Nothing to change there.

---

## 2. Proposed target state

### Top-level (after reorg)

```
OCR-docs/
├── README.md              # Public entry point. One screen. Points to everything.
├── CLAUDE.md              # Claude session protocol. Aligned with VISION.
├── SKILL.md               # Unchanged.
├── OCR_STATUS_project.md  # MERGED. Single status file. Any agent writes here.
├── OCR_LOG_session.md     # MERGED. Single append-only log. Any agent writes here.
├── docs/
│   ├── OCR_VISION.md      # Rewritten for scannability. All content preserved.
│   └── (existing subfolders unchanged)
├── CCR/
├── Prompts/
├── skills/
└── templates/
```

### Files that go away

| Remove | Content migrated to | Why |
|--------|---------------------|-----|
| `PROJECT-STATUS.md` | `OCR_STATUS_project.md` (as a second snapshot section) | Duplicate purpose. `OCR_*` naming wins. |
| `SESSION-LOG.md` | `OCR_LOG_session.md` (appended as Bloodraven entries) | Duplicate purpose. `OCR_*` naming wins. Log is already append-only. |

Nothing is lost. Both files get merged into the `OCR_*` versions.

---

## 3. VISION.md — specific restructure

Current order (230 lines):

1. One sentence → 2. What this is → 3. End goal → 4. Founding doctrine → 5. Product registry (prose) → 6. Founding corridors → 7. NCR methodology → 8. Documentation as code (run-on paragraph) → 9. Archive commitment → 10. Open decisions

Proposed order (same line count approx, content preserved, scannable):

1. **North star** — the one sentence, unchanged
2. **What OCR is** — dual nature (experiment + business), preserved verbatim
3. **End state** — the "not a million dollars" section, preserved
4. **Founding doctrine** — OCR brings framework, community brings knowledge
5. **Archive commitment** — data ownership, preserved verbatim *(promoted up from bottom — it's doctrine, not a footnote)*
6. **Product registry** — rewritten as a **table with one-line summaries**, with per-product detail paragraphs immediately below for anyone who wants depth. All current prose preserved; just regrouped.
7. **Founding corridors — June 1 2026** — already in good shape, minor formatting cleanup
8. **NCR methodology** — tightened, still points to LOCKED_NCR_Methodology_v1.3
9. **Documentation as code** — the run-on paragraph broken into 4 bullets (one per idea), same facts
10. **Open decisions** — preserved
11. **Footer** — owner/status/last updated

### The two unresolved CLAUDE.md drift items

CLAUDE.md currently asserts two things VISION.md doesn't:
- "OSE + OW converge into one service under the OCR moniker"
- "All product data flows to BigQuery. OER accesses via RAG."

Bloodraven flagged both in SESSION-LOG on 2026-04-12. Neither is resolved.

**In VISION_v2 I did NOT add these claims to the source of truth** — adding them requires a Matt decision. Instead, I added both to the **Open decisions** section so they stay visible and get resolved deliberately, not accidentally. CLAUDE_v2 softens the language to match (presents them as architectural direction pending VISION ratification).

---

## 4. CLAUDE.md — what changes

Current CLAUDE.md has good bones but overlaps VISION.md (product table, corridors, NCR, archive commitment all appear in both). That redundancy means a change in one can drift from the other — which is exactly what happened.

CLAUDE_v2 keeps **only what Claude needs for a session**:
- Session protocol (read VISION → understand → execute)
- Arch boundaries (one-screen, explicit rules, the actionable part)
- CCR protocol (one-screen, because it governs every artifact)
- DAC checklist (which files every product repo must have)
- Open questions (pointer to VISION.md open decisions)

The product line description, corridor list, and archive commitment are **removed from CLAUDE_v2** in favor of a pointer: `See docs/OCR_VISION.md §6 (Product registry), §7 (Corridors), §5 (Archive commitment).`

Net effect: CLAUDE.md goes from 110 lines to ~60. No duplication. When VISION.md changes, CLAUDE.md doesn't need to change.

---

## 5. README.md — what changes

Current README.md has a product table, key docs table, and the one-sentence mission. It is 48 lines — already tight.

README_v2 is trimmed to ~30 lines:
- The one sentence
- What this repo is (2 sentences)
- Where to start (pointer to VISION.md as the real entry)
- Product line (same table, shorter purpose column)
- Key documents (same table)

Kept simple because GitHub renders this file first for anyone landing on the repo. It should orient a stranger in 10 seconds.

---

## 6. Naming convention — the pattern

Matt's files overwhelmingly follow `OCR_<TYPE>_<subject>.md` camelCase (OCR_VISION, OCR_STATUS_project, OCR_LOG_session, OCR_STANDARD_*, OCR_DECISION_*, OCR_PROMPT_*, OCR_CHECKLIST_*, OCR_RELEASE_*, OCR_GATE_*). The outliers — `PROJECT-STATUS.md` and `SESSION-LOG.md` — use SCREAMING-KEBAB and were almost certainly auto-generated by Bloodraven without convention awareness.

Merging them into the `OCR_*` files restores a consistent convention across the entire repo and makes new files easier to name.

---

## 7. What I am NOT touching

- `docs/` subfolders (decisions, standards, corridors, releases, prompts, ccr-gates) — content is clean, structure works
- `CCR/`, `Prompts/`, `skills/`, `templates/` folders — out of scope for this pass, can be reviewed separately
- `OCR_ADR_001_repoScaffold.md`, `OCR_DEPENDENCY_crossRepo.md` in `docs/` — specific engineering artifacts, not birds-eye concerns
- `uec-system.jsx`, `dashboard/` — code/tool assets, not documentation
- `LOCKED_NCR_Methodology_v1.3` — explicitly locked per VISION.md

---

## 8. Delivery — what I'm producing in this pass

| File | Status | Purpose |
|------|--------|---------|
| `OCR_DOCS_REORG_PROPOSAL.md` | This file | The birds-eye plan |
| `docs/OCR_VISION_v2.md` | DRAFT | Restructured VISION, all content preserved |
| `CLAUDE_v2.md` | DRAFT | Session protocol, de-duplicated |
| `README_v2.md` | DRAFT | Trimmed entry point |

**NOT produced in this pass** (intentional — flagged for a second approval):
- Merged `OCR_STATUS_project_v2.md` — mechanical merge of the two status files. Low-risk but better done after you confirm which version of duplicated content is authoritative (they have different dates and different numbers).
- Merged `OCR_LOG_session_v2.md` — same reason, plus the file is already 421 lines and merging SESSION-LOG adds another 117. Want your sign-off on the merge policy first.

---

## 9. Approval gates

Please review in this order:

1. **This proposal** — agree with the plan?
2. **`OCR_VISION_v2.md`** — read it against the current file. Anything missing?
3. **`CLAUDE_v2.md`** — does the slimmed-down version still give Claude what it needs?
4. **`README_v2.md`** — does the landing experience work?
5. **Status and log merge** — after the above, I'll produce those consolidations.

Once you approve a file, I'll replace the original and delete the `_v2` suffix. Nothing gets overwritten without a green light.

---

---

## 10. Iteration log

### 2026-04-14 — Architecture layer added (Matt)

Matt added two first-class architectural concepts to VISION_v2 after the initial draft:

1. **§6 Architecture** promoted to a top-level section of VISION.md. Contains:
   - **§6.1 Architecture layer** — the four-file DAC pattern (CLAUDE.md, OCR_VISION.md, README.md, SKILL.md) reframed as architectural invariant rather than documentation habit.
   - **§6.2 Invariant layers** — taxonomies and contracts stable across deployments.
     - **§6.2.1 Sponsors** — canonical 9-vertical enum (Bars, Schools, Hospitals, Recreational Centers, Business Meetings/Conventions, Sports, Art/Cultural, Political Rallies, Research Opportunities).
   - **§6.3 Vertical applications — the OSM + OWL flywheel** — OSM = back of the flywheel (API, skills, CI, institutional knowledge); OWL = front of the flywheel (fork template, onboarding, environment schema). Together they hydrate a vertical app (e.g., a Schools app, a Hospitals app) without bespoke engineering.

2. **Product registry detail for OSM and OWL** updated to reference their flywheel positions (§6.3).

3. **§10 Open decisions** grew to include:
   - Additional invariant layers pending (venues, participants, archive records, data flow).
   - Sponsor vertical completeness check.
   - Which verticals become standalone apps vs. embedded in OSE, and when.

**Impact on the rest of the reorg.** Old §9 "Documentation as code" was absorbed into §6.1 — DAC principles now live under Architecture. Section count stayed at 10. CLAUDE_v2.md needs a pointer update so its architectural-boundaries section references VISION §6 rather than duplicating it (see next iteration).

### 2026-04-14 — OW definition + platform symmetry (Matt)

Matt provided the full OW (OurWKRP) architectural definition. Three substantial changes:

1. **§7 OW detail expanded** — OW is the non-anonymous-ID counterpart to OSE: same architecture, separate DB, named identity, voluntary, free, community-based. Added the Fists-of-5 team unit, the Spotify→Apple-Developer-license trajectory, the DJ profile model (deployed via OWL), the QR-referral → SharedReports pipeline (anonymous OR named per code, Friday cadence, compounding), white-label tiers, anchor (RIPH), and venue targets.

2. **New §6.4 Platform symmetry — OSE and OW** — codifies the parallel-platform rule. OSE and OW share architecture and brand but hold opposite invariants on the identity axis. Side-by-side comparison table. **Resolves the long-standing CLAUDE.md "OSE+OW converge" open decision** — convergence means shared architecture, not merged DBs.

3. **§6.3 OWL flywheel role expanded** — OWL serves at every scale: corridor, vertical, venue, AND individual creator. Every DJ profile is effectively a single-person OWL deployment. The flywheel front works the same way regardless of scale.

**Open decisions updated.** The OSE+OW convergence question is now ✅ resolved. Three new open items added: Apple Developer license status, OW cross-arts expansion roadmap, QR routing rules (anonymous vs. named decision policy). Participants invariant placeholder updated to include Fists-of-5 alongside OSP's tier structure.

**CLAUDE_v2.md updated.** Architectural boundaries section now enforces the parallelism rule, the OW named-identity model, the OWL-at-every-scale rule, and the per-record (not per-database) cross-platform feature rule. Pointer to §6.4 added.

### 2026-04-14 — OER / BigQuery RAG + naming convention as invariant (Matt)

Matt locked in OER's actual identity and elevated naming convention from a reorg observation to an architectural invariant.

1. **§6 Architecture preamble** gained a discipline statement: *"Simplicity over completeness. A leaner layer that products actually consume beats a comprehensive one no one reads."* This is now the orienting principle for the entire architecture section.

2. **§6.1 expanded with file/folder naming as architectural invariant.** The `OCR_<TYPE>_<subject>.md` camelCase pattern, established type vocabulary (VISION, STATUS, LOG, ADR, DEPENDENCY, STANDARD, DECISION, PROMPT, CHECKLIST, RELEASE, GATE), and the canonical `docs/` subfolder taxonomy (decisions, standards, corridors, releases, prompts, ccr-gates) are now binding. Rationale captured: naming is data interoperability — predictable shapes let OER ingestion, sync agents, and cross-repo audits work without bespoke configuration.

3. **New §6.5 Data flow — OER as the BigQuery RAG.** OER's identity is now explicit: BigQuery RAG, set up at the org level. Ingestion sources table (OSE, OW, OWL, OSM, future qualifiers) with what flows from each. Defines the qualifying privacy gate (anonymous-by-construction OR named-with-explicit-voluntary-attribution). States the query model: products do not query each other's DBs directly; they emit, OER ingests, OER answers. Closes with the simplicity discipline applied to ingestion specifically — overkill is the failure mode.

4. **§7 OER detail rewritten** to lead with its real identity (BigQuery RAG layer, set up org-level) and the product table row updated accordingly (data model now reads "BigQuery / RAG" instead of "Derived").

5. **§10 Open decisions:**
   - ✅ The BigQuery question is now RESOLVED.
   - **New:** Define the qualifying privacy gate criteria at field level (which OW records carry consent metadata, how OWL strips client PII, what OSM telemetry is allowed).
   - **New:** OER ingestion threshold — what archive depth triggers activation; per-source schemas, cadence, retention.

**CLAUDE_v2.md updated** to enforce: OER as the universal RAG sink, the qualifying-privacy gate as binding, the naming convention as architectural, and the simplicity-over-completeness discipline. Pointer to §6.5 added.

**Implication for the reorg merge plan.** Matt's emphasis on "proper file name formatting is better" reinforces the merge-and-rename plan in §2 (kill `PROJECT-STATUS.md` and `SESSION-LOG.md` in favor of the `OCR_*_camelCase` versions). The merge is now consistent with VISION.md §6.1 — not just a tidiness pass, but a compliance pass. Still pending Matt's green light to execute.

---

*Drafted: 2026-04-14*
*Author: Claude (birds-eye reorganization pass)*
*Status: DRAFT — awaiting Matt's review*
