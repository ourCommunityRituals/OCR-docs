# Release Triage — June 1 2026 (Founding Corridor Activation)

> **Target:** June 1 2026 (53 days from triage date)
> **Scope:** All stories on the critical path to founding corridor activation
> **Model:** Per `OCR_STANDARD_agentOperatingModel.md` — agents work until green, then maintenance

---

## Triage legend

| Field | Values |
|---|---|
| **Class** | `AW` = agent-workable, `AA` = agent-assistable, `HO` = human-only |
| **Role** | Per scrum team roles in agent operating model |
| **Status** | Current state as of triage |

---

## Critical blockers

| ID | Title | Team | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|---|
| OSE-168 | isPrimary schema bug | OSE | BE | AW | migration + test | none — CI validates | **DONE** |
| OSE-166 | CI license false positive (node-forge) | OSE | SRE | AW | eslint/CI config fix | none — CI validates | TODO |
| OSM-1 | WAF exemption — automated API consumers | OSM | SRE | HO | agent documents rule needed | SRE configures Cloudflare dashboard | TODO |
| OCR-18 | BIPA legal opinion (Tom) | OCR | LEGAL | HO | agent flags urgency, creates checklist | full — legal consultation | TODO |

---

## OSE — In Progress / Urgent

| ID | Title | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|
| OSE-12 | P1-7: Secrets + first staging deploy | SRE + PO | AA | agent drafted updated AC | PO signs off AC, SRE verifies secrets | **AC DONE** — needs PO sign-off then close |
| OSE-22 | Test Coverage Tracker: Legacy vs Worker | PO | AA | agent updated tests per tracker | PO closes in Linear | **WORK DONE** — needs Linear close |
| OSE-167 | April 9 Eagles Hall technology blackout | OPS | HO | none | full — physical event | DONE (date passed) |
| OSE-163 | GAS ghost refs — googleAppScript/Apps Script API | BE | AW | grep + remove dead refs | none — CI validates | TODO |
| OSE-164 | GAS ghost refs — GAS/NUSDK acronym pattern | BE | AW | grep + remove dead refs | none — CI validates | TODO |
| OSE-158 | Security: upgrade wrangler to 4.59.1+ | SRE | AW | package.json version bump + CI | none — CI validates | TODO |
| OSE-145 | OPS-1: Verify dev environment config | SRE | AW | validate wrangler.toml, env vars, local dev | none — agent verifies | TODO |
| OSE-146 | MOCK-1: Configurable demo environment | BE | AW | D1 seed + demo endpoint + tier logic | none — CI validates | TODO |
| OSE-147 | MOCK-1: Demo data seeding | BE | AW | migration seed files | none — CI validates | TODO |
| OSE-148 | MOCK-1: Demo environment testing | QA | AW | Newman collections + tier validation | none — CI validates | TODO |
| OSE-152 | BRIEF-1: CEO briefing app — deploy to staging | FE + SRE | AA | agent builds static asset | PO reviews content | TODO |
| OSE-24 | MVP Production Readiness Review | TL + PO | AA | agent audits all systems, drafts report | TL + PO sign off | TODO |
| OSE-59 | INFRA-1: Provision D1 databases (main + forms, staging + prod) | SRE | AA | agent generates wrangler config | SRE creates DBs in Cloudflare dashboard | TODO |
| OSE-33 | SR-12: Runtime flag gating on sharedReport endpoint | BE | AW | feature flag check in handler | none — CI validates | TODO |

---

## OW — In Progress / Urgent

| ID | Title | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|
| OW-6 | Mobile Auth — Deep Link + Universal Links | BE + FE | AA | agent scaffolds auth flow, deep link config | human tests on physical devices | IN PROGRESS |
| OW-30 | Event Playlist Linking | TL + BE | AA | agent researched boundary, drafted gate | TL approves design before code | **BLOCKED** — gate at `OW_GATE_OW30_boundaryReview.md` |
| OW-31 | DJ Profile schema (D1 migration) | BE | AW | migration per `OCR_STANDARD_d1Migration` | none — CI validates | TODO (blocked by OW-6) |

---

## OCR-doc — Urgent

| ID | Title | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|
| OCR-18 | BIPA legal opinion (Tom) | LEGAL | HO | agent flags, creates checklist | full — legal | TODO |
| OCR-6 | Org mock data provider | TL | AA | decision made — OSE builds first | none — decided | **DONE** — `OCR_DECISION_mockDataProvider.md` |

---

## OSM

| ID | Title | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|
| OSM-1 | WAF exemption — automated API consumers | SRE | HO | agent documents rule | SRE configures Cloudflare | TODO |

---

## Due soon (May 1)

| ID | Title | Role | Class | Agent capability | Human gate | Status |
|---|---|---|---|---|---|---|
| OSE-172 | Harbor Country campaign operator named | PO + OPS | HO | none — human networking | full | TODO |
| OSE-169 | Define warm OSE brand for SharedReport/forms | PO + FE | AA | agent researches brand patterns, drafts options | PO selects direction | TODO |

---

## Summary by classification

| Classification | Count | Stories |
|---|---|---|
| **Agent-workable** | 11 | OSE-168 (DONE), OSE-166, OSE-163, OSE-164, OSE-158, OSE-145, OSE-146, OSE-147, OSE-148, OSE-33, OW-31 |
| **Agent-assistable** | 8 | OSE-12, OSE-22, OSE-152, OSE-24, OSE-59, OW-6, OW-30, OSE-169 |
| **Human-only** | 5 | OSM-1, OCR-18, OSE-167 (done), OSE-172, OCR-6 (DONE) |

### Agent-workable priority queue (sorted by leverage)

```
1. OSE-166  CI license false positive     — unblocks ALL CI merges
2. OSE-163  GAS ghost refs (AppScript)    — cleanup, quick win
3. OSE-164  GAS ghost refs (GAS/NUSDK)    — cleanup, quick win
4. OSE-158  wrangler security upgrade     — security, quick win
5. OSE-33   SR-12 flag gating             — unblocks sharedReport
6. OSE-145  dev environment config        — unblocks local dev
7. OSE-146  MOCK-1 demo environment       — unblocks sponsor demos
8. OSE-147  MOCK-1 demo seeding           — depends on OSE-146
9. OSE-148  MOCK-1 demo testing           — depends on OSE-147
10. OW-31   DJ Profile schema             — blocked by OW-6
```

**OSE-168 already DONE.** The next highest-leverage agent-workable story is **OSE-166** — it unblocks all CI merges, which means every other agent-workable story after it can actually ship.

---

*Triaged: April 9 2026*
*Release: June 1 2026*
*Status: ACTIVE*
