# CLAUDE.md — OCR-docs

> **Session protocol**: Read this file → Read `docs/OCR_VISION.md` → Understand the full product line → Execute the task at org level.

---

## What this repo is

OCR-docs is the org-level brain for OurCommunityRituals LLC. It holds the source-of-truth documentation that all product repos derive from. There is no application code here. Only governance, vision, architecture, and coordination.

If it is not written in `docs/OCR_VISION.md` it does not exist at the org level.

---

## Product line — quick reference

| Code | Product | Repo | Data model |
|------|---------|------|------------|
| OCR | OurCommunityRituals LLC | this repo | Governance |
| OSE | OurSharedEvents | ourSharedEvents | Anonymous ID |
| OW | OurWKRP | ourWKRP | Named identity |
| OSG | OurSharedGames | ourSharedGames | Inherits from OSE |
| OSR | OurSharedRecords | ourSharedRecords | Archive / oral history |
| OSP | OurSharedPulse | ourSharedPulse | Human-delivered, tech-optional |
| OSM | OurSharedMagnets | ourSharedMagnets | Developer / franchise |
| OER | OurEventRings | — | Intelligence / analytics |
| OWL | OurWhiteList | ourWhiteList | Deployment / white label |

### Key architectural boundaries

- **OSE is anonymized.** Anonymous ID architecture. No PII in its database.
- **OW (OurWKRP) is not anonymized.** Named identity. Attribution. DJ/artist verification.
- **OSE + OW converge** into one service under the OCR moniker. The anonymized/identified boundary is architectural and permanent.
- **All product data flows to BigQuery.** OurEventRings (OER) accesses via RAG for cross-product intelligence.
- **OSP has no anonymous ID dependency.** Human-delivered. Tech-optional entry point.

---

## Documentation as code (DAC)

Every product repo — whether it has application code or not — maintains:

- `CLAUDE.md` — session protocol and project brain
- `docs/OCR_VISION.md` — product-specific vision derived from org-level source of truth
- `README.md` — public-facing description
- `SKILL.md` — reusable skills for AI-assisted work

Documents are living. They are version-controlled, reviewed via PR, and treated with the same rigor as code. DAC keeps all applications aware of cross-product efficiencies and ensures customer value does not falter.

---

## NCR Methodology

Node Corridor Ring. The published academic methodology underlying the platform.

- **Node**: The specific activation point
- **Corridor**: The organic geographic thread connecting nodes
- **Ring**: The self-sustaining local economic loop

Six-layer geographic hierarchy from hyperlocal to macro region. Ring closes when the corridor economy no longer depends on outside investment.

See `LOCKED_NCR_Methodology_v1.3` for full doctrine.

---

## CCR Protocol

All production-grade decisions across the OCR product line are governed by the CCR (Critical, Conservative, Recursive) protocol.

- 3 layers: Critical, Conservative, Recursive
- 3 loops minimum per review
- 95% confidence gate — below that, human gate activates
- Artifacts are earned, not generated
- Prompts are data — the input is part of the artifact chain

See `skills/ccr-protocol.knowledge.md` in this repo for full spec.

---

## Founding corridors — June 1 2026

| Corridor | Anchor | Role |
|----------|--------|------|
| Blue Island | RIPH, Eagles Hall | AJ anchor. Municipal proof point. Primary activation. |
| Beverly | Open OutCry | Archive anchor. September 2026 platform launch. |
| Brainerd | — | Research comparator node |
| Evergreen Park | — | Cross-demographic corridor |
| Oak Lawn | — | SW cross-demographic corridor |
| Mt Greenwood | — | Adjacent ring. Beverly flywheel and contrast. |

---

## The archive commitment

OurCommunityRituals LLC owns the platform and the infrastructure. The data your community generates while using our platform is yours. We give it to you by choice. Not because we have to. Because we choose to. That is our founding commitment.

---

## Open decisions

- OWL repo structure and client fork workflow
- OER activation timing and data threshold
- OSP consulting engagement model formalized
- Dr. Obia conversation — NCR methodology sanity check — pending outreach

---

*Last updated: April 5 2026*
*Owner: Matt*
*Status: ACTIVE*
