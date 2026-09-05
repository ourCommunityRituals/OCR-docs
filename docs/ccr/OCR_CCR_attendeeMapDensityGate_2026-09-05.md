# CCR — Attendee map & the density gate (proposed VISION amendment)

**Date:** 2026-09-05 · **Tier:** governance (5 loops, ≥95%) · **Verdict: HELD**
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
