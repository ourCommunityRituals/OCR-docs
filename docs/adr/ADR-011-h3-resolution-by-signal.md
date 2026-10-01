# ADR-011: H3 resolution by signal — res9 for physical places, res7 is the corridor

**Status:** Accepted — implementation in flight (accepted 2026-10-01, PO). Done in ourSharedEvents #720 and #726: the res7 corridor id, the export row guard and the scan → export trace. Still open: poster-cell scan aggregation (OSE-1459) and the Brain evidence updates listed under Implementation.
**Date:** 2026-10-01
**Deciders:** Matt (founder / PO)
**Scope:** Fleet-wide (geography model for every product that tags, stores or exports place)
**Supersedes:** None. Records as doctrine what was until now a migration comment (ourSharedEvents `migrations/0046_density_tables_drop_corridor_fk.sql`: "the H3 res7 cell string IS the corridor identifier") and closes two open decisions in ourSharedEvents `docs/features/QR-AND-SHORTLINKS.md` (#1 "surface determines resolution", #3 "where a digital click's res7 comes from").
**Cross-refs:** ADR-010 (the hyperlocal map — corridor → venue → event_type → event as the shared key; this ADR fixes the grain of the corridor and venue levels); ADR-002 (identity-profile-keyed invariants — the anonymous boundary this protects); ourSharedEvents ADR-009 (`docs/adr/ADR-009-ncr-v2-geographic-hierarchy.md`, NCR v2 — a "corridor" there is a connection between nodes, a different concept, see Consequences; not the fleet ADR-009, which is the composition plane and has no corridor concept); `OCR_VISION.md` NCR section (Node = res9, Corridor = res7); `ocr-docs-brain/corridor-definitions.yaml` (named corridors anchored on a res7 cell); `docs/architecture/OCR_ARCHITECTURE_oerAggregationBoundary.md` (export: corridor-level only)

---

## Context

The H3 layer is how the platform knows *where* without knowing *who*. The vision
already names the two levels (`OCR_VISION.md`: a Node is a res9 cell, a Corridor
is a res7 cell, "a corridor (res7) contains many nodes (res9)"), and the code
uses them: posters and venues are tagged with both cells, sponsor impressions are
stamped at res7, and the corridor density baseline is keyed by the res7 cell.

But the rules about **which signal gets which resolution** were never written as
a decision. They lived in a migration comment, a founder note
(`OSE_REFERENCE_posterPrimitiveReconciliation_2026-09-04.md`) and a feature doc
whose key items were still marked "proposed" or "open". The documents also
disagreed about what a corridor is. One says it is a single res7 cell (vision,
migration 0046). One says it is a named area such as `blue_island`, anchored on a
res7 cell with a bounding box (brain `corridor-definitions.yaml`). One says it is
a connection between nodes (ourSharedEvents ADR-009, NCR v2). A shortlink click had no written location
source at all.

QR Path to Done rung 5 (OSE-616: trace one scan from the poster to the BigQuery
export, with the geography asserted at every hop) cannot be verified against
doctrine that does not exist. The PO ruled on each point on 2026-10-01; this ADR
records those rulings.

## Decision

**Resolution is a property of the signal's physical anchor, never of the person.**

| Signal | Finest resolution | Where the place comes from |
| --- | --- | --- |
| Poster placement (physical QR) | **res9** (and its res7) | The address the organiser entered, geocoded once at creation |
| Live QR scan during the event | **res9** (and its res7) | The event venue (the scan happens there) |
| QR scan at a poster | res9 via the poster | The poster placement it references; the scan row stores no place of its own |
| Shortlink (`/s/`) click | **res7** | The event it belongs to: the event venue's res7. The click record stores no place of its own |
| Sponsor impression | res7 | Stamped at write time (unchanged, OSE-635) |
| Anything else, and every export | res7 or coarser | — |

1. **res9 is for physical places only**: a poster's placement and live QR scans
   at the venue during the event. Nothing else is ever tagged finer than res7.
2. **The corridor is the res7 cell.** The corridor id that crosses to BigQuery /
   OER is the res7 cell string. Named corridors (`blue_island`, the OSE-613
   registry) are labels over sets of res7 cells. They are added beside the
   res7 id when the registry exists. They do not replace it.
3. **Shortlink clicks resolve to their event, at the event venue's res7.** This
   keeps clicks private (no click is ever placed finer than a corridor) while
   still counting toward the event. No geography is stored on the click itself.
4. **Exports carry res7 or coarser.** A row that would carry a res9 cell, a
   coordinate, an address or a placement reference is **rejected** at the
   boundary, and its phase fails closed. It is never trimmed and shipped.

Device location (browser geolocation, IP-derived city/region) is never an input
to any of the above. This was already enforced, and it is restated here as part
of the same rule.

## Consequences

### Positive

- One written rule for every signal. Code, tests and the brain can be checked
  against it, and the OSE-616 trace asserts it hop by hop.
- The corridor id is stable and computable from a coordinate with no lookup.
  Every product can stamp it at write time (ADR-010's shared key).
- Clicks become countable per corridor without ever being placeable at a node.

### Negative / trade-offs

- A click is placed in the **event's** corridor, not where the link was shared.
  Reach into other corridors is invisible to click data. The earlier
  "published-into area" idea (QR-AND-SHORTLINKS.md) is not adopted.
- A res7 cell is a fixed hexagon. It is not a community boundary. Communities
  that straddle cells need the registry (OSE-613) to be reported as one place.
- Scan aggregates today take the venue's cells for every scan. A pre-event scan
  at a poster elsewhere is aggregated at the venue node, not the poster's. That
  conflicts with rule 1's intent and is tracked in OSE-1459.

### Neutral / explicit

- ourSharedEvents ADR-009's "corridor" (a connection between nodes in the
  NCR v2 hierarchy, e.g. Chicago→Detroit via I-94) is a different concept with
  the same word. This ADR governs geographic
  corridor ids only.
- This ADR does not set export time grain or K-floors. The grain is hourly:
  the PO decided it on 2026-10-01 (OSE-1460), matching the code, and
  CHOICE-INVARIANTS A-8 and the IRB YAML now say so.
- It does not decide whether `anon_id_hash` and `venue_id` may cross the OER
  boundary. OSE-1460 (PO decision 2026-10-01) says they may not: the returns
  export becomes corridor counts with neither field, in ourSharedEvents
  PR #737 (open as of 2026-10-01).

---

## Implementation

- **ourSharedEvents, OSE-616 slice 1:**
  - The export's `corridor_id` is now the event's res7 cell
    (`COALESCE(h3_res7, corridor_id)`). Before this, every event-joined row said `'unknown'`.
  - `src/lib/export-geography.ts` rejects any row finer than res7.
  - `tests/scan-to-export-trace.spec.ts` traces one Eagles Hall scan and one
    shortlink click through every hop.
  - `scripts/ci/trace-scan-staging.sh` checks the scan step on staging (T4).
- **Brain:** add this ADR to the geography invariants' evidence. #2 hyperlocal
  geo-resolution, #4 NCR accumulation and #17 OER emission boundary should
  cite it. Record named-corridor ↔ res7 membership in
  `corridor-definitions.yaml` when OSE-613 lands.
- **Docs:** `QR-AND-SHORTLINKS.md` open decisions #1 and #3 point here and
  close.

## Validation

- `tests/scan-to-export-trace.spec.ts` (T0 `worker-d1-schema`):
  - the poster/venue res9 = `89266454447ffff` and corridor res7 = `872664544ffffff` at every hop
    (one fixture where the poster and the venue share a cell — see the gap below);
  - a click resolves to its event at the venue res7;
  - export rows carry `corridor_id` = res7, and res9 appears nowhere in the payload;
  - a res9-keyed corridor row fails the export phase closed.
- `tests/poster-deployments-h3-tagging.spec.ts` 8b–8e:
  - no device geolocation;
  - a scan's place is the poster's res9;
  - shortlinks hold no place;
  - nothing stores finer than res9.
- `scripts/ci/trace-scan-staging.sh` (T4): a real staging scan of the Eagles
  test poster lands at res9/res7.

**Not yet validated — rule 1 for a poster away from the venue.** The trace
fixture puts the poster and the venue in the same res9 cell, so it cannot tell
"the scan was placed at its poster" from "the scan was placed at the venue".
Today's code does the second (see Negative / trade-offs), and the trace would
pass either way. OSE-1459 changes the aggregation and adds a fixture whose
poster and venue are in different res9 cells, asserting the poster's cell
before aggregation and export. Until then, rule 1 is enforced for the scan
row (it stores no place of its own) but not for the aggregate.

## Open questions

- Corridor registry: permanent ids, versioned definitions,
  `definition_version` stamping. → OSE-613 / OSE-603.
- Per-placement scan aggregation, so poster scans aggregate at the poster's
  res9. → OSE-1459.
- ~~Export time grain and the `anon_id_hash` / `venue_id` boundary
  question~~ → decided 2026-10-01 under OSE-1460 (see the notes above);
  implementation in ourSharedEvents PR #737.

## References

- `OCR_VISION.md` — NCR (Node res9, Corridor res7)
- `ocr-docs-brain/corridor-definitions.yaml` — `blue_island.geo.anchor_h3_res7 = 872664544ffffff`
- `docs/architecture/OCR_ARCHITECTURE_oerAggregationBoundary.md` — "Location: corridor-level only"
- ourSharedEvents `migrations/0046_density_tables_drop_corridor_fk.sql`, `docs/features/QR-AND-SHORTLINKS.md`, `docs/discovery/OSE_REFERENCE_posterPrimitiveReconciliation_2026-09-04.md`
- Linear: OSE-616 (scan → export trace), OSE-613 (corridor registry), OSE-614 (channel-capped resolution), OSE-603 (snapshots)
