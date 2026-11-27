# PROPOSAL: Leagues, tournaments and referees

**Status:** proposed. Design only. No feature code until Matt says yes to the decisions in section 9.
**Proposed:** 2026-11-27 · **Owner:** Matt
**Lives in** `docs/proposals/`, so it does not propagate to spokes.
**Builds on:** OSE epic OSE-523 (League & Tournament Container) and its children OSE-524 to OSE-531,
which this proposal widens rather than replaces.

## 1. What Matt asked for

Matt, 2026-11-27 (lightly edited from voice):

> Starting in ourSharedEvents and the ourWKRP instance. It would live in that base, which then
> would be applied to ourSharedGames, because that is where it would ideally be applied. I want
> leagues, referees and tournaments with full support. League management for any kind of sports
> league, modeled after the events (the OSE event types) but geared to sports, with the option of
> a league, one-off, temporal or seasonal, and the different combinations of tournaments for the
> different leagues. Then OW lets teams and people carry through and be associated from league to
> league, season to season, year to year. Referees: there would be an entire product, for whatever
> type of game requires its own kind of in-house referee, with the ability to referee that game.

And: the model customer is a bocce company running its different ventures as spokes, which already
exists as a practice brand tree on staging under the stand-in name **Lakeside**.

## 2. What exists today (checked 2026-11-27)

| Piece | Where | What it gives us |
|---|---|---|
| Event types with a sports category | OSE `event_type_registry` (category `REC`, "Sports & Recreation"); brain `event-taxonomy.yaml` has `bocce_league`, `bocce_tournament`, `bowling_league`, `recreational_league` (takes one sport from the activities list), `youth_league` | A league night is already an event of a sports type |
| Declared series | OSE ADR-029, `lib/event-series.ts` (weekly, biweekly, monthly, daily-weekdays, as-announced) | A season's nights can already be grouped |
| Team ids | OSE ADR-040: a team is an opaque `grp_` id, used for team-night voting | The same id shape can name a league entry |
| Brand tree and venues | OSE migrations 0118, 0120; `lib/brand-tree.ts`; staging fixture `bruno/fixtures/lakeside-brand-tree-seed.sql` | A parent company sees all its ventures; a venue rolls up every venture that plays there |
| Practice bocce family | `stg.oursharedevents.com/demo/bocce` (OSE-2219): `lakeside-co`, `-club`, `-semipro`, `-league`, `-network` | The first customer to design for |
| Named profiles | ourWKRP `profile_type` (`artist`, `sports`; migration 0014), flag facets (migration 0009), opt-in to be voted on (0015) | People plant a flag; no team concept yet |
| Bocce format | ourSharedGames `docs/corridors/OCR_REFERENCE_chicagoBocce.md` | League night arc and how it maps to OSE |
| League epic | Linear OSE-523 and children OSE-524 to OSE-531 | Doctrine already set: team-level standings, team names are public, player names off by default, round robin plus manual override, export first |

Nothing today stores a fixture, a score, a bracket or a standings table. That is the gap.

## 3. The shape in one picture

```text
          ourSharedGames (formats: how a bocce league night or a cornhole bracket is run)
                                  │  templates and rule packs
                                  ▼
 ourSharedEvents (anonymous)                        ourWKRP (named, opt-in)
 ─────────────────────────                          ──────────────────────
 Competition (league / one-off / temporal / seasonal)    Team profile (persists for years)
   └ Stage (round robin, bracket, pools, ladder...)        └ roster: people who chose to join
       └ Fixture (a match, on an OSE event night)          └ history: entries it has claimed
           └ Result (score, entered by host or referee)  Person profile (sports type, flags)
   └ Entry (an opaque team slot with a public label)       └ teams they chose to show
                     ▲                                               │
                     └──────── claim code (one-way, by consent) ─────┘
```

The rule underneath: **OSE runs the competition and never knows who is in it. OW remembers who
played, only for those who choose to plant a flag.** A team can play a whole season without ever
touching OW.

## 4. Formats Matt named, and how they combine

A **competition** is the new thing a brand creates, beside its events. It has one format:

| Format | Plain meaning | Example (Lakeside) |
|---|---|---|
| **League** | Ongoing, no end date. Standings roll. | Club league night every Wednesday |
| **Seasonal** | Fixed start and end, and it comes back as a new edition each year | Fall bar league, Sept to Nov; Spring league next year |
| **Temporal** | A fixed window that is not a season and does not repeat by itself | A six-week summer ladder |
| **One-off** | A single day or weekend | Holiday tournament |

(My reading of "temporal" versus "seasonal" is a guess: see decision D2.)

A competition has one or more **stages**, run in order. A stage is one of: round robin, pools,
single elimination, double elimination, Swiss, ladder. Combinations are just stages in a row:

- Seasonal league → playoff bracket at the end (round robin, then single elimination).
- One-off tournament → pool play in the morning, bracket in the afternoon.
- League with divisions, top two from each division into a championship.

A competition may also have **divisions** (skill or region) and links to an OSE **series** (ADR-029),
so the nights it is played on are the series' events. Every fixture sits on an OSE event, so
posters, codes, sponsors, the map and the SharedReport all work as they do today.

## 5. Data model (first draft)

### 5.1 ourSharedEvents, in `DB` (the anonymous side)

| Table | Holds | Never holds |
|---|---|---|
| `competitions` | brand, sport (event type), name, format, status, start and end, series link, venue, ruleset | anyone's name |
| `competition_stages` | competition, kind, order, how teams advance | |
| `competition_divisions` | competition, label | |
| `competition_entries` | `grp_` id, competition, division, **public label** the team chose, seed, status | roster, captain, contact |
| `fixtures` | stage, OSE event, round, court or table code, entry A, entry B, scheduled time, status | |
| `fixture_results` | fixture, score A, score B, outcome, state (provisional, confirmed, disputed, final), entered-by actor | who watched |

- **Standings are computed**, never stored (OSE-525 already said so).
- **Scores are not counts of people,** so the under-5 floor does not apply to them. Anything that
  counts people (scans, check-ins, votes) keeps the floor and stays post-event.
- **An entry id uses the `grp_` shape** of ADR-040, so a team-night vote and a league entry can be
  the same team without a new id.
- Any captain contact that must exist stays in `FORMS_DB`, referenced by opaque id (OSE-525).
- A **ruleset** names the sport's scoring: what a win is, points for win, draw and loss, and the
  tiebreak order. First version: a small list in OSE code. Later it moves to ourSharedGames as data
  (section 6).

### 5.2 ourWKRP (the named side, all opt-in)

| Addition | Holds |
|---|---|
| `team` profile type | A team page with a slug, logo and colours inside the base skin, like any OW profile |
| Team roster | People who asked to join and were accepted by a team admin. Leaving is one tap |
| Team history | The OSE entries this team has claimed, so its page shows every league, season and year |
| Person history | The teams a person chose to show on their own profile |

**The claim code.** When a team enters an OSE competition, the organizer can hand its captain a
short claim code. The captain enters it on the team's OW page. OW then stores "this team is entry
`grp_…` in that competition" and reads its public results. OSE never learns which OW team claimed
the entry: it only marks the code used. Next season, a new entry is claimed onto the same OW team,
and the history carries on. This is the "carry from league to league, season to season, year to
year" Matt asked for, without OSE ever holding a name.

### 5.3 New data links (added to `data-edges.yaml` only when built)

- OW → OSE: redeem a claim code (sends the code, gets back an entry id). Class A.
- OSE → OW: public read of a competition's fixtures, results and standings by entry id. Public class,
  the same as what the public page shows.

## 6. How the three repos split the work

| Repo | Owns |
|---|---|
| **ourSharedEvents** | Competitions, stages, entries, fixtures, results, standings; the organizer screens; the public schedule and standings page; the display board; the referee role and score screen |
| **ourWKRP** | Team profiles, rosters, team and person history across years; the claim code redemption |
| **ourSharedGames** | The formats: ready-made competition templates (bocce league night, cornhole bracket, trivia season, darts ladder) and per-sport rule packs. This is where it is "applied". OSG stays docs-as-code: templates are data files OSE reads, the same way UEC codes come from the brain |
| ourAirwaves | Later: "start a league" as a self-serve action, calling OSE's API. Looks only, as today |
| ourSharedMagnets | Later: the organizer runbook and Bruno collections for leagues |
| ourEventRings | No change: results reach it through the existing OSE feed, at brand and venue grain |

## 7. Referees

Matt's idea: a product for each game that needs its own in-house referee, so people can referee it.

Proposed shape, in three layers:

1. **Referee role in OSE (shared by every sport).** An organizer assigns a fixture, a court or a whole
   night to a referee with a short-lived referee code. Holding the code lets a phone enter and confirm
   scores for those fixtures only, nothing else. Every entry is audited. A referee never needs an OW
   account. The ruleset says whose word is final (the referee's, or both captains').
2. **A per-sport referee kit** (lives with the format in ourSharedGames). The rules, the score screen
   layout (bocce frames and points, cornhole cancellation scoring, darts legs), common calls, and a
   short training card. A new sport is a new kit, not new platform code.
3. **Referees as people, on OW (opt-in).** A referee can plant a flag as an official: which sports,
   which leagues, how many seasons, and any certification a league grants. Leagues can find referees.

Decision D4 asks whether this is one "Referee" product with a kit per sport (my recommendation:
the kits share most of their machinery) or a separate product per sport, as Matt described it.

## 8. Phased plan

Each phase is useful on its own. Phase 1 is the smallest slice that helps a real bar league.

| Phase | What ships | Where | Linear |
|---|---|---|---|
| **1. Seasonal round robin** | A seasonal competition with one round-robin stage; entries as public labels; fixtures on existing league-night events; host enters scores; public standings page. Shown on the `lakeside-league` staging brand | OSE | OSE-525, OSE-526, OSE-527, OSE-529 |
| 2. Brackets and one-offs | Single elimination stage, playoffs after a season, one-off tournaments | OSE | OSE-530 |
| 3. Teams that carry over | OW team profile, roster, claim code, history across seasons | OW (+ small OSE claim route) | new OW story |
| 4. Referees | Referee code and score screen in OSE; bocce kit first | OSE, OSG | new stories |
| 5. More stage kinds | Pools, double elimination, Swiss, ladder, divisions | OSE | under OSE-523 |
| 6. Applied to ourSharedGames | Templates and rule packs as OSG data; bocce, cornhole, trivia first | OSG | new OSG story |
| 7. Self-serve | "Start a league" in ourAirwaves; board on the display (OSE-528) | OA, OSE | later |
| 8. Player stats | Per-person stats on OW, opt-in per event (OW-223) | OW | OW-223 |

**The first customer.** The Lakeside practice tree is the test bed: `lakeside-league` (seasonal bar
league across bar venues, with a playoff), `lakeside-semipro` (seasonal, needs referees),
`lakeside-club` (club league plus one-off tournaments), `lakeside-network` (a stream link per
fixture), and `lakeside-co` seeing every competition in its roll-up. Real names are loaded only
after the real groups agree (OSE-2218).

## 9. Decisions for Matt

| # | Question | Recommendation |
|---|---|---|
| D1 | Is the split right: OSE runs competitions anonymously, OW holds teams and people by opt-in, OSG holds formats and rule packs? | Yes |
| D2 | What is "temporal" versus "seasonal"? | Seasonal repeats each year as a new edition; temporal is a one-time window (a six-week ladder) |
| D3 | Team names on the public OSE page: always public, or can a team choose a plain label ("Team 4")? | The team chooses its label; OSE-524 already says team names are public identities |
| D4 | Referees: one product with a kit per sport, or one product per sport? | One product, a kit per sport |
| D5 | Individual sports (singles darts, pickleball singles): an entry is a team of one with a chosen handle, and the real name shows only on OW if claimed? | Yes |
| D6 | Youth leagues: no OW team or person profiles for minors; youth play on OSE labels only | Yes, until a youth consent design exists |
| D7 | Which tier unlocks what? | Free: one competition at a time, round robin. Paid: seasons with playoffs, divisions, referee tools, more competitions. Anchor/Enterprise: brand-tree roll-up across ventures. Security and the floor are never tier-gated. First guess, awaiting Matt's numbers |
| D8 | Phase 1 first, on the `lakeside-league` staging brand? | Yes |

## 10. Standing rules this design keeps

- OSE anonymous, OW named, the two databases never joined (ADR-010 in this repo).
- Never who, only how many; the under-5 floor for any count of people.
- Fan voting (for example, player of the night) stays in the room and at the Anchor level; this
  proposal adds no online voting.
- Mobile first: the score screen and standings must work one-handed on a phone at the court.
- Colours only from the hub tokens; brands look different through the skin, never new CSS.
- No real customer named on staging or in public until they agree.
