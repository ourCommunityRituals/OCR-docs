# SKILL.md — OCR-docs

Skills for org-level coordination across the OCR product line.

---

## Skill: Vision Sync

### When to Use
User says: "sync vision", "update products", "derive from vision", "propagate"

### Steps
1. Read `docs/OCR_VISION.md` — the org-level source of truth
2. Identify which product repos need updates based on changes
3. For each affected repo, update its `docs/OCR_VISION.md` to reflect org-level changes
4. Ensure no product-level document contradicts org-level vision
5. Commit changes per repo with clear attribution to the org-level change

---

## Skill: Product Line Status

### When to Use
User says: "product status", "line status", "where are we", "product overview"

### Steps
1. Read `docs/OCR_VISION.md` for the product registry
2. For each product repo that exists locally, check:
   - Last commit date
   - Whether CLAUDE.md exists
   - Whether docs/OCR_VISION.md exists
   - Branch status
3. Report status table across the full product line

---

## Skill: Cross-Product Audit

### When to Use
User says: "cross product", "product line audit", "system level", "ocr audit"

### Steps
1. Read `docs/OCR_VISION.md` for architectural boundaries
2. Read `.claude/skills/ccr-protocol.knowledge.md` from OSE for CCR spec
3. Run CCR at System level across all product repos
4. Check for:
   - Contract consistency between products
   - Anonymized/identified boundary integrity
   - Documentation completeness per repo
   - DAC compliance (CLAUDE.md, VISION.md, README.md, SKILL.md present)
5. Report findings with CCR confidence score

---

## Skill: Corridor Check

### When to Use
User says: "corridor", "corridors", "activation status", "geography"

### Steps
1. Read `docs/OCR_VISION.md` — founding corridors section
2. Report current corridor status, activation dates, and roles
3. Flag any corridors approaching activation with incomplete product readiness

---

## Skill: DAC Compliance

### When to Use
User says: "dac check", "documentation check", "repo compliance"

### Steps
1. For each product repo in the OCR org:
   - Check for CLAUDE.md
   - Check for docs/OCR_VISION.md
   - Check for README.md
   - Check for SKILL.md
2. Report compliance matrix
3. Flag repos missing required documents

---

*Last updated: April 5 2026*
*Owner: Matt*
*Status: ACTIVE*
