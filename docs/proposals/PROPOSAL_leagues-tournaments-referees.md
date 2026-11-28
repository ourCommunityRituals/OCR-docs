# PROPOSAL: Leagues, tournaments and referees

**Status:** decided. Matt approved D1 to D8 as recommended on 2026-11-27 (19:53 UTC, project thread). Phase 1 may start.
**Proposed:** 2026-11-27 · **Decided:** 2026-11-27 · **Owner:** Matt
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

## 1a. The headline outcome (Matt, 2026-11-27)

> The main part here is to have one shared report that sits as the parent company over all of their
> entities, so they can see all of the traffic, all of the reporting, and all of the sponsor traffic,
> and then be able to say: this is what we are capable of, and this is what our one company brings to
> the table from a corporate sponsorship market footprint.

Everything else in this proposal (leagues, referees, team pages, the spreadsheet mirror) feeds that one
report. For the practice brands it is a SharedReport for `lakeside-co` that covers every venture beneath
it: traffic on every code, every event and competition, and all sponsor traffic, with a footprint map.
The parent shares it with a corporate sponsor as one signed link.

It reuses what exists: the brand tree (OSE migration 0118, OSE-1532), the portfolio roll-up strip
(OSE `handlers/portfolio-rollup.ts`), the venue roll-up (OSE-2221), the SharedReport and its tiers, and
the map. Every venture's counts are floored on their own before they are added, so the total never
reveals a small venture. Sponsors appear only where both sides agreed. It shows traffic, never people.

**When:** it does not wait for leagues. It can be built now from traffic and sponsor data that exists
today (phase 0 in section 8), and competitions, results and referee records join it as their phases land.

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

### 7.1 How it works in a bocce league today (Matt, 2026-11-27)

Say there are three courts with four games on each. A referee rotates between courts by
availability, in half-hour slots. The referee shows up at their time, gets the game going, enforces
every rule and keeps score by hand.

What Matt wants:

1. **One referee site per league**, just for its referees. Every referee sees the schedule: which
   court, which half-hour slot, and when they are available.
2. **A community referee board.** A referee who will be late or cannot make a game posts it there and
   asks for cover; another referee picks it up.
3. **A photo as proof.** At the end of each game the referee takes a picture of the scoreboard and
   uploads it. The photo is stored (Cloudflare storage, with its record in D1) and is the record of
   what the score was.
4. **No admin work.** The score flows into the standings and the report automatically. The photos are
   the backup for any question or dispute, and they exist by the nature of what referees already do.

This matches Matt's NextUp vision of 2025-11-01 (`bereasonable13/robot-knowledge`,
`strategy/NEXTUP_COMPLETE_VISION.md`, "Phase 3: Referee System"), which was sized for an eight-court
tournament with eight referees.

### 7.2 An add-on, tied into the report (Matt, 2026-11-27)

Referees are an **add-on a league chooses** (OSE already has per-brand add-ons, migration 0121,
`lib/brand-addons.ts`). A league that does not take it enters scores itself. A league that does gets the
referee site, and everything the referees do is attached to that league's report: which referee covered
which court and slot, every score, cover requests, and the scoreboard photo behind each result. That
gives the league one record, and the **managing owner above it** (the parent brand in a brand tree, such
as `lakeside-co` over `lakeside-league`) can follow every venture's games from its roll-up.

The report section is private to the brand and its parent: referee names and photos never reach a
public page, a sponsor's view or OER. The public report shows scores and standings only.

### 7.3 How it fits the platform

- **Referees are league staff, not attendees.** The referee site is a private, brand-scoped area of
  ourSharedEvents, like the organizer's admin. Naming a referee there does not touch the anonymous side,
  which is about the public in the room. Nothing on it is public.
- **Schedule and availability.** Each fixture has a court and a half-hour slot. Referees mark when they
  are available and take slots; the organizer can assign. The board shows open slots and cover requests.
- **Cover requests** are posts on that board ("can't make 7:30 on court 2"). Taking one moves the slot
  to the new referee and is audited.
- **Score entry.** At the end of a game the referee enters the score and attaches the scoreboard photo
  from their phone. The result is confirmed at once by the referee's word, unless the ruleset asks both
  captains to confirm. Standings and the report update by themselves.
- **The photo.** Stored in the brand's own storage space, with a row in D1 that links it to the
  fixture. Seen only by the brand's organizers and referees, and the managing owner above the brand, never on a public page, never sent to
  ourWKRP or OER. A photo can catch people in frame, which is why it stays inside the league.
  It is kept for the season plus 90 days, then deleted; the score itself is kept (D9, Matt, 2026-11-27).
- **Reading the score from the photo** automatically is a later option. OSE's runtime stays free of
  model calls (OSE AGENTS.md), so it would need its own decision.
- **A per-sport kit** (in ourSharedGames) gives each sport its rules, its score screen (bocce frames
  and points, cornhole cancellation scoring, darts legs), common calls and a short training card. A new
  sport is a new kit, not new platform code.
- **Referees as people, on OW (opt-in).** A referee can plant a flag as an official: which sports,
  which leagues, how many seasons, and any certification a league grants. Leagues can find referees.

Scores are not counts of people, so a confirmed score can show at once. Whether the TV display shows a
live scoreboard is still Linear OSE-1635.

Note: OSE recorded on 2026-10-01 that drawing standings, schedules and brackets as tables would be a
separate product, not OSE (OSE `docs/brain/role-state/frontend-integration.md`, "League pane = links
out"). Matt's approval of this proposal on 2026-11-27 puts them in OSE; that older line is updated
when phase 1 lands.

D4 (approved): one Referee product, with a kit per sport.

## 7a. Mirroring a league's existing spreadsheet (Matt, 2026-11-27)

Many leagues already publish every schedule and result in a Google Sheet. It works, but it is
cumbersome to read. A league should be able to **keep its sheet** and let ourSharedEvents and ourWKRP be
the sleeker, configurable front end, in its own look.

- **One-way mirror.** OSE reads the league's sheet on a schedule and fills the same competitions,
  entries, fixtures and results tables as native entry. Nothing is ever written back to the sheet.
- **One source per competition.** A competition is either mirrored or entered natively, never both, so
  two sources cannot disagree. The page says where its results come from.
- **Column mapping, set once.** The organizer maps the sheet's columns (date, court, team A, team B,
  scores) when connecting it. A tab whose layout changes stops the mirror and tells the organizer rather
  than guessing.
- **Teams only on OSE.** A column of player names is never imported into OSE. Player stats, where a
  league wants them, go to ourWKRP by each player's opt-in (OW-223).
- **The league's look.** Once mirrored, the pages use the league's skin (ourAirwaves), the same as
  natively entered leagues.
- **Matt owns how the sheet is reached and logged**, working directly with each league. That detail
  is kept out of this public document.

This fits the existing "export first, integrate later" rule on the league epic (OSE-523, OSE-531): we
meet the league where its data already lives.

**Team formats and rule sets** (1v1 to 4v4, the 3v3 split, and the rules matrix) are in
`PROPOSAL_bocce-team-formats-and-rules.md`.

## 8. Phased plan

Each phase is useful on its own. Phase 1 is the smallest slice that helps a real bar league.

| Phase | What ships | Where | Linear |
|---|---|---|---|
| **0. One parent report** | A SharedReport for the parent brand over every venture: traffic, events, sponsor traffic, footprint map, shareable with a corporate sponsor. Built from today's data | OSE | new story |
| **1. Seasonal round robin** | A seasonal competition with one round-robin stage; entries as public labels; fixtures on existing league-night events; host enters scores; public standings page. Shown on the `lakeside-league` staging brand | OSE | OSE-525, OSE-526, OSE-527, OSE-529 |
| 1b. Mirror a spreadsheet | One-way mirror of a league's Google Sheet into the phase 1 tables, column mapping, one source per competition | OSE | new story |
| 2. Brackets and one-offs | Single elimination stage, playoffs after a season, one-off tournaments | OSE | OSE-530 |
| 3. Teams that carry over | OW team profile, roster, claim code, history across seasons | OW (+ small OSE claim route) | new OW story |
| 4. Referees | Referee site per league: schedule by court and half-hour slot, availability, cover board, score plus scoreboard photo, results straight into the report; bocce kit first | OSE, OSG | OSE-2239, OSG-10 |
| 5. More stage kinds | Pools, double elimination, Swiss, ladder, divisions | OSE | under OSE-523 |
| 6. Applied to ourSharedGames | Templates and rule packs as OSG data; bocce, cornhole, trivia first | OSG | new OSG story |
| 7. Self-serve | "Start a league" in ourAirwaves; board on the display (OSE-528) | OA, OSE | later |
| 8. Player stats | Per-person stats on OW, opt-in per event (OW-223) | OW | OW-223 |
| 9. Business intelligence | Season-over-season league and venue trends for the parent company through ourEventRings | OER | later |

**The first customer.** The Lakeside practice tree is the test bed: `lakeside-league` (seasonal bar
league across bar venues, with a playoff), `lakeside-semipro` (seasonal, needs referees),
`lakeside-club` (club league plus one-off tournaments), `lakeside-network` (a stream link per
fixture), and `lakeside-co` seeing every competition in its roll-up. Real names are loaded only
after the real groups agree (OSE-2218).

## 8a. The enterprise picture (Matt, 2026-11-27)

Every site in a sports company's family gets a front end built on OSE and OW. It either works beside the
company's existing website (plain link-back buttons; no embedding, per the 2026-11-26 decision for the
first customer) or stands alone as its own front end. Mapped onto the Lakeside practice brands:

| Layer | Lakeside brand | What people see |
|---|---|---|
| 1. A league site, one-stop shopping for every team | `lakeside-league` | Every team in one place: schedule, standings, results, the map of venues. Each team links to its own page |
| 1a. Each team, uniform yet unique | team profiles on OW | The league sets the frame (the required parts, laid out the same for every team); each team sets its own logo, colours and story inside that frame, through its skin |
| 2. The club | `lakeside-club` | The club's buckets: league nights, lessons, member nights, private events, tournaments, each an OSE event type on the same front end |
| 3. Each league | children of the club or the league brand | The same front end per league or division, so a player moves between them without learning a new site |
| 4. The parent company | `lakeside-co` | Its own tournaments, leagues and events, plus the roll-up of every venture and everything on the map |

How it is built with what exists:

- **Looks** come from the one skin format and ourAirwaves self-serve (PROPOSAL_ourAirwaves-self-serve.md):
  the parent can set a family look, each venture its own, and each team a team skin inside the league's
  frame. Only the abstraction carries across surfaces; layouts never do.
- **The map** is the existing OSE map (venues as H3 cells; ADR-033 and OCR ADR-013).
- **The roll-up** is the existing brand tree and venue roll-up (OSE migrations 0118 and 0120).
- **Business intelligence** is the long play: the same competitions and traffic feed ourEventRings
  through the existing OSE feed, at brand and venue grain, floored, never people. It is a later phase,
  not part of this build.

## 9. Decisions for Matt

All eight were approved as recommended (Matt, 2026-11-27). D7's tier split is approved as a shape; the numbers are still a first guess.

| # | Question | Decision |
|---|---|---|
| D1 | Is the split right: OSE runs competitions anonymously, OW holds teams and people by opt-in, OSG holds formats and rule packs? | Yes |
| D2 | What is "temporal" versus "seasonal"? | Seasonal repeats each year as a new edition; temporal is a one-time window (a six-week ladder) |
| D3 | Team names on the public OSE page: always public, or can a team choose a plain label ("Team 4")? | The team chooses its label; OSE-524 already says team names are public identities |
| D4 | Referees: one product with a kit per sport, or one product per sport? | One product, a kit per sport |
| D5 | Individual sports (singles darts, pickleball singles): an entry is a team of one with a chosen handle, and the real name shows only on OW if claimed? | Yes |
| D6 | Youth leagues: no OW team or person profiles for minors; youth play on OSE labels only | Yes, until a youth consent design exists |
| D7 | Which tier unlocks what? | Free: one competition at a time, round robin. Paid: seasons with playoffs, divisions, referee tools, more competitions. Anchor/Enterprise: brand-tree roll-up across ventures. Security and the floor are never tier-gated. First guess, awaiting Matt's numbers |
| D8 | Phase 1 first, on the `lakeside-league` staging brand? | Yes |
| D9 | How long is a scoreboard photo kept? (added 2026-11-27, after approval) | Decided (Matt, 2026-11-27): kept as the record for the season plus 90 days for disputes, organizers and referees only, then deleted; the score itself is kept |

## 10. Standing rules this design keeps

- OSE anonymous, OW named, the two databases never joined (ADR-010 in this repo).
- Never who, only how many; the under-5 floor for any count of people.
- Fan voting (for example, player of the night) stays in the room and at the Anchor level; this
  proposal adds no online voting.
- Mobile first: the score screen and standings must work one-handed on a phone at the court.
- Colours only from the hub tokens; brands look different through the skin, never new CSS.
- No real customer named on staging or in public until they agree.
