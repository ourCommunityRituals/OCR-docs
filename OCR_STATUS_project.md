# OCR_STATUS_project — OCR Org-Level Status

> Maintained by orc-doc-brain-floss. Updated each sync run.  
> Source of truth for issue baseline comparison across runs.

---

## Snapshot: 2026-04-09 (third run — evening)

### Issue counts — all visible teams

| Team | Total | Backlog | Done | In Progress | Todo | Other |
|------|-------|---------|------|-------------|------|-------|
| OurSharedEvents (OSE) | 172 | ~101 | 33 | 2 | 6 | 7 |
| OurWKRP (OW) | 52 | ~27 | 0 (18 actual, not in Linear) | 24+ (bulk move — see right-sizing) | 0 | 0 |
| OCR-doc | 20 | ~19 | 0 | 0 | 0 | 1 |
| OurSharedMagnets (OSM) | 2 | 2 | 0 | 0 | 0 | 0 |
| OurSharedRecords (OSR) | 0 | 0 | 0 | 0 | 0 | 0 |
| OurSharedGames (OSG) | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | **~246** | **~149** | **33** | **26+** | **6** | **8** |

Teams NOT yet in Linear: OSP, OWL  
⚠️ OW In Progress count is anomalous — bulk sprint move. See log.

---

### In Progress (as of this run — right-sized)

| ID | Title | Team | Priority | Status |
|----|-------|------|----------|--------|
| OW-6 | WKRP-9: Infrastructure Deployment | OW | **High** | Automation done, manual steps remain (DNS, staging, Apple Developer) |
| OSE-12 | P1-7: Secrets + first staging deploy | OSE | High | AC audit done — needs PO sign-off then close |

### Right-sizing applied (OW sprint correction)

**18 OW stories moved to Done** — codebase confirms these are complete (Sprints 1-4). Linear was not reflecting actual state.

**OW-30 moved to Backlog** — CCR gate BLOCKED. See `docs/ccr-gates/OW_GATE_OW30_boundaryReview.md`. 4 unchecked requirements. No code until gate clears.

**Remaining OW backlog moved back to Backlog/Todo** — bulk In Progress was a state change error, not actual concurrent work. See `docs/releases/OW_SPRINT_rightSizing.md` for full breakdown.

**Recommended OW Todo (ready to start, dependencies met):**

| ID | Title | Role | Class | Unblocks |
|----|-------|------|-------|----------|
| OW-23 | DJ Attribution + QR Scan | BE | AW | OW-26, OW-27 (sponsor reporting, OSE integration) |
| OW-22 | OurRecordStories Integration | BE | AW | Beverly archive activation |
| OW-31 | DJ Profile schema (D1 migration) | BE | AW | DJ profiles — blocked until OW-6 Done |

---

### Critical blockers (org-wide)

| ID | Title | Team | Impact | Action |
|----|-------|------|--------|--------|
| ✅ ~~OSE-168~~ | ~~isPrimary schema bug~~ | ~~OSE~~ | ~~Blocks ALL EPIC-02 sponsor work~~ | **DONE 2026-04-09** |
| **OW-30** | Event Playlist Linking in sprint — CCR gate BLOCKED | OW | Architectural boundary integrity | 🔴 Stop. Review gate. Move back to Backlog or sign off gate. |
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

### June 1 critical path (53 days remaining)

```
✅ OSE-168 (isPrimary fix) — DONE 2026-04-09
  → EPIC-02 sponsor work unlocked ✅

OSE-12 (staging deploy, AC audit)
  → AC update needed → close in Linear
  → Staging baseline → integration testing

OSM-1 (WAF exemption)
  → Franchise layer operational
  → Corridor operators can access API

OW sprint right-sizing
  → Reduce In Progress to ≤5 stories
  → Close OW-4/OW-5 (description says Done)
  → Gate OW-30 back to Backlog pending CCR sign-off
  → OW-6/OW-7 → OW-8 → OW-10 → OW-15 ordered sequence

OW-31 (DJ Profile schema)
  → Must reference OCR D1 migration standard before writing
```

### New action items (this run)

| Priority | Action | Owner | Status |
|----------|--------|-------|--------|
| 🔴 1 | OW-30 CCR gate — move back to Backlog OR formally sign off gate | Matt | OPEN |
| 🔴 2 | OW sprint review — right-size to ≤5 In Progress | Matt | OPEN |
| 🟠 3 | Close OW-4 and OW-5 in Linear (description says Done) | Matt | OPEN |
| 🟠 4 | OSE-12 — update AC, close story | Matt / OSE | OPEN |
| 🟠 5 | OSE-22 — close in Linear (archived Apr 6) | Matt | OPEN |
| 🟡 6 | OSR Beverly — create Linear issues for Phase 1 activation | Matt | OPEN |
| (carry) | OSM-1 WAF exemption | SRE | OPEN |
| (carry) | OCR-18 BIPA legal call with Tom | Matt | OPEN |

---

*Last updated: 2026-04-09 (third run — evening)*  
*Updated by: Bloodraven (orc-doc-brain-floss)*
