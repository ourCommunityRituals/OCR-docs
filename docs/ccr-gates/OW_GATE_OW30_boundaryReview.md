# CCR Gate Review — OW-30: ourSharedEvents Integration (Event Playlist Linking)

> **Status:** BLOCKED — must pass CCR review before moving to In Progress
> **Flagged by:** Bloodraven sync (2026-04-09)
> **Boundary rule:** OCR_DEPENDENCY_crossRepo.md lines 39–49

---

## The rule

> OW uses named identity. OSE uses anonymous ID. This boundary is architectural and permanent. The two data models never cross. When both converge under OCR, they join at the BigQuery layer with separate schemas — not at the application layer.
>
> This is not a dependency to manage. It is a constraint to enforce. Any proposed integration that would cross this boundary must fail CCR review.

— `docs/references/OCR_DEPENDENCY_crossRepo.md`

---

## The proposal

OW-30 proposes a D1 `event_playlists` junction table with an `event_id` column, linking OW playlists to OSE events.

---

## Current compliant pattern

OW already stores `event_id` in its `attributions` table (`migrations/0006_dj_attribution.sql`). This is compliant because:

- OSE calls OW (not the reverse) via `GET /api/events/:id/music`
- OW returns **aggregate music data only** — tracks, DJ stats, attribution counts
- No listener PII crosses the boundary (stripped via `sanitizeForExport()`)
- The `event_id` is used purely for OW-internal features ("Discovered at [venue]" playlists)
- OSE never writes to or reads from OW's attribution tables directly

The privacy boundary is documented in `ourWKRP/src/lib/privacy.ts`:

```
WITHIN ourWKRP: full identity, attribution, tracking (user consented)
CROSSING TO OSE: aggregate only, no PII, no listener identities
```

---

## What passes

An `event_playlists` table is **compliant** if:

1. It lives entirely in OW's D1 database
2. OSE never writes to or reads from it directly
3. OW does not export `contributor_id`, `contributor_name`, or `playlist_id` to OSE
4. OSE does not store any OW identity reference in its own database
5. The `event_id` is contextual metadata for OW-internal features only
6. At the BigQuery layer, OW and OSE maintain separate schemas

---

## What fails

The table is **non-compliant** if:

1. OSE stores OW `playlist_id` or `contributor_id` in its own database
2. OSE API endpoints return OW contributor names or playlist references without sanitization
3. The table becomes a shared data store with bidirectional references between named and anonymous IDs
4. Any application-layer join between OW named identity and OSE anonymous behavioral data

---

## Required before In Progress

- [ ] `event_playlists` migration file written and reviewed against the pass/fail criteria above
- [ ] Design decision documented: is the table purely internal to OW?
- [ ] Privacy boundary reaffirmed in code comments on any new handler
- [ ] This CCR gate review signed off by PO

---

*Reviewed: April 9 2026*
*Reviewer: Bloodraven sync + CCR gate*
*Status: BLOCKED pending design review*
