# CCR — the choice network interpretation

**Date:** 2026-09-05
**Target:** the owner's interpretation, stated across this session —
publication as an **act** rather than a setting; three actor postures (private
citizen, business, government entity); and the claim that this is *"the
personification of the choice network."*
**Panel:** extended scrum team + **Director of Security** + **Community
Development Specialist**.
**Question asked:** does this interpretation have merit?

> **Verdict: PASS — the interpretation has strong merit and is load-bearing.**
> It resolves a hole in the invariant register that no one had named, it
> descends from real civic practice rather than from analogy, and it is
> already half-written in doctrine. Three findings are attached, one of them
> structural and worth acting on before the front end is built. None of them
> is a reason to reject the interpretation.

---

## What is actually being claimed

Three claims, and they should be judged separately because they are not equally
strong.

1. **Publication is an act, not a setting.** The bit lives on the *event*, not
   the *address*, so the same house can be private on Tuesday and a venue on
   Saturday.
2. **The posture differs by actor.** Private citizen → control is the point.
   Business → publication is *value* ("public record to show your public
   impact"). Government → publication is *obligation* ("their dedicated rule
   dictating how you need to make it public").
3. **This is the choice network personified** — the network is composed of
   choices, not of records.

---

## Loop 1 — Critical: what would break this?

### 1.1 · MERIT · The interpretation fills a hole the invariant register actually has

The prior CCR (`OCR_CCR_attendeeMapApproach_2026-09-05.md`, finding 1.5) found
that OCR has a **strong, well-enforced privacy commitment pointing at the
attendee and nothing pointing at the host.** Invariant #1 makes the customer
anonymous by construction. Invariants #5 and #25 govern the sponsor. The
Event/host corner had no equivalent.

That is why the map could ship a rigorous inbound coordinate refusal *and* a
street address in the response without anything feeling inconsistent — there was
nothing to violate.

The choice network is that corner's doctrine. Stated as the panel would state
it:

| Triangle corner | Its guarantee | Mechanism |
|---|---|---|
| **Customer** | anonymous by construction | Invariant #1, two-DB split, `ose_anon` |
| **Sponsor** | access is not purchasable | Invariants #5, #25 |
| **Event / host** | **presence is chosen, not assumed** | **`is_published`, per event** |

Three corners, three guarantees, one shape. That symmetry is not decoration —
it is the test of whether an interpretation belongs in this architecture, and
this one passes it.

### 1.2 · MERIT · "Cleared and listed" was already written and half-implemented

§6.2b: *"the surface shows what is **cleared and listed** across the clearance
lattice."* `legal_clearance_tier` implemented **cleared** (migration 0023).
Nothing implemented **listed**.

The three actor postures complete the lattice rather than adding to it:

- **Cleared** — what the *regime* requires or permits. Government: compelled.
  Regulated activity: conditional. This is the axis
  `OCR_STANDARD_declinedRegimes` already governs.
- **Listed** — what the *actor* chooses. Private citizen: default closed.
  Business: default open.

And the composition rule falls out on its own: **cleared overrides listed.** A
public body does not get to un-list a public meeting. That is not a rule anybody
had to invent for this design; it is what the two words already meant.

### 1.3 · MERIT · Community Development Specialist — the form is real, not analogised

This is the lens the owner asked for, and it is where the interpretation is
strongest.

The multi-stop, host-opts-in-per-stop event is not a hypothetical shape invented
to justify a flag. It is a **recognised civic form with many existing
instances**: porch-front music festivals, historic home and garden tours, open
studio / art walks, progressive dinners, neighbourhood run routes with open
houses. These share a precise structure:

- one organising body, **no venue of its own**
- N locations, each belonging to **a different resident**
- each resident **individually consents**, per occasion
- the roster is **published as the advertisement** — being on the list *is* the
  participation

That last point is the one the interpretation gets right and a privacy-framing
would get wrong. In these events **publication is the contribution.** A resident
who opens their porch is not tolerating exposure; they are giving something, and
the listing is how the gift is delivered.

**Asset-based community development** is the practice this sits in: the
neighbourhood's assets — homes, porches, gardens, people — are the venue, rather
than an institution's building. A platform that can only model institutional
venues cannot host this category at all. One that models per-occasion consent
can host all of it.

**Assessment: the interpretation has merit on its own terms and unlocks a
category the current data model cannot express.**

### 1.4 · HIGH · Community Development Specialist — the defaults create commercial drift

**This is the finding worth acting on.**

If private citizens default to unpublished and businesses default to published,
then over time **the map fills with commerce while civic and residential life
stays dark.** Not by anyone's intent — by the arithmetic of defaults.

The consequence is worse than a thin map, because it is self-reinforcing. The
below-threshold front door says *"fill this space so you can see the map."* If
the space that fills is commercial, the map teaches every subsequent reader that
this is a listings product for businesses, and the residential side never
recruits.

For a company named **OurCommunityRituals**, whose stated subject is community
gathering, a map that trends toward commercial listings is a mission failure
that would arrive quietly and look like growth.

**This does not invalidate the interpretation** — it is a consequence of the
defaults, not of the model. But it means the defaults need a counterweight, and
the counterweight is a product decision (Loop 3.1).

### 1.5 · HIGH · Director of Security — a publish is not reversible, and the UI must say so

Un-flipping does not un-send. Once a home address has been on a public map it
has been scraped, cached, screenshotted, and indexed. The flag protects the
*next* reader, never the ones who already looked.

Two consequences the design has to carry:

- **The asymmetry must be visible at the moment of choice.** Publishing and
  unpublishing are presented as one toggle, and they are not symmetric acts. The
  create flow must say what publishing means in plain language, once, before it
  happens.
- **"Just flip the flag" assumes the host can assess their own risk.** For many
  people that is fine. For someone living alone, someone with an ex, a family
  worried about immigration enforcement — publishing a home address is a
  materially different decision, and the platform is asking them to make it in
  one tap with no context.

The community development lens sharpens this rather than softening it: in
practice, porch-festival and home-tour organisers **brief their hosts**. The
consent is informed because a person explains it. A checkbox is not that, and
should not pretend to be.

### 1.6 · MEDIUM · Government compulsion can collide with residential privacy

A government entity is compelled to publish. But a government event can be *at a
private residence* — a ward meeting in a living room, and in some jurisdictions
**polling places are literally private garages**.

When the compelled-public actor meets the private-citizen location, the two
postures point in opposite directions and the model as stated has no
tie-breaker. This is genuinely thorny and is **not blocking** — it is rare, and
it needs a policy answer rather than a schema answer.

### 1.7 · MEDIUM · Director of Security — mandated retention collides with Invariant #8

Invariant #8 is **bounded PII retention**: every opt-in PII column has a TTL and
a daily lifecycle job deletes on schedule.

Public-records law frequently mandates the opposite — **retain**. A government
entity's registration list may be a public record that must be preserved for a
statutory period, while the platform's lifecycle cron is deleting it.

Invariant #8 and the government posture can therefore issue contradictory
instructions about the same rows. Neither is wrong; they belong to different
regimes. This needs an explicit answer before any government entity is
onboarded, and it should be filed now rather than discovered then.

### 1.8 · LOW · "Public impact" creates an incentive on the numbers

A business wanting its results as public record is legitimate, and it is the
honest reason SharedReports exist. But once a report is *marketing*, there is
pressure on what it says. Invariant #7 (aggregate-only) and the min-sample
suppression already limit the surface; worth naming that this posture is what
makes those guards load-bearing rather than theoretical.

---

## Loop 2 — Conservative: what is the smallest version that still ships value?

### 2.1 · **KEEP** · The binary flag, exactly as specified

Owner set it binary and rejected a third "listed but located coarsely" state.
That was the right call and should not be reopened: the third state is where
this design would acquire a permissions matrix, and the two-state version
already expresses every case the panel could name — including the historical
home, which was the hard one.

### 2.2 · **DEFER** · The second axis (results as public record)

*"Business owners want the results to be public record"* implies a second bit —
presence on the map, and outcomes in the record — with defaults inverted by
actor. **This is real and should not be built yet.** Nothing consumes it, and
SharedReports are already aggregate-only and link-gated, so the exposure is
bounded today. Build it when a business asks for a public report URL.

Record the *shape* now so it is not re-derived: same mechanism, inverted
defaults, per-actor.

### 2.3 · **DEFER** · Actor-type as a schema concept

The three postures are real, but the platform has no `actor_type` and does not
need one to ship the flag. Defaults can be a create-flow question long before
they are a column. Adding the column first would invite a permissions model
nobody has specified.

### 2.4 · **CUT** · Any attempt to infer residential-vs-commercial automatically

Tempting (geocode class, address shape, venue-name heuristics) and wrong. It
would be inaccurate, unaccountable, and would quietly re-introduce the static
classification this interpretation correctly replaced. **The host answers.**

---

## Loop 3 — Recursive: what does this imply that we haven't done?

### 3.1 · **REQUIRED** · Give the residential side a counterweight to commercial drift (1.4)

Options the panel would put to the owner, cheapest first:

- **Ask everyone, default nothing.** Publication is a required answer at
  creation rather than an inherited default. Removes the arithmetic entirely,
  costs one screen.
- **Rank civic and residential above commercial** on the map when both are
  present, rather than by recency alone.
- **Treat the multi-stop event as the recruiting instrument.** A house walk
  publishes twelve residents at once and each one has been briefed by an
  organiser. This is the strongest answer, because it is the form that already
  solves the informed-consent problem in 1.5.

### 3.2 · **REQUIRED** · Multi-stop events are a new entity shape — file it

`event_series` (migration 0033) groups events **across time**. There is **no
spatial grouping**. `venue_id` (migration 0031) means "anchor event for
return-rate tracking", not "stop on a route".

An art walk is one event, N stops, N hosts, N independent consents. That is new,
and it needs:

- **per-stop consent, held by that stop's host** — in a twelve-stop walk the
  organiser is not the host of eleven locations. If the flag is event-level and
  the organiser owns the event, **the organiser can publish eleven people's home
  addresses.** This is the single most important implementation constraint in
  the whole interpretation.
- an NCR fit that is already right: each open house is a **Node** (res 9,
  ~201 m), the walk is a **Corridor** (res 7, ~1,406 m). The map draws a route,
  not a pin. This is the first product use of res 9 as a *display* concept.
- a strong sponsor shape: twelve stops = twelve poster locations, twelve QR
  codes, one corridor, one local sponsor.

### 3.3 · **REQUIRED** · Publication must expire with the event

A house published for one Saturday must stop being published after. This
composes free with the map (forward window only) but **not** with the list,
which deliberately shows `post_event` recaps. A home event's recap must drop the
address while a venue event's keeps it.

### 3.4 · **REQUIRED** · File the Invariant #8 / mandated-retention collision (1.7)

Before any government entity is onboarded, not after.

### 3.5 · **RECOMMENDED** · `is_published` must not be freely settable for a compelled actor

If cleared overrides listed, then a government entity's event cannot be
unpublished by a user action. The column is currently a free toggle. This is not
a bug today — there are no government tenants — but it is the shape the
governed-flag needs, and it should be written down before someone builds a
settings screen.

### 3.6 · **NICE-TO-HAVE** · Name the pattern in the design language

The owner's designs keep taking one shape: **the same mechanism, read in
opposite directions depending on who is standing there.** The landing-card
inversion (supply below the threshold, demand above it). The flag (protective
for a resident, generative for a house walk). The postures (choice for a
citizen, value for a business, obligation for a government). That is a
consistent authorial style and naming it would make future decisions faster to
reach.

---

## Synthesis

### Verdict: **PASS** — the interpretation has merit and should be adopted as doctrine

It descends from real civic practice, it completes a lattice that was already
half-written, and it gives the Event corner the guarantee the other two Triangle
corners already had. The panel found nothing that argues against adopting it.

### Top three findings

1. **1.4 — commercial drift.** Defaults alone will fill the map with commerce
   and leave residential life dark, in a product whose subject is community
   gathering. Needs a counterweight (3.1) before the front end is built.
2. **3.2 — per-stop consent.** In a multi-stop event the organiser must not be
   able to publish other people's homes. This is the constraint most likely to
   be got wrong by whoever implements the house walk quickly.
3. **1.5 — a publish is irreversible.** The toggle is symmetric; the act is not.
   The create flow has to say so once, in plain language, before it happens.

### What has merit, stated plainly for the record

- **Publication as an act, not a setting** — correct, and the reason the
  historical-home case works at all.
- **The three postures** — real, and they complete "cleared and listed" rather
  than adding a parallel concept.
- **"The personification of the choice network"** — accurate. The network is
  composed of per-occasion consents, and the map is not a database view but
  **the visible surface of everyone who said yes today.** That is a materially
  different thing to build, and it is the better one.

**Confidence: 96%.** The residual is 1.6 (compelled-public at a private
residence), which is a policy question with no technical answer and no near-term
forcing function.
