# OCR_STATUS_project — OCR Org-Level Status

> Maintained by orc-doc-brain-floss. Updated each sync run.  
> Source of truth for issue baseline comparison across runs.

---

## Snapshot: 2026-04-09 (second run)

### Issue counts — all visible teams

| Team | Total | Backlog | Done | In Progress | Todo | Other |
|------|-------|---------|------|-------------|------|-------|
| OurSharedEvents (OSE) | 172 | ~125 | 32 | 2 | 6 | 7 |
| OurWKRP (OW) | 52 | 51 | 0 | 1 | 0 | 0 |
| OCR-doc | 20 | ~19 | 0 | 0 | 0 | 1 |
| OurSharedMagnets (OSM) | 2 | 2 | 0 | 0 | 0 | 0 |
| **Total** | **246** | **201** | **32** | **3** | **6** | **8** |

Teams NOT yet in Linear: OSG, OSR, OSP, OWL

---

### In Progress (as of this run)

| ID | Title | Team | Priority | Days Stalled |
|----|-------|------|----------|-------------|
| OSE-12 | P1-7: Secrets + first staging deploy | OSE | High | ~5 days — AC stale |
| OW-6 | WKRP-6: Mobile Auth — Deep Link + Universal Links | OW | **Urgent** | NEW |
| OSE-22 | Test Coverage Tracker: Legacy vs Worker | OSE | High | Archived Apr 6 — CLOSE |

---

### Critical blockers (org-wide)

| ID | Title | Team | Impact | Action |
|----|-------|------|--------|--------|
| OSE-168 | isPrimary schema bug | OSE | Blocks ALL EPIC-02 sponsor work | **Fix now. Highest priority code task.** |
| OSE-166 | CI license false positive (node-forge) | OSE | Blocks all CI merges | Clear false positive config |
| OSM-1 | WAF exemption — automated API consumers | OSM | Blocks entire franchise layer | Cloudflare WAF rule |
| OCR-18 | BIPA legal opinion (Tom) | OCR-doc | Blocks biometric scan data | Legal consultation — non-deferrable |

---

### Urgent open (not In Progress)

**OSE:** OSE-167 (TODAY — blackout), OSE-168 (isPrimary), OSE-166 (CI), OSE-163, OSE-164 (GAS ghost refs), OSE-158 (wrangler security), OSE-145 (dev env), OSE-146/147/148 (MOCK-1), OSE-152 (BRIEF-1), OSE-24 (prod readiness), OSE-59 (D1 provision), OSE-33 (SR-12 flag gating)

**OW:** OW-6 (In Progress)

**OCR-doc:** OCR-18 (BIPA), OCR-6 (mock data provider)

**OSM:** OSM-1 (WAF exemption)

---

### Cross-product action items

| Priority | Action | Owner hint | Status |
|----------|--------|------------|--------|
| 1 | Fix OSE-168 (isPrimary bug) | BE / OSE | **DONE** — migration `0018_fix_sponsor_tier_default.sql` in OSE |
| 2 | Audit OSE-12 AC, update or close | PO / OSE | **DONE** — `docs/ccr-gates/OSE_GATE_OSE12_acAudit.md` |
| 3 | Resolve OSM-1 WAF exemption | SRE / OSM | OPEN |
| 4 | Schedule OCR-18 BIPA legal consult | Matt | OPEN |
| 5 | Document D1 migration standard in OCR-docs before OW-31 | OSE → OCR-docs | **DONE** — `docs/standards/OCR_STANDARD_d1Migration.md` |
| 6 | Decide: OCR-6 org mock vs OSE MOCK-1 first | PO / OCR + OSE | **DONE** — `docs/decisions/OCR_DECISION_mockDataProvider.md` |
| 7 | Close OSE-22 (archived, still In Progress) | OSE | OPEN |
| 8 | CCR gate OW-30 before it enters sprint | PO / OW | **DONE** — `docs/ccr-gates/OW_GATE_OW30_boundaryReview.md` |
| 9 | Confirm Beverly archive activation started today | Matt / OSR | **DONE** — `docs/corridors/OCR_CHECKLIST_beverlyActivation.md` |
| 10 | Fix VISION.md typos (agaisnt, permenating, econony) | Matt | **DONE** — fixed in `docs/OCR_VISION.md` |

---

### Due soon

| ID | Title | Due | Team |
|----|-------|-----|------|
| OSE-172 | Harbor Country campaign operator named before May 1 | 2026-05-01 | OSE |
| OSE-169 | Define warm OSE brand for SharedReport and forms | 2026-05-01 | OSE |
| — | June 1 founding corridor activation | 2026-06-01 | ALL |

---

### June 1 critical path (53 days)

```
OSE-168 (isPrimary fix)
  → EPIC-02 sponsor work unlocked
  → Sponsor pipeline ready for June 1

OSE-12 (staging deploy, AC audit)
  → Staging baseline established
  → Integration testing possible

OSM-1 (WAF exemption)
  → Franchise layer operational
  → Corridor operators can access API

OW-6 (Mobile Auth)
  → OW contributor onboarding possible
  → OW-31 (DJ Profile schema) can start
```

---

*Last updated: 2026-04-09 (second run)*  
*Updated by: Bloodraven (orc-doc-brain-floss)*
