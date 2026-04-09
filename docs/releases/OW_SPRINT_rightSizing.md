# OW Sprint Right-Sizing — April 9 2026

> **Trigger:** Bloodraven third run detected 24+ OW stories simultaneously In Progress with 0 Done, dependency chain violations, and OW-30 in sprint despite CCR gate BLOCKED status.
> **Action:** Right-size sprint to match actual work state and dependency order.

---

## Problem

Linear shows 24+ OW stories In Progress. The codebase (STORIES.md) shows 18 Done, 1 In Progress, 10 Backlog. A bulk Linear state change moved stories to In Progress without regard for dependency order, capacity, or CCR gates.

---

## Actual state (from STORIES.md + codebase)

### Done (18 stories) — move to Done in Linear

| Linear ID | STORIES.md ID | Title | Sprint |
|---|---|---|---|
| OW-1 | WKRP-1 | Project Scaffold + Worker Entry | 1 |
| OW-2 | WKRP-2 | Spotify OAuth + PKCE Auth Flow | 1 |
| OW-3 | WKRP-3 | Spotify Sync Engine | 1 |
| OW-4 | WKRP-4 | Mobile-First Frontend | 1 |
| OW-5 | WKRP-5 | Testing Pyramid | 1 |
| OW-7 | WKRP-6 | Catalog API Endpoints | 2 |
| OW-8 | WKRP-7 | Playlist Builder (D1 MVP + Apple Music Push) | 2 |
| OW-9 | WKRP-8 | Multi-Tenant Brand Support | 2 |
| OW-11 | WKRP-10 | Genre Discovery Links | 2 |
| OW-13 | WKRP-12 | Last.fm Scrobble Sync + Genre Enrichment | 3 |
| OW-15 | WKRP-14 | CSV Bulk Import UI | 3 |
| OW-16 | WKRP-15 | Contributor Profiles | 3 |
| OW-18 | WKRP-17 | Wire Catalog UI to Track API | 3 |
| OW-19 | WKRP-18 | Wire Playlist Builder UI | 3 |
| OW-20 | WKRP-19 | Connect Flow — CSV-First Model | 3 |
| OW-21 | WKRP-20 | Frontend Identity Overhaul | 3 |
| OW-24 | WKRP-23 | DJ Dashboard | 4 (see flag below) |
| OW-25 | WKRP-24 | Catalog Stats Page | 4 |

**Action:** Move all 18 to Done in Linear. This establishes velocity and accurate board state.

### In Progress (1 story) — keep In Progress

| Linear ID | STORIES.md ID | Title | Notes |
|---|---|---|---|
| OW-6 | WKRP-9 | Infrastructure Deployment | Automation + playbook done. Manual steps remain: DNS config, staging deploy, smoke tests, Apple Developer enrollment (1-2 week external dep). |

### Backlog (10 stories) — move back to Backlog in Linear

| Linear ID | STORIES.md ID | Title | Blocked by | June 1 relevance |
|---|---|---|---|---|
| OW-17 | WKRP-16 | Apple Music as Contribution Source | OW-6 (Apple Developer enrollment) | Low — external dependency |
| OW-22 | WKRP-21 | OurRecordStories Integration | OW-16 (Done) | Medium — Beverly archive |
| OW-23 | WKRP-22 | DJ Attribution + QR Scan | OW-16 (Done) | High — enables DJ monetization |
| OW-26 | WKRP-25 | Sponsor Reporting API | OW-23 | Medium — needs attribution first |
| OW-27 | WKRP-26 | OurSharedEvents Integration | OW-23 | Medium — needs attribution first |
| OW-30 | — | Event Playlist Linking | **CCR GATE BLOCKED** | **BLOCKED — see below** |
| OW-31 | — | DJ Profile schema (D1 migration) | OW-6 | High — but needs OW-6 Done first |
| OW-28 | — | OpenAPI/Scalar docs | None | Low |
| OW-29 | WKRP-29 | Catalog Export | None | Low |
| OW-32 | WKRP-30 | Catalog Layers View | OW-18 (Done) | Low |

---

## OW-30: CCR gate violation

**OW-30 (Event Playlist Linking) entered In Progress despite the CCR gate document explicitly stating BLOCKED.**

Gate document: `docs/ccr-gates/OW_GATE_OW30_boundaryReview.md`

Unchecked requirements:
- [ ] `event_playlists` migration file written and reviewed against pass/fail criteria
- [ ] Design decision documented: is the table purely internal to OW?
- [ ] Privacy boundary reaffirmed in code comments on any new handler
- [ ] CCR gate review signed off by PO

**Action:** Move OW-30 back to Backlog immediately. No code should land for this story until the gate checklist is complete and signed off.

The architectural boundary (OW named identity / OSE anonymous ID never cross at app layer) is the core constraint of this platform. This is not a process concern — it's a data model integrity issue.

---

## Right-sized sprint (recommended)

After correction, OW should have at most 3-5 stories In Progress:

| Priority | Linear ID | Title | Role | Class | Why now |
|---|---|---|---|---|---|
| 1 | OW-6 | Infrastructure Deployment (manual steps) | SRE | AA | Unblocks OW-17 and OW-31. Apple Developer enrollment is time-gated. |
| 2 | OW-23 | DJ Attribution + QR Scan | BE | AW | Unblocks OW-26, OW-27. Core monetization feature. |
| 3 | OW-22 | OurRecordStories Integration | BE | AW | Beverly archive dependency. Links to OSR activation. |
| 4 | OW-31 | DJ Profile schema (D1 migration) | BE | AW | Per OCR D1 standard. Blocked until OW-6 Done. Move to Todo. |
| 5 | OW-29 | Catalog Export | BE | AW | Independent, no blockers. Can run in parallel. |

Everything else stays in Backlog until its dependencies are Done.

---

## Red flag: OW-24 (DJ Dashboard) marked Done but depends on OW-23

STORIES.md marks WKRP-23 (DJ Dashboard) as Done in Sprint 4. But it depends on WKRP-22 (DJ Attribution + QR Scan) which is in Backlog. The dashboard cannot be functional without the attribution system feeding it data.

**Options:**
1. OW-24 is scaffolded (UI shell done) but not functional — mark as Done with a note that it activates when OW-23 completes
2. OW-24 acceptance criteria are not fully met — move back to Todo

**Recommendation:** Option 1. The shell exists, the data integration is a separate story.

---

## Linear actions (human — 5 minutes)

1. Move 18 stories to **Done** (see Done table above)
2. Move OW-30 to **Backlog** (CCR gate BLOCKED)
3. Move remaining bulk-moved stories to **Backlog**
4. Keep OW-6 as **In Progress**
5. Move OW-23, OW-22 to **Todo** (ready to start, dependencies met)
6. Move OW-31 to **Todo** (ready when OW-6 completes)

This gives OW: 18 Done, 1 In Progress, 3 Todo, 7 Backlog. Clean board. Correct dependency order. Velocity visible.

---

*Created: April 9 2026*
*Trigger: Bloodraven third run*
*Status: PENDING — requires Linear board updates*
