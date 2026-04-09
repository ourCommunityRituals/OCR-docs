# Beverly Corridor — Archive Activation Checklist

> **Formal launch date:** April 9, 2026 (archive collection start)
> **Platform launch:** September 2026
> **Anchor:** Open OutCry — Tuesday trivia target
> **Role:** Archive anchor
> **Owner:** Matt / OSR

---

## Status: April 9 2026

The formal archive collection start date has arrived. The OSR repo exists with documentation scaffolding (CLAUDE.md, README.md, SKILL.md) but no operational activation is in motion. OSR is not yet tracked in Linear.

---

## What exists

- OSR repository established with DAC scaffold
- OurRecordSides format documented: one person, five minutes, one story
- SKILL.md includes Beverly Archive Launch skill
- VISION.md defines Beverly as archive anchor
- Architectural boundaries documented (OSR owns archive, OSE owns platform)

## What's missing

- No `docs/` directory in OSR
- No activation plan for Beverly corridor
- No OurRecordSides format specification
- No capture workflow documentation
- No OSR issues in Linear
- No storage provisioning plan
- No volunteer role definitions

---

## Phase 1: Definition and planning (target: before May 1)

- [ ] Create OSR Linear team and initial issues
- [ ] Create `docs/corridors/beverly-activation-plan.md` in OSR
- [ ] Define OurRecordSides format formally — `docs/formats/record-sides-spec.md`
  - Recording format (audio? video? both?)
  - Duration constraint (5 minutes)
  - Metadata captured (participant name, date, location, prompt/topic)
  - Consent model (aligned with archive commitment — community owns the data)
- [ ] Document capture workflow — `docs/workflows/story-capture.md`
  - Equipment list and procurement
  - Recording environment requirements (Open OutCry venue specifics)
  - Post-capture processing (transcription, indexing, storage)
- [ ] Define volunteer roles
  - Story scout (identifies participants)
  - Audio/video operator
  - Transcriber
  - Indexer/archivist
- [ ] Coordinate with OSG — confirm Beverly game format and cadence (Tuesday trivia at Open OutCry)

## Phase 2: Infrastructure (target: before June 1)

- [ ] Provision archive storage (D1 per org standard — see `docs/standards/OCR_STANDARD_d1Migration.md`)
- [ ] Define archive schema: record metadata, media storage references, transcripts
- [ ] Configure data ownership transfer template (per founding commitment)
- [ ] Set up OSE event integration (corridor event creation triggers OSR archive plan per OCR_DEPENDENCY_crossRepo.md)

## Phase 3: Operations (target: before September 1)

- [ ] Train volunteer team at Open OutCry venue
- [ ] Test capture workflow with first Tuesday trivia session
- [ ] Establish indexing cadence
- [ ] Collect initial archive entries (April–August buffer)

## Phase 4: Platform integration (target: September 2026)

- [ ] Integrate OSR archive into OSE platform display
- [ ] Launch SharedReport surface for archive contributions
- [ ] Activate OER analytics on archive depth (when threshold met)

---

## Dependencies

Per `docs/OCR_DEPENDENCY_crossRepo.md`:

```
OSE (new corridor event created)
  → OSG (corridor activation plan: game format, cadence, venue)
  → OSR (archive plan: capture workflow, storage, volunteer roles)
```

Beverly activation depends on OSE corridor being created on the platform. OSG defines the game night format. OSR defines the archive capture.

---

*Created: April 9 2026*
*Owner: Matt*
*Status: PHASE 1 — planning*
