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
