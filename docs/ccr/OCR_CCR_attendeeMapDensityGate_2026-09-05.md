# CCR — Attendee map & the density gate (proposed VISION amendment)

**Date:** 2026-09-05 · **Tier:** governance (6 loops, ≥95%) · **Verdict: PASS**
**Holds cleared:** owner statement 2026-09-05 (see Loop 6). Verdict revised HELD → PASS.
**Target:** proposed `OCR_VISION.md` amendment — the three front-door perspectives as the
Triangle's corners, and the density gate holding the attendee map closed.
**Source:** owner statement 2026-09-05 · **Surface story:** OSE-1242

---

## What the amendment would assert

1. The front door has three perspectives, one per Triangle corner: Sponsor, Event, Customer.
2. The Customer perspective is a **map of events near the viewer**.
3. It is **switched off until a corridor has enough events**, then turns on per area.
4. Turning it on "completes the Triangle."

---

## Loop 1 — Critical

**1.1 · HIGH · The amendment contradicts shipped doctrine in `corridor-map.ts`.**
That module — already built, already rendering in the SharedReport — states the saturation
doctrine as its *opposite*:

> *"honest at any density: one venue lighting one cell on day one IS the product ('watch the
> corridor fill in' — saturation doctrine visible)"*

The owner statement says hold the map until saturated, because an empty map tells a first
attendee the platform is dead. Writing the new position into VISION without reconciling
leaves VISION and code disagreeing — and `CLAUDE.md` says **code wins**, so the entry would
be born non-authoritative.

**Proposed reconciliation (not a fudge — they address different readers):** `corridor-map`
renders inside the **SharedReport**, read by a sponsor or host who already knows the event
happened; one lit cell is meaningful evidence *to them*. The attendee map is read by a
**stranger deciding whether to go out**; one cell is not a product *to them*. Same rendering,
different audience, different threshold. This must be stated explicitly, or the next
contributor wires the attendee surface to the existing module and silently inherits
"honest at any density."

**1.2 · HIGH · The threshold recommended in OSE-1242 is wrong, and contradicts a ratified constant.**
OSE-1242 proposes K=5 "for consistency." But:

| Constant | Value | Question it answers | Status |
|---|---|---|---|
| `CORRIDOR_MAP_MIN_COUNT` | 5 | is this *cell's count* safe to show? (suppression) | live |
| `CORRIDOR_BASELINE_MIN_SAMPLE` | **10 events / 30d** | does this *corridor* have enough events to say anything? | **"Q4 ratified"**, live |

The second is exactly the attendee map's question, it is already ratified, and it is already
**enforced** — `shared-report-builder.ts:336,346` gates corridor baseline claims on it and
emits `"N of 10 required"`. Recommending K=5 would introduce a **third** number for corridor
sufficiency. Correction owed to OSE-1242.

**1.3 · MEDIUM · Tier-equity (#5) collision.** `renderCorridorMap` is called from the
SharedReport's **premium** path. If the attendee map reuses it, it inherits tier gating —
and Invariant #5 holds that tiers govern *display priority within events only, never platform
access*. An attendee map that appears only where a premium sponsor exists is platform access
sold by tier. The attendee map must be tier-blind, and that is a testable claim.

**1.4 · MEDIUM · "Their location" is an unresolved identity-surface question.** How is the
viewer's corridor determined? IP geolocation is ruled out by the owner ("I don't utilize
cloudflare's map. It resolves to the H3 layer"). Browser geolocation is a permission prompt
and a new data class. A scan-derived corridor couples the map to `ose_anon`. **Each option has
a different relationship to Invariant #1.** VISION must not assert the surface exists without
naming that this is undecided.

**1.5 · MEDIUM · The gate is per-corridor, so "the landing page" is not one page.** Two people
in the same city can see a different number of cards. That is correct behaviour, but any test,
screenshot or doc asserting "the front door has N cards" is wrong by construction.

**1.6 · LOW · "Saturated within the ring" mixes two vocabularies.** A **corridor** is a
geographic container (h3 res7); a **ring** is a *detected topology* (migration 0012:
bidirectional flow, 3+ node cycle, `validation_window_count >= 2` — two seasons). Saturation is
measured per corridor; rings emerge *from* corridors and require a year or more of scan history.
Writing "saturated within the ring" into VISION licenses the wrong query and would gate the map
on a condition that cannot be met for a year.

---

## Loop 2 — Conservative

**2.1 · CUT · "Completes the Triangle."** The Triangle is **already complete** as an
architecture — §6.1 defines three corners, and the Customer corner is enforced today via
anonymous ID, QR scan and the forms funnel. What is missing is a *front-door surface* for that
corner. Asserting the Triangle is incomplete contradicts §6.1 and the invariant suite.
Say **surface**, not architecture.

**2.2 · CUT · "Three cards on the front door."** That is a UI expression of the doctrine, not
the doctrine. VISION should record that the Customer corner has a density-gated front-door
perspective; whether it renders as a third card will change.

**2.3 · DEFER · Naming the number in VISION.** Cite `CORRIDOR_BASELINE_MIN_SAMPLE`; do not
restate `10`. A doc restating a constant is precisely the drift class
`OCR_STANDARD_reconciliationLoop` §9.1 step 3 names — a number nobody re-derives.

**2.4 · KEEP · The density gate itself.** This is the load-bearing new idea and it is genuinely
org-level: *the Customer corner opens on evidence, not on launch.* Other products inherit the
pattern (OW's catalog, OSG) even though the map surface is OSE's.

**2.5 · DEFER · The map surface entirely.** Nothing in the amendment requires it to be built.

---

## Loop 3 — Recursive

**3.1 · REQUIRED ·** Correct OSE-1242's threshold recommendation (K=5 → `CORRIDOR_BASELINE_MIN_SAMPLE`).
**3.2 · REQUIRED ·** Reconcile `corridor-map.ts`'s header doctrine — its "honest at any density"
line needs an audience qualifier, or VISION must scope it explicitly. Code and doctrine cannot
disagree on the same sentence.
**3.3 · RECOMMENDED ·** When built: a test that the attendee map is tier-blind (#5).
**3.4 · RECOMMENDED ·** When built: a test that the map plots **events, never people**.
Never-who holds naturally here, and nothing enforces it — which is how it stops holding.
**3.5 · RECOMMENDED ·** Invariant #2 (Hyper-local Geo-Resolution) currently covers
*sponsor-side* corridor matching. Viewer-side corridor resolution is a new use of the same
invariant and may warrant enrichment rather than a new invariant.
**3.6 · NICE ·** OSE-1241's front door should use an intrinsic grid track so a third card joins
without a CSS change (already noted on that story).

---

## Loop 4 — Does this belong in VISION at all?

`CLAUDE.md`: *"If it is not written in `docs/OCR_VISION.md`, it does not exist at the org
level"* — and *"Pointers (not copies)"*.

**Split:** the **principle** is org-level (every product with a Customer corner faces "when do
we open it?"); the **surface** is OSE's. VISION gets one short subsection under §6; OSE-1242
keeps the map, the threshold mechanics and the UI. VISION cites the constant rather than
restating it.

**Verdict on placement: belongs, scoped to the principle.**

---

## Loop 5 — Recursion on this review

**5.1** Loop 1.2 was checked rather than asserted: `CORRIDOR_BASELINE_MIN_SAMPLE` is not a
dormant constant — 5 live references, and `shared-report-builder.ts` gates on it. The
recommendation rests on an enforced rule, not a stored intention.

**5.2** My own earlier advice in this session was the error 1.2 catches. I recommended K=5 to
the owner *before* reading `shared-report.ts`. Recorded because the pattern is the one this
session has hit repeatedly: **a plausible answer reached without reading the file that already
answers it.**

**5.3** Residual uncertainty: the reconciliation in 1.1 is *my* synthesis, not an owner
statement. It is coherent and I believe it, but "different audiences, different thresholds" is
an inference. It should be ratified, not assumed.

**Confidence: 88%** — below the 95% governance gate. The gap is 1.1 (an unratified synthesis
of two conflicting doctrines) and 1.4 (an unresolved identity-surface question). Neither is
resolvable by further review; both need an owner decision.

---

## Verdict: **HELD**

Sound direction, and the density gate is a genuine doctrine worth recording. Held because the
amendment as stated contradicts shipped code in one place, contradicts a ratified constant in
another, and rests on an unresolved question about how a viewer's location is determined.

### Top three concerns
1. `corridor-map.ts` already asserts the opposite saturation doctrine (1.1).
2. The recommended threshold contradicts a ratified, enforced constant (1.2).
3. Viewer-location resolution is undecided and touches Invariant #1 (1.4).

### Top three follow-ons
1. Correct OSE-1242's threshold (3.1).
2. Reconcile `corridor-map.ts`'s header (3.2).
3. Tier-blindness test when the surface is built (3.3).

### Holds — all must clear before PASS

| # | Hold | Who clears it |
|---|---|---|
| H1 | Ratify the audience split: `corridor-map` is honest at any density **for a reader who already knows the event happened**; the attendee map waits for density **because its reader is a stranger**. | **Owner** |
| H2 | Correct OSE-1242 to `CORRIDOR_BASELINE_MIN_SAMPLE` (10 events / 30d) and drop the K=5 recommendation. | Claude — mechanical |
| H3 | Decide how a viewer's corridor is resolved, or state in VISION that it is open. | **Owner** |
| H4 | Drop "completes the Triangle" in favour of "opens the Customer corner's surface." | Claude — mechanical |

H2 and H4 are cleared in the same run as this review. **H1 and H3 are owner decisions and are
the reason this is HELD rather than PASS.**

---

## Appendix — the amendment as it would land

**NOT WRITTEN.** Held on H1 and H3. Reproduced so the owner can see the actual text rather
than approve a description of it. Drafted to survive Loop 2: no card count, no restated
constant, no claim the Triangle was incomplete.

> ### 6.x The Customer corner opens on evidence
>
> Each Triangle corner has a front-door perspective: a sponsor arrives to be listed, an
> organiser arrives to run something, a customer arrives to find something to go to. The first
> two are answerable from an empty database. **The third is not.**
>
> A map with nothing on it does not read as "early" to someone who has never heard of us — it
> reads as abandoned. So the customer-facing perspective is **held closed until the area around
> that reader carries enough activity to be worth their attention**, and opens per area rather
> than per launch. Two people in the same city can correctly see different front doors.
>
> Sufficiency is measured **per corridor**, and the threshold is not a new number: OSE already
> ratified and enforces a corridor baseline minimum sample
> (`ourSharedEvents/src/lib/shared-report.ts` → `CORRIDOR_BASELINE_MIN_SAMPLE`, consumed by
> `shared-report-builder.ts`). The same bar that decides a corridor can be *reported* on decides
> it can be *shown*.
>
> **This is not ring emergence.** A ring is a detected topology requiring bidirectional flow
> across multiple seasons (`migrations/0012`); it is downstream of attendance, not a
> precondition for it. Gating the customer surface on ring emergence would hold it closed for
> a year by construction.
>
> **Density gates the surface, never the architecture.** The Customer corner is already
> enforced today — anonymous ID, scan, forms funnel. What waits on density is one *front door*,
> not the corner's existence, and never a tier: an area's readiness is a fact about that area,
> not a thing a sponsor can buy (Invariant #5).
>
> *Open:* how a reader's corridor is resolved is undecided and touches Invariant #1. Recorded
> here as open rather than assumed. See OSE-1242.

### Why this wording

- *"opens on evidence"* — the doctrine in four words, portable to any product with a Customer corner.
- No card count, no layout: §6 describes architecture, and the UI will change.
- Cites the constant instead of restating `10` — §9.1 step 3, the numbers nobody re-derives.
- Names the ring exclusion **inside VISION**, because that is where someone will go looking for
  permission to use ring emergence as the gate.
- States the open question rather than papering it, so the entry does not assert a resolved
  design it does not have.

---

## Loop 6 — Delta review after the owner statement (holds cleared)

### H1 — CLEARED, and reframed better than the review's synthesis

Owner: *"that shared report is a product of the event that's created. But for the attendee…
it would use their geolocation to understand what are the events that are available."*

Loop 1.1 proposed "same rendering, different audience, different threshold." That was
directionally right and **under-powered**. The real distinction is not audience, it is
**direction in time**:

| | SharedReport corridor map | Attendee map |
|---|---|---|
| Is | a **product OF** an event that happened | a **discovery surface** for events that have not |
| Looks | backward — proof | forward — what's on |
| Reader knows | the event occurred; they were part of it | nothing; they are deciding whether to go out |
| One lit cell | meaningful evidence | not a product |

Two different artifacts that happen to share a rendering technique. `corridor-map.ts`'s
"honest at any density" is **correct for a retrospective proof surface** and needs no change to
its behaviour — only an audience qualifier in its header so it is not read as a platform-wide
rule. **H1 cleared.**

### H3 — CLEARED: device geolocation, resolved to a cell

Owner: *"it would use their geolocation… for their current res seven, or larger if they wanted
to."* Plus the roaming cases — Blue Island, travelling for work, camping.

**The privacy shape falls out of this and is strong:** geolocation resolves to an **H3 cell**,
and the cell is the query key. Coordinates are a means, not a payload. This sits inside
Invariant #1 rather than straining it — the platform learns *which ~5 km² tile*, not where
someone is.

**Zoom-out needs no migration.** `h3_res7` is stored; res6/res5 are `cellToParent` computations.
"Or larger if they wanted to" is derivable from what exists.

### New findings from the delta

**6.1 · HIGH · The gate governs LAUNCH, not query results.** The roaming cases prove the map
must answer for **any** location, including ones with zero events — *"what events are going on
in this current location"* while camping. So:

- **Density gate** → when is the surface worth shipping *for a founding corridor*? (one-time,
  per area, ratified constant)
- **Zero results for a cell** → a legitimate **answer**, not a failure state.

Conflating them produces a map that refuses to answer for Blue Island because Blue Island is
quiet. The VISION wording must not license that reading.

**6.2 · MEDIUM · Coordinate handling is a real fork with a measured price.**

| Option | Coordinates leave the device? | Cost |
|---|---|---|
| Resolve to cell **in the browser** (`h3-js`) | **no** | **94 KB gzipped** on a mobile-first public page |
| Send lat/lng, resolve **server-side** | yes, transiently | free; but coordinates exist in the request, so log lines must carry the *cell*, never the input |

Recommend client-side: the property "raw coordinates never leave the device" is worth stating
publicly, and it is only true in option 1. But 94 KB is not free and this should be a decision,
not a default. **Implementation choice for OSE-1242 — not a VISION blocker**, since the doctrine
is "resolved to a cell" either way.

**6.3 · LOW · The sponsor mechanic described is already built.** *"local sponsors in my
geolocation… the event types they've signed up… I have a choice to associate them… they will
randomly show up in my header"* is `sponsor_areas` + `sponsor_event_types` (**Invariant #2**)
plus the seeded shuffle that keeps position unbuyable (**Invariant #25**, OSE-1138). Recorded so
nobody rebuilds it.

**6.4 · MEDIUM · "What's going on" implies a completeness the platform deliberately does not
offer.** The map spans the clearance lattice — backyard (layer zero) through bars, rec centres,
libraries. But `OCR_STANDARD_declinedRegimes` permanently excludes some regimes (hospital PII,
under-13 parental-clearance). An attendee map is a listing of **what is cleared and listed**, not
a census of everything happening in an area. Honest framing is cheap now and expensive later.

### Revised confidence

**96%.** H1 and H3 are answered by the owner, not inferred. 6.1 changed the wording rather than
the doctrine. 6.2 is a priced implementation choice, not an open question. Residual 4% is 6.4 —
a copy question that will be settled when the surface is designed.

## Verdict: **PASS**

Clear to write the VISION entry, with 6.1's launch-vs-answer distinction folded into the
wording and 6.4 flagged to OSE-1242.

---

## Loop 7 — Delta on the two-state landing page (owner refinement, same day)

Scope: a **refinement of the entry this review just passed**, by its author, clarifying rather
than reversing. A focused delta is proportionate; a second full six-loop pass is not, and saying
so is part of the review rather than a shortcut around it.

### What changed, and it corrects §6.2b as written

The passed entry said the customer perspective is **"held closed"** below threshold. The owner's
refinement: it is **always present**, and below the line it is an *invitation* —
*"coming soon, fill this space with events for the map of your current location."* What changes
with density is **rank and content**, not existence:

| Area state | Order | Customer card |
|---|---|---|
| Below | create event · register sponsor · **attendee** | invitation |
| At or above | **attendee** · create event · register sponsor | the map |

**This is better than what passed.** Hiding the perspective teaches a reader nothing. An honest
empty state teaches them what the place is for — and shows it to exactly the person who could
make it true. Below the line the page asks for **supply**; above it, it serves **demand**.
§6.2b amended.

### 7.1 · HIGH · The threshold now drives ORDER, so it must latch

`CORRIDOR_BASELINE_MIN_SAMPLE` is a **rolling 30-day window**. A corridor sitting near the line
(9 events one week, 11 the next) would reorder the landing page's primary CTA between one visit
and the next. Card order flapping is disorienting on its own; **demoting a reader's map because
last month was quiet is worse than never having promoted it.**

Not a problem when the threshold only governed visibility of a not-yet-built surface. It is a
problem now that it governs rank. **Readiness must latch: once an area clears the bar, it stays
cleared.** Written into §6.2b.

### 7.2 · HIGH · "Under the amount of attendees" — the metric must be EVENTS, not attendees

The owner said *"under the amount of attendees."* Almost certainly loose phrasing, but the
distinction is load-bearing and gets the design wrong if taken literally:

- **Attendee-count gate is circular.** No map → fewer people find events → fewer attendees →
  the map never opens. The gate would prevent the thing that clears it.
- **Attendee counts need scans**, which need events to have already run — so the metric cannot
  exist before the surface it gates.
- `CORRIDOR_BASELINE_MIN_SAMPLE` is **events per 30 days**, and is what the ratified constant
  already measures.

Recorded as: the gate counts **events**. Flagged to the owner rather than silently corrected.

### 7.3 · MEDIUM · The public landing now disagrees with `/admin` on order

`/admin` was flipped to **sponsor-first** earlier today, on the owner's reasoning that *"we
always want the sponsors to sign up"* and that a front door ranking the two differently by
entrance argues with itself. The below-threshold public order stated here is **event-first,
sponsor-second**.

Both are defensible — the surfaces have different readers, and an already-signed-in host is not
a cold sponsor. But the earlier flip was justified *by consistency*, so this needs an explicit
answer rather than drift: does `/admin` follow to event-first, or are the two deliberately
different now? **Owner decision, tracked on OSE-1240 / OSE-1241.**

### 7.4 · LOW · The invitation card is the attendee-becomes-host ladder

*"Fill this space… so you can see the map"* asks a reader to become a creator — the ladder
recorded earlier in this session. Worth naming so the copy is written as an on-ramp rather than
as an error state.

### Verdict on the delta: **PASS**, §6.2b amended

Two findings landed in doctrine (7.1 latching, 7.2 the metric). 7.3 is an open owner decision
that does not block the entry — it governs one surface's card order, not the doctrine.

**Confidence 94%** on the amended entry — down from 96% only because 7.3 is unresolved, and the
answer changes one shipped surface.

---

## Loop 8 — owner resolution of 7.2 and 7.3

Both open findings were put to the owner and answered. This loop records the answers, checks
what they change, and re-scores.

### 8.1 · RESOLVED · 7.2 — the gate counts **events**

Owner confirmed: reuse the ratified `CORRIDOR_BASELINE_MIN_SAMPLE` (10 events / 30 days) rather
than introducing a landing-specific constant.

Consequences checked:

- **No new number to keep honest.** The constant already has two enforcing call sites
  (`shared-report-builder.ts:336,346`). A third consumer inherits the enforcement rather than
  inventing a parallel one that can drift away from it.
- **The circularity is closed**, not merely acknowledged. The recorded reasoning is now in
  doctrine so a future reader cannot "improve" the gate into an attendee count without first
  reading why that was rejected.
- **Coupling accepted and named.** Moving the SharedReport baseline now also moves the landing
  gate. That is a real constraint and is the intended one — the doctrine states it as *"the same
  bar that decides a corridor can be reported on decides it can be shown."* If the two ever need
  to diverge, that divergence is a decision with a paper trail, which is the outcome a separate
  constant would have bought silently and prematurely.

### 8.2 · RESOLVED · 7.3 — public flips to **sponsor-first** below the threshold

Owner chose the third option: the public below-threshold order becomes
`register sponsor · create event · attendee`, matching `/admin`. `/admin` does not move.

This is the stronger resolution of the three, and for a reason worth recording:

- **The two states are now an exact inversion**, not two unrelated orderings. Below:
  sponsor · event · attendee. Above: attendee · event · sponsor. One sentence describes the whole
  behaviour, which means one sentence is all a future implementer has to hold.
- **Event lands in the middle of both**, and that is architecturally motivated rather than
  incidental: Event is the corner the other two connect *through* (§6.1). The card that is never
  first and never last is the one that is never the *point* — it is the hinge.
- **The consistency argument that created the finding is now satisfied in the direction it was
  originally made.** Sponsor-first on `/admin` was justified by consistency with the public door;
  the public door now agrees. No surface is carrying an unexplained exception.
- **Sponsor rank still falls to third above the threshold**, and this is not a contradiction of
  the above. The inversion is the rule; sponsor leads only while the page is asking for supply.
  Once the area is served by demand, the reader leads and the sponsor ask moves to where a
  sponsor with proof of density is *more* likely to convert, not less.

### 8.3 · LOW · Implementation note carried to OSE-1241

The chooser markup must not encode order in the DOM as an assumption. Build the three cards in a
single intrinsic grid track and let rank be assigned, so the inversion is a data-driven attribute
rather than two hand-maintained template branches that can fall out of step. The existing
per-link `testid` convention applies — *position is not an identity* — so tests must assert the
card by identity and its rank separately, or they will pass in both states and prove neither.

### Verdict on Loop 8: **PASS**

Both open findings are closed by owner decision; neither answer introduced a new finding. The
entry's remaining risk is implementation fidelity (8.3), which is a story-level concern with a
named gate, not a doctrine gap.

**Confidence 96%** — restored to the Loop 6 level. The two resolutions removed the only
unresolved dependency, and 8.2 improved the doctrine rather than merely settling it: the entry
now states one rule where it previously stated two orderings.

---

## Loop 9 — retraction of the Loop 8 metric finding

Triggered by the owner's map interaction spec (OSE-1242), which introduced a
**forward** display window and so forced the gate's *direction* to be stated.
Stating it revealed that the instrument had never been read.

### 9.1 · CRITICAL · The Loop 8 metric conclusion was wrong, and it is now doctrine

Loop 8 recorded, and §6.2b then asserted, that the gate reuses
`CORRIDOR_BASELINE_MIN_SAMPLE` as **"10 events / 30 days"**. The constant is
real and enforced at two call sites. Everything else about the claim is false:

| Claimed | Actual | Source |
|---|---|---|
| events | `COUNT(DISTINCT anon_id_hash)` — **attendees** | `shared-report.ts:240-256`; `migrations/0032:44` says *"rolling 30-day distinct anon_id_hash count"* |
| corridor-wide | per **(corridor, day-of-week, hour)** | `GROUP BY … bucket_dow, bucket_hour` |
| a readiness bar | a floor for publishing a **density ratio** | `shared-report-builder.ts:336-349` |
| (direction unstated) | **trailing** | `WHERE e.start_date >= floor90dIso` |

**The provenance is the finding.** Loop 8 cited `shared-report.ts:60`:

```ts
// Q4 ratified — corridor baseline minimum sample size: 10 events / 30d
export const CORRIDOR_BASELINE_MIN_SAMPLE = 10;
```

That comment disagrees with its own schema and with the query 180 lines below
it. **A comment was read as evidence and a query was not opened.** This is the
same failure mode this document has now recorded three times, and the second
time it reached a ratified artifact.

It is worse than the earlier instances in one respect: the owner's original
instinct — *"when it's under the amount of attendees"* — **matched the column**.
Loop 7 talked them out of it. The reviewer's correction was the error, and the
review's confidence in it (recorded at HIGH) came from the same unverified line.

### 9.2 · What survives the retraction

The **circularity objection does not depend on the constant**, and it stands: a
gate denominated in attendees cannot be climbed out of, because no map means
fewer attendees means the map never opens. So Loop 7's *reasoning* was sound
even though its *conclusion about the code* was not. The requirement it yields —
that the gate be something a reader can act on from the page they are standing
on — carries forward unchanged.

Everything else in §6.2b is untouched: always-present, rank-follows-density,
the inversion, readiness latching, launch-not-answers, tier-blindness, and
location-resolves-to-a-cell. **None of those cited the constant.** The blast
radius is one paragraph, which is the only reason this is a correction rather
than a rebuild.

### 9.3 · HIGH · Trailing gate vs forward surface

Independent of units, a **trailing** gate governing a **forward** surface can
fail in both directions, and one failure is precisely what §6.2b exists to
prevent: a corridor clears on history, the attendee card is promoted to first
position, and the map opens **empty** because nothing is scheduled ahead. The
mechanism meant to stop the surface reading as abandoned becomes the thing that
makes it read that way.

This could not have been caught before the interaction spec existed, because
until the map's window was stated the gate's direction was never a question.
Recorded as an argument for writing the interaction spec *before* ratifying the
gate, not after.

### 9.4 · The standing recommendation

Readiness should be a question the surface answers about **itself**: the
attendee card leads when the forward window it would open on holds at least N
events in the reader's corridor. Self-consistent (the thing counted is the thing
shown), non-circular (events come from the corner the page recruits), and it
leaves `CORRIDOR_BASELINE_MIN_SAMPLE` doing its real job. **N is a new number,
openly.** Owner decision.

### 9.5 · Process finding — what would have caught this

Loop 8 scored 96% on a claim about code that no loop had opened the code for.
The gap is that this protocol's *evidence* rule ("Verified requires citable
evidence, not 'I looked at it'") was satisfied by a citation to a **comment**.

**Proposed amendment to the CCR protocol:** a citation to a comment, a doc, or a
constant's *name* is not evidence of runtime behaviour. Behavioural claims cite
the **query, the expression, or the test that exercises it**. A constant may be
cited for its value; never for its meaning.

### Verdict on Loop 9: **RETRACTION ACCEPTED — the entry stands, minus one claim**

§6.2b amended: the metric paragraph is replaced with the correction, the
surviving circularity requirement, the trailing-vs-forward finding, and the
recommendation. The gate instrument is now an **open owner decision** on
OSE-1242 rather than settled doctrine.

**Confidence 91%** on the amended entry — below Loop 8's 96% and correctly so.
The design is better evidenced than it was; the gate is now honestly marked
unresolved instead of falsely marked settled. A number that goes *down* after a
loop that improved the document is the protocol working.

---

## Loop 10 — owner decision on the gate instrument

Loop 9 retracted the metric and left the instrument open. The owner accepted the
recommendation and set **N = 5**.

### 10.1 · RESOLVED · The gate is the surface's own forward window

> The customer card leads when the **forward window it would open on** holds at
> least **5 events** in the reader's corridor.

| | |
|---|---|
| Unit | events |
| Grain | corridor (H3 res7), whole |
| Direction | **forward**, now → +90 days — the same window the map displays |
| Threshold | **5** |
| Constant | `ourSharedEvents/src/lib/corridor-readiness.ts` → `CORRIDOR_READY_MIN_EVENTS` |

### 10.2 · Why this closes Loops 7 and 9 together rather than splitting the difference

Loop 7 objected that an attendee gate is **circular**. Loop 9 objected that a
trailing gate is **misdirected**. A weaker resolution would have picked one. This
instrument answers both from a single property:

**The thing counted is the thing shown.**

- *Circularity* dissolves because events are supplied by the corner the
  below-threshold page recruits. A reader on that page can add one; they cannot
  conjure attendees for a map they are not being shown.
- *Misdirection* is impossible because the gate and the display read the **same
  window**. The card cannot open onto an empty map — not as a matter of tuning,
  but by construction.

The number is the least important part of the decision and should be recorded as
such. **5 could be wrong and the instrument would still be right.** If 5 proves
too low the symptom is a thin map and the remedy is one constant; if the
instrument were wrong, no value of N would fix it.

### 10.3 · LOW · Justification for 5 specifically

The below-threshold state is an **invitation**, not a punishment (§6.2b). The bar
to leave it should therefore be reachable by one committed organiser over a
season. A high bar would keep a corridor in the "asking for supply" state after
it has supply — which is the same class of dishonesty as showing an empty map,
pointed the other way. 5 is low deliberately, and the low side is the safe side
here: its failure mode is visible to the reader and cheap to correct.

### 10.4 · LOW · What the implementation carried that the doctrine did not

Two decisions were made in code and are recorded here so they are not mistaken
for accidents:

1. **The past edge is decided by `phase`, never by a date comparison.**
   `computeEventPhase` already accounts for `end_date` and `status`, so a
   multi-day event that began yesterday is still `event`. A `start >= now`
   filter would drop it from the map *while it is happening* — the exact
   reader-facing failure the map exists to avoid. A test substitutes the naive
   filter and asserts it goes red.
2. **Latching is not approximated.** §6.2b requires readiness to stay cleared
   once cleared. That is persistent state, and `isCorridorReady` deliberately
   answers only "is the bar met right now". The doc comment says so, because the
   tempting shortcut — widening the window until it feels sticky — would
   reintroduce a trailing component into a gate whose whole point is that it has
   none.

### 10.5 · Protocol amendment applied

The Loop 9.5 proposal is now in `skills/ccr-protocol.knowledge.md` §3.3.1 as two
anti-patterns and an admissibility table:

- **A citation to a comment, a doc, or a constant's name is not evidence of
  runtime behaviour.** A constant may be cited for its value, never for its
  meaning; its meaning lives in what reads it.
- **The asymmetry rule.** Contradicting the owner on their own domain requires
  *more* evidence than agreeing, because agreement gets checked by them and
  disagreement does not.

### Verdict on Loop 10: **PASS — the entry is complete**

The gate is settled, its constant exists with unit, grain, direction and purpose
stated at its definition, and the failure that produced Loop 9 has a mechanical
guard (a test asserting the two constants remain distinct) plus a protocol rule
against its cause.

**Confidence 96%** — restored, and on a different footing than Loop 8's 96%. That
score rested on an unread comment. This one rests on a query, a schema, an
executing constant, and 16 tests including a negative control.
