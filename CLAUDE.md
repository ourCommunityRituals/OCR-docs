# CLAUDE.md — OCR-docs

> **Session protocol**
> 1. Read this file.
> 2. Read `docs/OCR_VISION.md` — the source of truth.
> 3. Execute the task at org level.

---

## What this repo is

OCR-docs is the org brain for OurCommunityRituals LLC. Governance, vision, architecture, and coordination only. **No application code.**

If it is not written in `docs/OCR_VISION.md`, it does not exist at the org level. Do not assert org-level facts that aren't in VISION.md — flag them as drift instead.

---

## Product line — at a glance

| Code | Repo | Data model |
|------|------|------------|
| OCR  | this repo        | Governance |
| OSE  | ourSharedEvents  | Anonymous ID |
| OW   | ourWKRP          | Named identity |
| OSG  | ourSharedGames   | Inherits OSE |
| OSR  | ourSharedRecords | Archive / oral history |
| OSP  | ourSharedPulse   | Human-delivered, tech-optional |
| OSM  | ourSharedMagnets | Developer / franchise |
| OER  | —                | Intelligence / analytics |
| OA  | ourAirwaves     | Deployment / white label |

Full registry with per-product detail → `docs/OCR_VISION.md §6`.

---

## Architectural boundaries

Architecture is the Triangle + the invariants in the brain + 4 governance files per repo. Source of truth lives in code at `ourSharedEvents/tests/e2e/0-architecture/`. This document mirrors what the tests enforce. Full prose in `docs/OCR_VISION.md` (Architecture section).

**The Triangle.** `Sponsor → Event ← Customer` with `SharedReport` derived. Any entity plugs into any corner. The Triangle enforces HOW entities participate, not WHAT they are.

**The invariants.** The list lives in `ocr-docs-brain/architectural-invariants.yaml` (schema 1.2.0): 29 numbered invariants in six groups, of which 17 are live, 10 partial and 2 retired. Method: parse the file and count `invariants[]` by `status`; the ids run 1 to 29. Numbers are never reused or renumbered, and a retired entry keeps its number. Read that file for each invariant's current text and status. This document does not copy it, so it cannot drift from it.

**The four governance files per repo.** Every repo maintains `CLAUDE.md`, `docs/OCR_VISION.md`, `README.md`, `SKILL.md`.

**Derived patterns Claude enforces:**

- **OSM + OA is one flywheel.** OSM = back (API, skills, CI). OA = front (fork, onboarding, environment). Together they spin up new entity instances that inherit all four invariants by construction.
- **OSE and OW are parallel platforms, not one merged service.** Same architecture, separate databases, opposite identity invariants (OSE anonymous-by-construction; OW named with voluntary attribution). "Converge under the OCR moniker" = shared architecture and brand, NOT merged data. Cross-platform features are per-record decisions.
- **OA serves at every scale.** Corridor, partner, venue, AND individual creator (every DJ profile is a single-person OA deployment).
- **OER is the BigQuery RAG.** All qualifying product DBs (OSE, OW, OA, OSM) feed it. Products do not query each other's DBs directly — they emit, OER ingests, OER answers.
- **OSP has no anonymous ID dependency.** Human-delivered. Tech-optional entry point.
- **File and folder naming is architectural.** `OCR_<TYPE>_<subject>.md` camelCase. Canonical `docs/` subfolders: decisions, standards, corridors, releases, prompts, ccr-gates.
- **Simplicity over completeness.** Code is the source of truth. When code and docs disagree, code wins.

---

## CCR protocol

All production-grade decisions across the OCR product line are governed by **CCR — Critical, Conservative, Recursive**.

- 3 layers: Critical, Conservative, Recursive
- 3 loops minimum per review
- **95% confidence gate** — below that, human gate activates
- Artifacts are earned, not generated
- Prompts are data — the input is part of the artifact chain

Full spec: `skills/ccr-protocol.knowledge.md`.

---

## Human review gate for governance artifacts

ADRs (`docs/adr/`), `docs/OCR_VISION.md`, standards (`docs/standards/`), the brain (`ocr-docs-brain/`), skills, and every repo's `CLAUDE.md` are governance artifacts. A change to any of them needs a human's review before it merges. Green CI is not enough.

- **Flag it.** Any PR that touches a governance artifact says so at the top of its description: "Needs human review: edits <file>". It lists the exact claims it adds or changes, so the reviewer can check each one against the evidence.
- **Never propose a bypass.** Claude never recommends "bypass rules and merge", admin override, or making a required check or review pass automatically on a governance PR. If a required check cannot report, fix the check so it still waits on a person; do not remove the gate.
- **Numbers are claims.** Any count or measurement written into a governance artifact carries its method (the command, or the file and line), so the reviewer can re-derive it.
- **Enforcement.** `.github/CODEOWNERS` routes these paths to the human reviewer account. It binds once branch protection has "Require review from Code Owners" turned on, which is an owner setting.

## Knowledge homes & reconciliation

Every truth has one home; reconciliation keeps the homes agreeing and promotes shared truths into the brain so every spoke inherits them.

- **Product repo** = its own current state + deep detail (code wins over docs).
- **Linear** = the historical record (ticket state, PRs, dated logs).
- **OCR-docs brain** = shared cross-spoke understanding (invariants, standards, VISION) → propagates to spokes.
- **Session / agent memory** = a thin, live pointer cache — never a system of record.

Reconciliation = drive **code ↔ brain ↔ docs ↔ Linear ↔ deployed** to zero inconsistencies: verify first, file a story per inconsistency (never duplicate — fold into the owner), fix drift at its home, and **promote any shared truth into this brain** — the third leg, because a spoke-local fix re-enters as drift through the other spokes.

Full standard: `docs/standards/OCR_STANDARD_knowledgeHomes.md`. Transport mechanism: `OCR_STANDARD_orgBrainSync.md`.

---

## Pointers (not copies)

To avoid drift, Claude should not duplicate these from VISION.md here:

- **The Triangle and the invariants (source of truth)** → `ocr-docs-brain/architectural-invariants.yaml` (the list), `ourSharedEvents/tests/e2e/0-architecture/` (executable specs) and `docs/OCR_VISION.md` (Architecture section, prose mirror)
- **Four governance files per repo** → `docs/OCR_VISION.md` (Architecture section, governance-files subsection)
- **OSM + OA flywheel** → `docs/OCR_VISION.md` (Architecture section)
- **OSE / OW platform symmetry** → `docs/OCR_VISION.md` (Architecture section)
- **Data flow / OER as BigQuery RAG** → `docs/OCR_VISION.md` (Architecture section)
- **Product registry** → `docs/OCR_VISION.md` (Product registry)
- **Founding corridors** → `docs/OCR_VISION.md` (Founding corridors)
- **Archive commitment** → `docs/OCR_VISION.md` (Archive commitment)
- **NCR methodology** → `docs/OCR_VISION.md` (NCR methodology) · full doctrine in `LOCKED_NCR_Methodology_v1.3`
- **Open decisions** → `docs/OCR_VISION.md` (Open decisions)

---

*Last updated: 2026-10-21 (v3: invariants list replaced by a pointer to the brain)*
*Owner: Matt*
*Status: edited 2026-10-21, awaiting human review.*
