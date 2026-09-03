# Fleet Discovery Hub

This directory is the **fleet-wide** discovery surface for the OCR product line. It holds primary research, sales playbooks, and case-study material that spans more than one product. Per-product discovery work lives in that product's repo at `<repo>/docs/discovery/`.

The routing rule is encoded in [`OPERATING_SYSTEM.md §3`](../../OPERATING_SYSTEM.md) at the OCR-docs root:

| Scope | Lives at |
|-------|----------|
| Repo-specific discovery (one product's ICP, one venue type, one persona) | `<repo>/docs/discovery/` |
| **Fleet-wide discovery (cross-product themes, cross-ICP findings, fleet sales playbook)** | **`OCR-docs/docs/discovery/` (this directory)** |

## Why split fleet vs per-repo?

OSE is interviewing bar owners. WKRP will interview DJs and curators. OSM may interview agency procurement teams. OurAirwaves will interview venue programmers. **The ICP per product is different**, and the interview guide, target list, and anonymization rules are product-specific.

But there are **cross-product patterns** that emerge only when you read interview findings from multiple products in one place:

- A DJ who plays at a bar that uses OSE — the two products serve the same physical venue from different angles.
- A sponsor that buys impressions on both OSE and OurAirwaves — the sales motion is one conversation, not two.
- A bar-owner objection ("I don't want third-party tech in my space") that becomes a fleet-wide pricing/positioning concern.

Those patterns belong here, in the fleet hub, so the founder isn't reading seven separate `docs/discovery/` directories to find them.

## What lives here

### Now (2026-09-03)

| File | What it is |
|------|-----------|
| [`OCR_REFERENCE_contentMarketFitResearch.md`](OCR_REFERENCE_contentMarketFitResearch.md) | Sept 2025 – Sept 2026 sentiment study of the three pain points (surveillance / false consent, third places, small business priced out). Source input. |
| [`OCR_REFERENCE_contentMarketFitAssessment.md`](OCR_REFERENCE_contentMarketFitAssessment.md) | Fit of OCR hub, OSE foundation, and OW spoke against that research, drift found, and the ordered path to the Front Door site design (Linear OCR-115 / OCR-116). |

Per-product discovery work still lives in `ourSharedEvents/docs/discovery/` — see [§ Pointers](#pointers) below.

### Planned (as fleet-wide discovery accumulates)

| File pattern | Purpose |
|--------------|---------|
| `CROSS-PRODUCT-FINDINGS-YYYY-MM-DD.md` | Synthesis when interview batches across ≥2 products reveal a shared pattern |
| `OCR_PLAYBOOK_sales_*.md` | Sales motion patterns that apply across the fleet (objection handling, pricing conversations, intro emails) |
| `OCR_CASE-STUDY_<anonymized>_<theme>.md` | Anonymized case studies that demonstrate the platform's claim across multiple products |
| `OCR_METHODOLOGY_<topic>.md` | Cross-cutting discovery methodology (e.g., universal anonymization rules, conversation-recording etiquette, interview-cadence guidelines) |

These are seeded on demand — do not create empty placeholder files. The first fleet-wide discovery artifact written is the trigger to formalize the pattern.

## Anonymization discipline (fleet rule)

Per `ourSharedEvents/docs/discovery/README.md`, the anonymization rule is fleet-wide doctrine:

- **Never** record venue names, owner names, performer names, or specific addresses in any committed artifact.
- Acceptable identifiers: venue type, neighborhood-level location, role, conversation date.
- Acceptable quotes: paraphrased to remove identifying detail.
- Personal notes with identities can live in a private notebook; the committed artifact must be anonymized at write time.

This rule applies to **every** discovery artifact in the fleet — per-repo and fleet-level alike. It is foundational to the platform's anonymity ethos.

## Process for adding a fleet discovery artifact

1. Confirm the artifact spans ≥ 2 products or is genuinely fleet-cutting. If it belongs to one product, write it in that product's `docs/discovery/`.
2. Pick the right file pattern from the table above. If none fits, propose a new one in a PR that edits this README.
3. Write the artifact. Anonymize aggressively per the rule above.
4. Cross-link from the relevant product's `docs/discovery/README.md` so the fleet artifact is discoverable from the product side too.
5. Land in a focused docs PR.

## Pointers

### OSE — bar owner discovery (OSE-271)

- [`ourSharedEvents/docs/discovery/README.md`](../../../ourSharedEvents/docs/discovery/README.md) — overall process + anonymization rules
- [`ourSharedEvents/docs/discovery/INTERVIEW-GUIDE-BAR-OWNERS-2026-05-14.md`](../../../ourSharedEvents/docs/discovery/INTERVIEW-GUIDE-BAR-OWNERS-2026-05-14.md) — 14 ICP-validating questions
- [`ourSharedEvents/docs/discovery/INTERVIEW-TEMPLATE-2026-05-14.md`](../../../ourSharedEvents/docs/discovery/INTERVIEW-TEMPLATE-2026-05-14.md) — note-taking template
- [`ourSharedEvents/docs/discovery/TARGET-LIST-FRAMEWORK-2026-05-14.md`](../../../ourSharedEvents/docs/discovery/TARGET-LIST-FRAMEWORK-2026-05-14.md) — bar selection logic

### Other products

- **OW (ourWKRP)** — no discovery directory yet. When WKRP starts interviewing DJs/curators/chefs, create `ourWKRP/docs/discovery/` and link here.
- **OSM, OSP, OSR, OSG, OA** — no discovery directory yet. Create per-repo when the product starts engaging ICPs.

### Methodology references (fleet doctrine that governs discovery work)

- `~/.claude/projects/.../memory/feedback_*.md` — doctrine memory files that constrain discovery work (anonymization, no-OneDrive paths, private-until-launch).
- [`OPERATING_SYSTEM.md §4`](../../OPERATING_SYSTEM.md) (OCR-docs root) — the sales→eng→sales loop that discovery work feeds.

## Closing the loop

Discovery is the `①→②` arrow in `OPERATING_SYSTEM.md §4` (the sales → engineering → sales loop). Its job is to convert sales-side conversations into structured input that triages into Linear epics, ADRs, or Brain contracts. The closing test for any discovery batch: **each insight has a clear destination link in the loop**.

If a discovery finding can't be triaged into the loop, it either belongs in a personal notebook (not committed) or it surfaces a gap in the routing matrix itself (PR `OPERATING_SYSTEM.md`).
