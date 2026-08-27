# OSE / OW Hybrid — Design Brief

A community events-and-culture platform in two products that share one architecture.
This brief reflects the system as it exists in code and settled decisions (2026-08-26)
— not aspiration. Where something is designed-but-unbuilt, it says so.

---

## 1. The one-sentence thesis

**Never who, only how many.** The platform gives a community real data about its own
culture — events, music, art, commerce — without ever tracking an individual who
didn't explicitly choose to be named. Attendees get three choices at every event:
**don't interact · interact anonymously · put your name on it, on your own terms.**

## 2. The two products (one contract, two poles)

- **OurSharedEvents (OSE)** — the event engine and the **anonymous pole**. Events,
  QR scan ingestion, sponsors, posters, and the SharedReport. An attendee at an OSE
  event is a headcount, never a name. Scans store hour-granularity only — no exact
  timestamps, no IPs, hashed non-reversible agent fingerprints.
- **ourWKRP (OW)** — the music/arts catalog and the **named pole**. Contributors,
  curators, DJs, and artists *choose* attribution: their name on what they bring is
  the product. Listeners inside OW remain counts.
- **The hybrid:** OW runs the same screen architecture as OSE; the only sanctioned
  difference between them is how each interprets the shared invariant constitution
  (a central registry of numbered architectural rules, CI-enforced per repo).
  When data crosses from OW to OSE or to a sponsor, listener identity never
  crosses — aggregates only, stripped and floored *before* the boundary.

**Roles ladder (OW), a 5-rung consent ladder — anonymity fades to named as you climb
by choice:** 1 Listener (anonymous by default, zero account) · 2 Contributor (named,
consented — connects their library) · 3 Curator (named, attributed — builds shelves)
· 4 DJ/Artist (named, published — every set documented, "no more creditless night")
· 5 Crew (named, operational).

## 3. The five surfaces (all exist in OSE)

Every event is delivered through five surfaces. OSE renders; for hybrid events the
surfaces **pull from OW**, which is the sole system of record for attribution.

1. **Poster** — printed, durable, per-placement QR codes (`poster_deployments`: one
   row per poster / table / booth / piece, with a human label like "Table 4").
2. **Admin** — organizer's operational view. First-party data is legitimately exact
   here (an organizer must be able to run their own event).
3. **Display** — the TV / venue screen. Unlike a poster it can *change*, so it is
   the only legitimate home for rotating codes (now-playing, vote keys).
4. **Public** — the event's public page: the **five W's** (Who/What/When/Where/Why —
   who_story is "the WHO conversion engine"), hero image, trailer video link,
   outbound links that visibly declare where they go ("opens YouTube", "opens Stripe").
5. **SharedReport** — where everything resolves. See §7.

## 4. Attribution: three shapes, open vocabulary

Artist *type* is vocabulary (data, cheap to add). Attribution *shape* is schema
(three, closed):

| Shape | A scan resolves to | Types |
|---|---|---|
| time-indexed | the unit playing now (playback event) | DJ, band |
| session-indexed | the bounded session itself | theater, talk, workshop |
| object-indexed | a specific physical thing | sculpture, print, art-fair table, market booth |

Object-indexed is fully built (per-placement posters + scans + floored report).
Session-indexed needs no new attribution code. Time-indexed awaits a
`playback_events` table; its law is settled: **the code carries the unit id — a
scan never resolves by timestamp** (the scan path stores hour-buckets only, by
privacy invariant). "New song, new code" = rotating logical key on the Display
screen; the wall poster never changes.

## 5. QR codes: UEC (Universal Event Code)

A color-semantic code standard — **the color IS the instruction** — but UEC is a
*URL contract*, not a QR concept: shortlinks, posters, and deep links all carry it.

- 11 codes exist; the working core is being condensed. **LIVE was demoted from core**
  (nothing implements it; print is the wrong channel for content that exists four
  hours a month — live surfaces ride the Display screen or the entry session).
- **Color can never be the sole carrier.** Measured finding: the palette cannot make
  five codes CVD-distinguishable (worst pairs ΔE ≈ 9–13 under deuteranopia where
  ~20 is needed). Therefore every code carries a non-color channel: a plain WORD
  ("VOTE", "HELP"), a readable shortlink path (/live, /enter), and a tier label.
  Accessibility is architectural, not polish.
- Consent tiers on codes: **untracked** (HELP — keeps nothing) · **anonymous**
  (LIVE/vote, ARCHIVE — counts only) · **identified** (ENTER registration,
  FEEDBACK — you choose to leave a way back). The poster says which, in words.

## 6. Discovery — "What's on" (designed, not built)

The attendee's front door, before any scan: a map + week-list of published events
for a picked area. Three rules baked in: it is a **second map** built from published
listings (never scan data — nothing to protect, so browsing is anonymous *by
construction*, no account); the area is **picked, never detected** (no location
permission, ever); outbound links **say where they go**. Cold-start honesty: a
corridor with two listings shows "not enough yet" and routes to the nearest active
corridor rather than drawing a map of two things.

Deployment reality: **southwest Michigan is the live OSE rollout** (New Buffalo,
Sawyer, St Joseph, Three Rivers, Kalamazoo — bocce + cabin/venue occupancy +
partner funneling). Blue Island / Western Ave is the OW home corridor. Bronzeville
(white-label "Bronzeville's ourWKRP") and Oak Park are planned relationships,
designed at target state. White-label rule: **the chrome changes, the scan codes
never do** — UEC hues are theme-invariant.

## 7. The SharedReport — where everything resolves

Every shape, every discipline, every surface funnels into one artifact read the
next morning by three audiences: organizer, sponsor, talent. Its laws (all
CI-enforced in code today):

- **Uniform count floor (K=5), server-side.** Any listener-derived count below 5
  is *held* — sub-floor rows are dropped entirely (a present-but-suppressed row
  still says "a small cohort was here"), and totals are sums of *surviving*
  buckets so a total can never be differenced against the rows beside it. The
  floor is declared in the payload so clients never hardcode it.
- **Honesty lexicon.** Banned vocabulary that claims people when the system counts
  signals: attendance, impression(s), visit(s), reach, unique, turnout, eyeballs,
  people, view(s). Honest replacements name the measurement: *displays* (an ad
  rendered), *distinct listeners*, *draw*, *nods*, *distinct signals*. Marketing
  translation is allowed only downward: a term may never claim more than the count
  supports ("top third of placements" — checkable; "strong reach" — banned).
- **Counted vs claimed, visually distinct.** Counted stages (platform saw it):
  solid bars. Claimed stages (artist reported it): dashed outline + "claimed" chip,
  "prints with your name on the claim, never with ours."
- **The quiet night is a first-class state.** "Numbers held" — with the reason
  (numbers small enough to point at a person), the reassurance (they join season
  totals), and three concrete suggestions (move tables, bigger card, earlier
  block). The season is the story, not one Friday.
- Report primitives that exist: distinct signals, return share, corridor activity
  vs 30/90-day baselines (like-for-like by day-of-week × hour), per-placement
  draw, sponsor displays by class (local/mid/premium), night-over-night series.

## 8. Sponsors — the hyperlocal ad economy

- **Share covenant:** money buys rotation frequency and report depth ONLY — never
  size, slot, position, or local status. Every sponsor renders identically. Local
  businesses (geo-derived, corridor-cell match — never purchasable) hold a
  guaranteed rotation floor and can't be outbid for prominence.
- **Two-sided acceptance (built):** either party may initiate a placement
  (organizer adds a business, or a business subscribes to an event template +
  area); the other side must accept. Null = not answered (doesn't hide);
  rejection is the operative act and is durable — a declined match is never
  re-proposed. This is what lets matching be generous.
- The report answers the sponsor's real question honestly, including "are local
  organic advertisers out-performing paid spend?"

## 9. Commerce — Stripe as pure pass-through

The platform is a conduit, never a custodian — for identity AND money. An artist
pastes their own Stripe payment link into their public page; buyers go straight to
the artist's Stripe; the platform never sees buyer or funds. The report's Sales
stage is therefore **dormant** (dashed, "not counted yet") until the artist either
self-reports (labelled *claimed*) or connects Stripe zero-fee ("keep 100%"), after
which sales arrive as a count — never the buyer. Artists accumulate their own
merchant history: graduating from the corridor doesn't mean starting over.

## 10. Fist of Five — the tourney format (designed, not built)

Not a discipline; a competition format on the substrate. Persistent teams
(wrestling-style stables) compete monthly on a shared playlist; the room votes by
QR — one tap, +1 for the now-playing song, anonymous; votes roll up to the team;
winner holds **the belt**; season standings across monthly cards. A second
open-challenge belt (**Triple A** — Anyone, Anywhere, Anytime, 1v1) keeps it live
between cards and rides mobile-link voting. The night carries both poles at once:
competing teams identified, voting room anonymous. Results surface through the
SharedReport (aggregates by nature). Generalizes to battle-of-the-bands or
audience-choice one-act series by changing the taxonomy row, not the engine.

## 11. Design language

- **Mobile-first, 390px, dark default.** OW brand identity: amber-on-black; OSE:
  navy/blue system. Brand affects chrome only — UEC hues never re-theme.
- **Copy is load-bearing and plain.** The privacy promise is stated as fact where
  it applies, in situ: "no account · nothing stored" · "You picked this area. We
  didn't look." · "We count the room, never the person." · "The act of choosing is
  the consent." Legal-ese never appears on an attendee surface.
- **Honest at any density** — empty and quiet states are designed first (they are
  the common case): day-one corridors, below-floor nights, dormant stages.
- **Structure encodes truth:** solid = counted, dashed = claimed/dormant/planned,
  held = suppressed-with-reason. Status chips distinguish live / rollout /
  planned. Nothing on any surface may overclaim — the platform's market position
  is that it *underclaims by construction*, and that is the brand.
- **Accessibility floor:** WCAG AA contrast on all scan colors, pairwise CVD
  separation checked computationally, word + path + tier on every code, 44px+
  touch targets, one-tap flows (a vote is one tap; a scan is the only gesture).

## 12. Build status legend (for honest mockups)

| Built & enforced | Designed, not built | Planned |
|---|---|---|
| Five surfaces, per-placement scans, count floor, lexicon lint, boundary strip, sponsor covenant + two-sided acceptance, five-W's pages, floored OW sponsor report | What's-on discovery, artist ledger UI, consent-tier field on codes, playback_events, FOF engine | Bronzeville & Oak Park corridors, OurAirwaves artist site builder, Stripe Connect counting |
