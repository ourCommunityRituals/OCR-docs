# CCR — OSE-1242 attendee map approach

**Date:** 2026-09-05
**Target:** the shipped backend (`GET /api/v2/events/map`, `lib/corridor-readiness.ts`) and the planned front end, per OSE-1242.
**Panel:** extended scrum team (PO, BE, FD, Sr Design FE, Sr Automation QA, SRE/SDET, DevOps) **+ Director of Security**.
**Protocol:** Critical · Conservative · Recursive, 3 loops, 95% gate.

> **Verdict: HELD → PASS (holds resolved same day).** Two High findings, one a
> direct violation of a ratified architectural invariant that shipped past the
> CI gate written to prevent it. All four holds are closed; see the resolution
> log at the end. Three follow-ons remain open and are NOT holds.

---

## Loop 1 — Critical: what would break this?

### 1.1 · HIGH · BE + Director of Security · The map is a public list query with no brand scoping — Invariant #9

`src/handlers/events-map.ts:145`:

```sql
WHERE h3_res7 = ? AND status = 'active'
```

There is no `brand_id`. Invariant #9 (tenant isolation) is stated in
`tests/e2e/0-architecture/tenant-isolation.invariant.spec.ts:21` as *"public
list queries use `WHERE brand_id = ?`"*, and the reason is given at line 132:
*"without this filter every tenant sees every brand."*

A corridor is a geography, and **white-label instances share geographies by
design** — that is the entire premise of OA and of "Bronzeville's ourWKRP" /
"Reckless Records' ourWKRP" occupying the same city. So this is not a
theoretical leak awaiting a second tenant. The moment two brands operate in one
corridor, each brand's map lists the other's events, on an unauthenticated
endpoint.

**Security note (Dr. Security):** the leak direction matters. This is not a
tenant reading their own data — it is an **anonymous caller** enumerating every
brand's event inventory in a geography, including brands whose relationship to
that corridor may itself be confidential (a venue negotiating a partnership, a
franchise pre-launch). Invariant #9 is not only a correctness rule here; it is
the confidentiality boundary between competing licensees.

### 1.2 · HIGH · Sr Automation QA + DevOps · The gate that exists to catch 1.1 cannot catch it

`tenant-isolation.invariant.spec.ts:124`:

```ts
test('OSE-INV9 | ... public list (handleListEvents) uses WHERE brand_id = ? filter', () => {
  expect(existsSync(EVENTS_HANDLER), 'handlers/events.ts must exist').toBe(true);
```

The gate asserts the property of **one named function in one named file**. A new
public list endpoint in a new file is invisible to it. The invariant is
therefore enforced for `handleListEvents` specifically, not for "public list
queries" generally — which is what the invariant actually says.

This is the **second** instance of the same defect class found in one day. The
first: `.includes('handlers/events')` inside `Object.keys().find()` in
`slug-permanence.spec.ts` and `regulatory-label-unavailable.spec.ts`, which
silently retargeted onto `events-map.ts` the moment it existed. Both are gates
that **name their subject instead of describing their property**, and both
degrade silently — one by passing vacuously, one by testing the wrong file.

A gate that enumerates its subjects has a maintenance burden nobody is
assigned; a gate that describes its property does not. This should be treated as
a systemic finding, not two incidents.

### 1.3 · MEDIUM · SRE/SDET · The query is unbounded in both rows and time

`status = 'active'` does not expire. An event stays active after it happens
unless archived, so the query returns **every active event that has ever been in
that corridor**, and JS then filters to the 90-day window. Consequences:

- the row count grows monotonically with corridor age, forever;
- there is **no `LIMIT`**, so a dense mature corridor returns an unbounded
  payload to a mobile client on cellular;
- the work is done per request, at the edge, on the highest-traffic future
  surface.

The filtering happens in `corridor-readiness` deliberately (so gate and display
cannot diverge — that part is right), but the *fetch* should still be bounded.

### 1.4 · MEDIUM · SRE/SDET · No index on `events.h3_res7`

`migrations/0037` adds the column; no migration indexes it. Every map request is
a full scan of `events`. Note that the tenant-isolation gate
(`tenant-isolation.invariant.spec.ts:72-76`) already asserts an index exists for
the `brand_id + status` list query, with the rationale *"without this index,
tenant-scoped public list queries do full table scans."* The identical argument
applies here and no index was added.

Fixing 1.1 makes this concrete: the composite the map needs is
`(brand_id, h3_res7, status, start_date)`.

### 1.5 · MEDIUM · Director of Security · Precise coordinates on a public endpoint, for events that may be residential

The response emits per-event `lat`/`lon`. VISION §6.2b explicitly scopes this
product to *"a backyard gathering"* as well as *"a library programme"*. A
backyard gathering pinned at precise coordinates on an unauthenticated,
enumerable endpoint publishes **a home address**.

**This is pre-existing, not introduced here** — `GET /api/v2/events` already
emits `lat`/`lon` because `enrichWithPhase` spreads the whole row and
`data-provider.ts:228` selects them. So the map is *consistent* with the
existing surface rather than worse than it.

But the map **materially changes the exploitability**: a list is read one event
at a time by a human, while a map is a cell-enumerable bulk interface with
coordinates as its payload. The same data at a different aggregation is a
different exposure. The honest framing is: the map does not create this hole, it
industrialises it.

Two sub-findings:

- **(a)** `enrichWithPhase` spreads `...row`, so **every column in the SELECT
  reaches the public JSON** — currently `brand_id`, `corridor_id`, `h3_res9`,
  `h3_res7`, `legal_clearance_tier`, `lat`, `lon`. Nobody chose that list; it is
  whatever the SELECT happens to project. The map handler's fixed allowlist is
  the correct pattern and the list endpoint lacks it.
- **(b)** `h3_res9` is emitted publicly. Res 9 is the ~0.1 km² **node**
  resolution. The map endpoint carefully refuses to *accept* res-9 precision;
  the list endpoint freely *emits* it. The precision floor is enforced on the
  way in and not on the way out.

### 1.6 · MEDIUM · Director of Security · No rate limit on an enumerable endpoint

`lib/rate-limit.ts` exists and is applied to admin (`router.ts:464`) and
shared-report minting (`:1083`). The map has none. The cell space is
enumerable — a metro is a few hundred res-7 cells — so the endpoint is a bulk
export of every event with coordinates, at whatever rate the caller likes.

Combined with 1.5 this is the actual risk: not "one address leaked" but
"scriptable harvest of every gathering location in a region."

### 1.7 · MEDIUM · PO · `ready` ships before latching exists, and it is an API contract

The response carries `ready`. §6.2b requires readiness to **latch** — once
cleared, stays cleared — and that is explicitly unbuilt. So `ready` currently
flaps: a corridor at 5 events drops to 4 when one wraps, and a reader's front
door reorders between visits.

Shipping the field now means the first consumer binds to flapping semantics, and
adding the latch later changes behaviour for anyone already reading it. A field
in a public response is a contract from its first deploy, not from its first
intended use.

### 1.8 · LOW · BE · Doctrine claims a clearance filter that no surface implements

§6.2b: *"It is a listing, not a census. The surface shows what is cleared and
listed across the clearance lattice."* `events.legal_clearance_tier` exists
(`migrations/0023:65`, `INTEGER DEFAULT 1`). **No public surface filters on
it** — not the list, not the map. The claim is currently aspirational.

Also noted: `mock-data.ts:193` sets `legal_clearance_tier: 'tier-1'` (a string)
against an `INTEGER` column. The fixture and the schema disagree about the type.

### 1.9 · LOW · FD · The front end's hardest case is unspecified

The spec covers pin → pop-out → flow. It does not cover the state the surface is
in **most often on first visit**: geolocation not yet granted, denied, or
unavailable (desktop, VPN, privacy browser). The endpoint requires a cell and
the device is the only thing that can produce one, so "no position" is not an
edge case — it is the default state of every first load, and the surface has no
answer for it.

---

## Loop 2 — Conservative: what is the smallest version that still ships value?

### 2.1 · **CUT** · Remove `ready` from the response until the latch exists

It is the only field with no consumer and unsettled semantics. Cutting it now
costs nothing and avoids shipping a contract the doctrine says is wrong.
Reinstate it in the same story that builds the latch. (Resolves 1.7.)

### 2.2 · **KEEP** · The cell-only refusal, in full

The coordinate refusal and the resolution pin are the load-bearing parts and
should not be trimmed. They are what makes §6.2b's "by construction" claim true,
and 14 tests fail without them.

### 2.3 · **DEFER** · Client-side H3 (~94KB) — pass the cell explicitly first

The front end does not need `h3-js` to prove the surface works. A first cut can
accept a cell from a corridor picker (or a link, or a saved corridor) and skip
geolocation entirely. That ships the map, the pop-out and the phase routing —
the actual product — without paying 94KB or building the permission-denied flow
on day one.

It also **inverts the risk**: a corridor picker has no permission prompt, works
on desktop, and is the fallback 1.9 needs anyway. Geolocation becomes an
enhancement on top of a working surface rather than a prerequisite for it.

### 2.4 · **DEFER** · The clearance-lattice filter (1.8)

Real, but not this story's. It applies equally to `/events`, and doing it here
would make the map and the list disagree — the exact divergence OSE-1243 spent
a day removing. One story, both surfaces.

### 2.5 · **KEEP** · The `LIMIT` and the index

Small, and they are the difference between a surface that works in a founding
corridor and one that works in a mature one. Not deferrable past first deploy.

---

## Loop 3 — Recursive: what does this imply we should also do?

### 3.1 · **REQUIRED** · Rewrite the tenant-isolation gate to describe its property

`OSE-INV9` must assert *"every handler that issues a SELECT against a
multi-tenant table binds `brand_id`"* — enumerating handlers by scanning the
directory, not by naming one file. Same for the clearance and PII gates if they
are written the same way (they should be audited).

**This is the finding with the longest reach.** Every invariant enforced by
naming its subject is one refactor away from being unenforced, and the failure
is silent. Two instances surfaced today by accident; nobody has counted the
rest.

### 3.2 · **REQUIRED** · Give `GET /api/v2/events` a fixed field allowlist

`enrichWithPhase` spreading `...row` means the public contract is whatever the
SELECT projects. Adopt the map handler's pattern. This is the fix for 1.5(a) and
1.5(b) together, and it is a **contract change**, so it needs its own story and
a check of existing consumers (display, poster, shared-report surfaces).

### 3.3 · **REQUIRED** · Decide the coordinate-precision policy, product-wide

1.5 is a product decision, not a bug to patch: **what location precision does a
public surface publish for an event at a private residence?** Options include
emitting the res-9 cell centroid instead of the venue point, precision by
clearance tier, or organiser opt-in for exact placement. It affects map, list,
poster and the sponsor bundle.

Until it is decided, the map is publishing home addresses for backyard
gatherings and calling it a feature. **This is the item a Director of Security
would escalate above the story.**

### 3.4 · **RECOMMENDED** · Rate-limit public read endpoints as a class

Not just the map. `lib/rate-limit.ts` already exists; the gap is that it is
applied per-route by hand, so every new public route starts unlimited. A
default-on middleware with an opt-out inverts that.

### 3.5 · **RECOMMENDED** · A contract test asserting the two public surfaces agree on emission

The map and the list now describe the same events. OSE-1243 added parity tests
for phase→CTA; the same is needed for **field emission**, so the two cannot
drift into publishing different amounts about the same event.

### 3.6 · **NICE-TO-HAVE** · Fix the `mock-data.ts` clearance-tier type mismatch (1.8)

String `'tier-1'` against `INTEGER DEFAULT 1`. Harmless today because nothing
reads it; a trap for whoever implements 2.4.

---

## Synthesis

### Verdict: **HELD**

The privacy architecture is genuinely good — the coordinate refusal and
resolution pin make Invariant #1 structural, and the readiness gate cannot
promote a card onto an empty map. But the endpoint ships a **tenant isolation
violation** on an unauthenticated public route, and the gate written to prevent
exactly that could not see it. That combination is not a PASS.

### Top three concerns

1. **1.1** — public list query without `brand_id`; Invariant #9 violated on an anonymous endpoint, in a product whose whole model is multiple brands sharing geographies.
2. **1.2 / 3.1** — the invariant gates name their subjects instead of describing their properties, so they degrade silently on refactor. Two instances found in one day, by accident.
3. **1.5 / 3.3** — precise coordinates for potentially residential events on an enumerable public endpoint. Pre-existing, industrialised by the map, and a product decision nobody has made.

### Top three follow-ons

1. **3.1** — rewrite `OSE-INV9` to scan handlers rather than name one.
2. **3.3** — set the coordinate-precision policy product-wide.
3. **3.2** — fixed field allowlist on `GET /api/v2/events`; stop spreading rows into public JSON.

### Holds — all must resolve before PASS

| # | Hold | Converts to PASS when |
|---|---|---|
| H1 | Invariant #9 violation (1.1) | the map query binds `brand_id`, with a test that fails without it |
| H2 | The gate cannot catch H1 (1.2) | `OSE-INV9` enumerates handlers by scanning, and fails on a brand-less public SELECT in any file |
| H3 | Unbounded query (1.3) + missing index (1.4) | a `LIMIT` is in place and a composite index covers `(brand_id, h3_res7, status, start_date)` |
| H4 | `ready` ships without its latch (1.7) | the field is removed from the response, or the latch is built |

H1–H3 are defects in shipped code and should be fixed now. H4 is a scope
decision (Loop 2.1 recommends cutting the field).

**Confidence: 93%.** Below the 95% gate, so the human gate is active. The 7%
is concentrated in 3.3 — the coordinate-precision question is a product
decision this panel cannot make, and it is the finding most likely to change
what the surface should do.


---

## Resolution log — 2026-09-05, same day

| Hold | Resolution | Evidence |
|---|---|---|
| **H1** Invariant #9 | `events-map.ts` binds `brand_id`, echoes it back | test asserts brand is the first bound parameter |
| **H2** Gate blind to H1 | `OSE-INV9` rewritten to scan every handler | reverting H1 turns it red, naming file and line |
| **H3** Unbounded + no index | date floor + horizon + `LIMIT 250`; migration `0069` adds `(brand_id, h3_res7, status, start_date)` | index-count gates bumped 67 → 68 |
| **H4** `ready` without its latch | field removed; `windowDays`/`minEvents` still published | test asserts the response has no `ready` property |

### What H2 found the moment it could see

Rewriting the gate to describe its property rather than name its subject
immediately surfaced a **pre-existing Invariant #9 violation nobody had
looked for**: `pages.ts:1259`, the **public** post-event recap, suggests *"other
upcoming events at this venue"* with no brand filter. A venue hosting two
white-label instances advertised each brand's events on the other's recap page.
`row.brand_id` was already selected two hundred lines above; the filter was
simply never written.

That is the argument for 3.1 stated as evidence rather than as an opinion: the
named-subject gate had been green for the entire life of that leak.

Six other hits were triaged into `BRAND_SCOPE_EXEMPT` with a reason each — two
were comments (the matcher now skips comment lines), one is a correlated
sub-select keyed by column, and three are scoped by dynamically-built `WHERE`
clauses that no static scan can see. The baseline cannot grow silently: an
unlisted violation fails.

### On H3's date floor — a decision worth recording

The scan floor is **a week behind now**, not `now`. A hard `start_date >= now`
would bound the scan correctly and be **wrong**, because the past edge is
decided by `phase` downstream and a multi-day event that began two days ago is
still live. The floor exists to bound the scan; `corridor-readiness` still owns
the window. Getting this backwards would have dropped events from the map *while
they were happening* — the same class of error the naive-filter test in
`corridor-readiness.spec.ts` was written to catch.

### Still open — carried, not closed

These were never holds and remain outstanding:

1. **3.3 — coordinate-precision policy** (from 1.5). Precise `lat`/`lon` for
   potentially residential events on an enumerable public endpoint. Pre-existing
   and product-wide; the map industrialises it rather than creating it. **This is
   the item the Director of Security lens would escalate above the story.**
2. **3.2 — field allowlist on `GET /api/v2/events`** (from 1.5a/b). `...row`
   spreading means the public contract is whatever the SELECT projects —
   currently including `h3_res9`, the ~0.1 km² node cell. The map refuses to
   *accept* res-9 precision while the list freely *emits* it.
3. **3.4 — rate limiting public reads as a class** (from 1.6). Applied per-route
   by hand today, so every new public route starts unlimited.

**Post-resolution confidence: 96%.** Above the gate. The residual is 3.3, which
is a product decision this panel cannot make.
