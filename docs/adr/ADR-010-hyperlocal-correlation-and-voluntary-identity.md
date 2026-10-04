# ADR-010: The hyperlocal map — cross-product correlation as a write-time shared-key contract, under a voluntary-identity covenant

**Status:** Proposed
**Date:** 2026-09-10
**Deciders:** Matt (founder / PO)
**Scope:** Fleet-wide (product purpose + cross-product data architecture)
**Supersedes:** None
**Cross-refs:** ADR-009 (hybrid is a composition plane — *where* OSE+OW are composed; this ADR is *how their data correlates*); ADR-002 (identity-profile-keyed invariants — the anon/identified boundary); ADR-006 (free-forever guardrails — the commons economics); OSE-local ADR-010 (Templates = Breadth — why every event type is joinable); OSE-1220 (declined regimes — HIPAA/COPPA/SOPPA); `OCR-docs/docs/OCR_VISION.md`

---

## Purpose (why this platform exists)

**Make your hyperlocal community economy visible and participable.** The map
shows what is actually happening in your corridor — all the kinds of events you
can get involved in, who is putting them on, who is already there — and lets a
person say *"this is where you can see me, and this is who I'm working with."*
Online, but rooted in a real place.

Every architectural decision in this ADR is in service of that purpose. The
privacy machinery is not a brake on the mission; it is what makes a real person
willing to show up, participate, and *choose* to be seen. **Participation
infrastructure, never a surveillance archive** (Invariant #8, stated as mission).

## The six base templates — one covenant

The six base templates are the foundational families of community participation.
They are the top of the breadth axis (the event types under them) and the base
facets of a profile — a person is many of them at once, self-declared. Each
stresses a different load-bearing property of the same architecture:

| Facet | Declared as | Stresses | Proves the platform is… |
|-------|-------------|----------|-------------------------|
| **Worship** | "how I worship" | the commons — free forever, seen by choice | **safe** (protection) |
| **Arts** | "my art / who I create with" | provable draw, ethical value flow | **generative** (enable) |
| **Sports** | "my team / league" | recurrence, longitudinal belonging, youth-protected | **enduring** (returns) |
| **Academic** | "what I study" | institutions hold consent, item-tracking, feeds the aggregate | **legible** (learns about itself) |
| **Volunteer** | "how I serve" | reciprocity — the give-back that runs through the others | **self-sustaining** (replenishes) |
| **Hobbyist** | "what I make / play / collect" | the long tail — every niche is a first-class event type | **inclusive** (room for every passion) |

Worship and volunteer sit on the **commons** side (never metered — see ADR-006
faith-organization free-forever). Arts, sports, and academic are where identity,
recurrence, and value flow. Volunteer is the thread that keeps the map a commons
and not merely a marketplace. Hobbyist is the proof of breadth — the model-rail
club, the bonsai society, the board-game night — every niche is joinable, which
is why **templates never gate** (OSE-local ADR-010: Templates = Breadth).

**These six are the base templates.** They are the foundational families of
community participation — the top of the breadth axis — and they double as the
base facets of a profile (athlete, artist, academic, worshipper, volunteer,
hobbyist). Every specific event type rolls up under exactly one base template
(a bocce league under Sports, a gallery night under Arts, a bonsai society under
Hobbyist, a food drive under Volunteer), and **no base template ever gates** —
every tier gets all six (OSE-local ADR-010: Templates = Breadth; tiers gate
depth, never breadth). Breadth lives in the open-ended set of types *under* each
base template; the six families themselves are the stable canon. A new kind of
gathering is a new type under an existing base template, not a new regime and
not a code branch.

## Decision

**Cross-product community data correlates at
`{corridor → venue → event_type → event}` granularity via keys stamped into
both data planes at *write time*. There is no cross-database join. Person-level
connection to participation is opt-in self-declaration only — never inferred —
and `event` is the finest grain at which the planes ever meet.**

### 1. The correlation spine (identity-free, hierarchical)

Two independent D1 databases (OSE anonymous, OW identified) never join. They do
not need to: at creation, both stamp the **same shared, identity-free keys**, so
the data is connected by construction. BigQuery later aggregates on keys that
already agree.

```
corridor             ← H3-derived (pure function of lat/lon; shared automatically)
  └─ venue           ← venue_canonical_id (shared normalization contract)
       └─ event type ← uec_code (single brain taxonomy; classified ONCE)
            └─ event ← event_correlation_id = hash(venue + uec_code + time_bucket)   ← finest grain
```

These map onto the existing `REQUIRED_TAGS` (`corridor_id`, `venue_id`,
`event_type`, `uec_code`, `product_id`); `event_correlation_id` is the one
net-new key. Type in the key is the **single brain-canonical `uec_code`**,
classified once (at setup / from the shared taxonomy), never a per-product type
string — otherwise the two planes classify independently, the hash diverges, and
the halves silently fail to correlate. The venue-normalization and
single-classification rules are a **shared contract** (brain / OSM contract
layer), contract-tested, not reimplemented per product.

*Decided 2026-10-04 (PO; OSE-1614, `ourSharedEvents/.telemetry/tracking-plan.md`). The ADR as a whole stays Proposed; the first three points below are settled within it, the fourth is not.*

- **`time_bucket`** is the **local date of the event's start in its own IANA zone, minus one day when the local start time is before 04:00**, written `YYYY-MM-DD` (a date-only event uses its start date). The rule is on the wall clock, not "minus 4 hours" on the instant, because the two disagree on a daylight-saving day and both planes must compute the same id. The plan carries six test vectors. A late league night stays one id; two nights at the same venue in one week stay apart. The hash input is versioned (`v1`) so a later rule change is visible.
- **`venue_canonical_id`** is a **stored, server-computed column** on the product's events table: a hash of the normalised venue name and the H3 res-7 cell (SHA-256, `v1`; the exact normalisation and hash layout are pinned with fixtures in the tracking plan). No coordinates enter the hash, and there is no venue registry yet. Known limit: one venue geocoded into two neighbouring cells gets two ids. **A key is null when any input is missing**; it is never computed from part of its inputs.
- **`event_correlation_id` means "the same event"**: same venue, type and night. It does not group a league's nights across venues, because the venue is inside the hash. A league or season roll-up joins on the tenant (`brand_id`) plus `uec_code` and dates. When the league owns its events, `brand_id` alone is enough. When the venues own them, a consented, people-free league-to-event mapping says which events are the league's.
- **OW receives the keys**, never person-level rows. OSE and OW are each to stamp them at write time from the shared normalisation, and their data meets in the pool dataset, not in a join. Exports and roll-ups carry the keys only for listed events, and never return a total from which a withheld count could be worked out.
- **Open: do venue-grain keys cross the BigQuery boundary?** Section 3 below assumes they do. `OCR_ARCHITECTURE_oerAggregationBoundary.md` ("corridor-level only"), the export guard in `ourSharedEvents` (`lib/export-geography.ts`) and OSE-1460 ("the venue never leaves") say that today they do not. The PO has not yet reconciled them; the tracking plan sets out four options (keys on the event rows only, which already cross as `events_backup`; that plus per-event floored counts; keys stay in OSE; a separate keyed dataset). Until then, nothing in this note authorises an export of either key.

### 2. The voluntary-identity covenant

There are two kinds of connection, on opposite sides of the covenant line:

- **Role/event-level — automatic, anonymous, safe.** Sponsor ↔ event ↔ attendee
  correlate through the shared characteristics with no identity. This happens by
  construction, for everyone.
- **Person-level — opt-in, self-declared.** When a person says *"this is me, and
  I am all of these things,"* they voluntarily step from the anonymous plane into
  the identified one. The system never infers who an anonymous scanner was; the
  person *claims* their participation.

**Forbidden** = involuntary re-identification (silently joining a scan to a
name). **The product** = voluntary, multi-role identity. `event` is the finest
join grain; below it (individual scan, attendee, profile-to-scan) is forbidden
and is exactly what the K-anon floor suppresses on the OSE side before anything
reaches the aggregate. The anonymity floor is the *default that protects the
person until they choose to step forward*.

### 3. Convergence is BigQuery, not D1

Each product exports to its own BigQuery dataset (OSE → `oureventring_general`).
The de-identified `oureventring_aggregate` layer is the meeting point the RAG
reads. Cross-product intelligence lives there, keyed on the correlation spine —
never a raw profile joined to a raw anonymous row.

## Consequences

- **Easier:** a person sees a map of their own corridor and steps in; an artist
  proves the crowd they drew (anonymized, K-floored SharedReport) without
  exposing a single attendee; a hospital/library/rec-league is served in the
  `general` pool without entering a declined regime (OSE-1220).
- **Must be maintained:** the shared canonicalization + single-classification
  contract (drift silently breaks correlation) — it belongs in the brain/OSM
  layer and must be contract-tested. The K-anon floor must hold on the OSE side
  before export. The `event`-is-finest-grain rule must never be relaxed.
- **Retires an anti-pattern:** "solve it with a cross-database join." The planes
  are isolated on purpose; correlation is designed in at write time, not
  reconstructed at query time.
- **Risk accepted:** if the two planes ever classify the same event differently,
  a real event splits into two un-joinable halves — hence classification is
  single-sourced and gated.

## Worked example — worship (why the covenant *protects*)

A place of worship is foundational community infrastructure — a commons, free
forever (ADR-006). On the map it is a venue and an event type, joinable like any
other. In the profile, *"this is how I worship"* is a self-declared facet.
Religious participation is anonymous by default and named only by choice: a
person can belong — be counted in the aggregate — without a record of their
faith being built behind their back. **Freedom of worship as freedom of
participation**, protected by the same covenant that protects every attendee.

## Worked example — the arts (why the covenant *enables*)

The arts are OW's native ground (music curation, artist/DJ pages). On the map,
arts events make the local *scene* legible at corridor granularity. In the
profile, the artist is the proudest self-declaration — visibility is the point.
The same covenant that keeps the attendee anonymous lets the artist prove their
draw: an anonymized, K-floored SharedReport shows the crowd a night pulled, so a
sponsor or venue can back the artist — value flowing into the corridor, honestly,
because the proof layer never sells out the attendee.

## Worked example — sports (why the covenant *endures*)

Sports is the archetype of the recurring, team-based gathering — the founding
case is the Thursday bocce league. On the map it is a league at a venue in a
corridor; in the profile, *"my team / my league"* is a self-declaration that is
often **collective**, not just individual. Sports is where the platform proves
*belonging over time*: the same crew back every week, measured by the corridor
density and return-rate baselines (`refreshCorridorBaselines`, the 30d/90d
windows). And it is the youth-protection proof — a rec-centre youth league is
served in the `general` pool by tracking the league, never the child, so SOPPA
and COPPA stay declined while the community is still served (OSE-1220).

## Worked example — academic (why the covenant is *legible*)

Academic gatherings — lectures, workshops, study groups, the library
summer-reading programme — make the corridor's learning life visible. In the
profile, *"what I study / teach"* is the declared facet. Academic is the
cleanest case for the item-tracking principle: the **institution holds the
roster and the consent**; OCR holds only the programme's scans by week. That is
how student-adjacent contexts are served while **SOPPA stays declined** — the
same refusal `phaseToPool` enforces. It also closes the loop to the endgame: the
de-identified aggregate the RAG reads is a community learning *about itself*.

## Worked example — volunteer (why the covenant is *self-sustaining*)

Service days, food drives, cleanups, mutual aid — the community taking care of
itself, often organised by the same institutions that host worship. In the
profile, *"how I serve"* is the give-back facet, and it is the thread that runs
*through* the others: the artist who teaches a free workshop, the athlete who
coaches youth, the academic who tutors. Volunteer is what keeps the map a
**commons** and not merely a marketplace — people replenish the corridor they
draw from. Like worship it is never metered (ADR-006); a sponsor backing a
cleanup is pure local investment, the covenant at its most honest.

## Worked example — hobbyist (why the covenant is *inclusive*)

The model-rail club, the bonsai society, the board-game night, the birders —
the long tail of community passion. On the map, every niche is a first-class,
joinable event type; in the profile, *"what I make / play / collect"* is a
declared facet like any other. Hobbyist is the proof of breadth: it is why
**templates never gate** (OSE-local ADR-010 — Templates = Breadth). A new kind
of gathering is a new type under an existing base template, never a new regime
and never a code branch — so the map has room for every passion, not only the
marquee ones.
