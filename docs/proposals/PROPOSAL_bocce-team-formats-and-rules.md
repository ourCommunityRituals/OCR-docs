# PROPOSAL: Bocce team formats and rule sets

**Status:** proposed, first pass. A follow-up to `PROPOSAL_leagues-tournaments-referees.md` (decided 2026-11-27).
**Proposed:** 2026-11-27 · **Owner:** Matt
**Lives in** `docs/proposals/`, so it does not propagate to spokes. The rule data itself will live in
ourSharedGames as the bocce kit (Linear OSG-10).

## 1. What Matt asked for

Matt, 2026-11-27 (lightly edited from voice):

> For tournament support I want 1v1, 2v2, 3v3 and 4v4. In bocce a team of three plays two at one end
> and one player at the other, so it is essentially 3 versus 3. All the combinations must be supported.
> Research every iteration of the rules, from the top national body down: the United States, Canadian,
> South American and international rules, then the regional and little-league rules. The bocce map
> site is a good source of the facilities and the different rule sets.

## 2. Team formats

| Format | Players a side | Balls a side | Where players stand | Source |
|---|---|---|---|---|
| 1v1 (singles) | 1 | 4 (4 each) | Walks end to end | USBF Open, CBI Art. 4 A, BSA, Special Olympics |
| 2v2 (doubles) | 2 | 4 (2 each) | Both walk end to end, **or** one at each end with 4 balls each | USBF Open, CBI, BSA |
| 3v3 (triples) | 3 | 4 (split 2 + 1) or 6 (2 each) | **Split:** two at one end throw 2 each, one at the other end throws 4 (BSA, Matt's description). **Walk:** all three walk, 2 each, 12 balls on court (USBF Open, CBI) | BSA, USBF Open, CBI |
| 3v3, walker | 3 | 4 (short-handed players throw 3) | One player at each end, and a **walker** who plays both ends; the walker must change from game to game | Members' club league rules, 2025 |
| 4v4 (fours) | 4 | 8 (2 each) or 4 (1 each) | Two at each end, may not switch ends (USBF Open, BSA); Special Olympics teams throw 1 ball each | USBF Open, BSA, Special Olympics |
| 5-player | 5 | 8 scoring + 1 coach ball | A coach throws a fifth ball that cannot score | bocce.org "Official Rules" (publisher not named) |

**What the platform stores.** A team entry has a size (1 to 4, 5 only where a rule set allows it).
Each frame has a **lineup**: which player position stands at which end and how many balls it throws.
The rule set checks that a side's balls add up (4, 6 or 8) and whether positions may switch ends. On
OSE these are positions (A, B, C, D), never names; a name appears only on ourWKRP if the player chose it.

## 3. Rule sets found (top down)

| Level | Rule set | Read? |
|---|---|---|
| National, US | **United States Bocce Federation (USBF) Open Rules**, updated 2023-03-23; used at USBF national championships and recommended for all leagues | Yes |
| International | **CBI (Confederazione Boccistica Internazionale) International Technical Rules**, punto raffa volo, in force since 2019, amended 2023 and 2024; USBF publishes the English version | Yes |
| National league standard, US | **Bocce Standards Association (BSA)** rules, as described by a court builder that points to boccestandardsassociation.org | Secondhand |
| Adaptive | **Special Olympics Bocce Sport Rules**, 2024, including Unified (athletes with partners) | Yes |
| Unattributed | "The Official Rules of Bocce" (bocce.org, 2020): 4-player teams, 5-player coach variant, to 9 | Yes, publisher unknown |
| Regional, South America | Venezuelan **bolas criollas** (2v2, 8 balls a side, to 20, steel "mingo") | Yes, from an encyclopedia summary |
| League, members' club | A bocce club's official league rules (2025): 4-player teams, 3-game series, walker rule, position weeks | Yes |
| League, Chicago social | A Chicago sport-and-social league's bocce rules (2023): 4v4, games to 11, refers to USBF Open as the official rules | Yes |
| **First customer's house rules** | Its own league and tournament rules | **Not yet: its league site blocks automated reading (Q2)** |
| Not yet read | Canadian rules; the **South American confederation's** bochas rules; **FIB** volo; Brazilian bocha; Italian league variants; the regional and league house rules on the bocce map | See section 6 |

Note: Matt named an "American Bocce Association" as the top US body. The national body found is the
**United States Bocce Federation**; no "American Bocce Association" rulebook turned up. Question Q1.

## 4. The rules matrix

Each row is a setting the tournament engine lets an organizer choose per competition. Cells show what
each rule set says; a blank means the rule set does not say.

| Setting | USBF Open | CBI international | BSA league | Special Olympics | bocce.org | Members' club | Chicago social |
|---|---|---|---|---|---|---|---|
| Points to win | 12; finals 15; director may set other | 12, or 8 hands (one more if tied) | 12; often best of 3 | 12 (1v1, 2v2); 16 (4v4) | 9; 15 international | 12 a game; 3-game series, 3 points a game won + 2 bonus for most total points | 11 a game, 3 games; last game may be shortened |
| How a frame scores | One side, a point per ball closer than the other side's best | Same | Same, 1 to 4 a frame | Same | Same | Same | Same, 1 to 4 a frame |
| Tie at end of frame | No points; last scorer tosses from the other end | | | | | | |
| Court | 86.92 x 13.12 ft official | 26.5 x 4 to 4.5 m | | 60 x 12 ft | | | |
| Foul lines | One line for pointing and shooting, about 13 ft from the back wall | Lines A to E: pointing, raffa, volo, minimum pallino | Separate pointing and hitting lines | Pointing and shooting lines, 10 ft | Pitch line and volo line | Point line; may step over if the ball is released first; never past centre | Can't cross the line holding a ball |
| Foot fault | Step on, not over; warning, then the ball is removed | Cards: warning, then a ball is seized | Step on, not over | | Referee penalties | Warning, then rule of advantage | |
| Pallino toss | Toss winner; past centre, short of far line; other side tries; alternate until valid | By draw, then last scorer; past midfield; after two misses the referee places it | Underhand, past mid-court, 12 in from boards; after two misses placed near the far hitting line | Three tries past the 30 ft line, opponent one try, then placed at 40 ft | Behind pitch line; other side tries; referee places it | Coin toss; that side has it in games 1 and 3; one try each, then placed on the D line; a ball's width off the side walls | Last scorer; coin flip to start |
| Who throws next | The side not holding the point | Same | Same | Same | Same | Same | Same |
| Hitting | Allowed (raffa); volo up to the director | Raffa and volo, each declared with its target to the referee | Allowed, must tell the referee ("spock"); **volo not allowed** | Allowed as a firm roll; no volo | Every throw called: punto, raffa or volo | Raffa and volo allowed; calling not stated | Not stated |
| Back wall | Dead (live as a house rule) | Contact voids some shots | | | | Ball on or behind the backboard is dead | Dead unless it touched a ball first |
| Side walls | Live | Not used | | | | | |
| Displacement limit | None | 70 cm (some Italian leagues 50) | | | | | |
| Measuring | Either side, one player crosses; official's call final | Referee only, after marking every ball | Captains or referee | Referee; players may ask | Referee or captains | Any time, players at that end or a captain | |
| Throw clock | Delay: one-minute warning, then a ball burned | 30 s a throw; two 2-minute time-outs | | | 30 s; three 2-minute time-outs | Three 3-minute time-outs a game | |
| No-show | Forfeit after 15 minutes | Leaving the field loses the game | Fewer than 2 present: forfeit 0 to 12 | | | Game 1 forfeits at 8:00, game 2 at 8:15, game 3 at 8:30; short side burns a ball a frame | Forfeit 11 to 0 after 10 minutes; repeat offences lose playoffs, then the league |
| Substitutes | Once a game, may not return | None in singles or doubles | | | | Only at the start of a frame; roster changes until week 5 | |
| Standings tiebreak | | | | | | Point differential, then coin toss; position weeks pair teams by standing | Game record, head to head, fewest forfeits, match record, opponents' win %, earliest sign-up |
| Who referees | Official if present; director decides variations | Referee at every lane, nods every throw | End captains without an official | Referee plus tournament director | Referee has final say | No referee; club officers and a rules committee | An official; duties not described |

## 5. How the engine uses it

- **Presets.** The bocce kit ships each rule set above as a preset: "USBF Open", "CBI international",
  "BSA league", "Special Olympics", the first customer's house rules once we have them, and "House
  rules" (a copy any league edits).
- **Overrides.** An organizer picks a preset per competition and changes only what their league does
  differently (points to win, back wall live, volo off). The page shows the preset and the changes in
  plain words, so players know the rules before they play.
- **Referee screen.** The rule set decides what the referee's phone asks for: a declared shot (CBI),
  a "spock" call (BSA), foot-fault warnings, a throw clock, the end of a frame.
- **Scoring.** Points per frame, the target score or number of frames, and tie handling come from the
  rule set, so standings compute the same way for every league that uses it.

## 6. Still to research

- **bocce-map.com** (run by BocceLabs): the site refused automated reading.
  A BocceLabs post says it maps 157 locations and 428 courts and plans a tournament roadmap. Its
  rule-set filters still need reading (Q2).
- **Canada:** no Canadian national bocce (not boccia) federation or rulebook found yet.
- **South America:** the continental bochas rulebook found online was a dead link; Argentine,
  Chilean and Brazilian federation rules still to read.
- **FIB** volo rules, and Italian federation league variants (the 50 cm displacement limit).
- **Regional and league house rules**, starting with the first customer's own, then across the US
  (Matt, 2026-11-27): Ohio, New York, Pennsylvania and the East Coast down the seaboard, and the West
  from California to Hawaii. Each becomes a preset or an override on the nearest national one. Found,
  not yet read:
  - Special Olympics state chapters: Ohio (manual rev. 10-2026), Pennsylvania (indoor bocce guide
    2021-22), Northern California (2026), Hawaii (2025).
  - City leagues: Solvang, California (co-ed league rules 2025).
  - The bocce map's facility list, to find the clubs and leagues in each region.

## 7. Questions for Matt

- **Q1.** Is the top US body you meant the United States Bocce Federation? No "American Bocce
  Association" rulebook turned up.
- **Q2.** Can you get a copy of the first customer's own league and tournament rules, and the bocce
  map's rule-set list from BocceLabs? Both sites block automated reading, so the first customer's
  house rules are the one set still missing from the matrix.
- **Q3.** For 3v3, should the default be your split (two at one end, one at the other, 4 balls a side),
  with the USBF/CBI walking triples (6 balls a side) as an option? Recommended: yes.

## Sources

- USBF Open Rules, 2023-03-23: https://usbf.us/wp-content/uploads/2023/05/USBF-Open-Rules_03-23-23.pdf
- CBI International Technical Rules: https://cbi-prv.org/multimedia/TechnicalRules16062024.pdf
- Bocce Standards Association (court builder's summary): https://www.sportsunlimitedinc.com/boccegame.html
- Special Olympics Bocce Sport Rules 2024: https://media.specialolympics.org/resources/sports-essentials/sport-rules/Sports-Essentials-Bocce-Rules-2024.pdf
- "The Official Rules of Bocce": https://bocce.org/rules-of-bocce/
- BocceLabs on the bocce map: https://boccelabs.beehiiv.com/p/play-bocce
- A members' club's league rules, 2025: https://americanbocceclub.com/wp-content/uploads/2025/05/ABC_League_Rules-1.pdf
- A Chicago social league's bocce rules, 2023: https://www.playerssports.net/page/bocce-rules
- Special Olympics Ohio: https://sooh.org/wp-content/uploads/2026/10/SOOH-Bocce-Rules-Manual-Rev.-10-2026.pdf
- Special Olympics Pennsylvania: https://specialolympicspa.org/images/Sports_Competitions/2021-2022_Indoor_Bocce_Coaches_Resource_Guide.pdf
- Special Olympics Northern California: https://sonc.org/wp-content/uploads/2026/01/SONorCal-Bocce-Rules.pdf
- Special Olympics Hawaii: https://sohawaii.org/wp-content/uploads/2025/08/2025-Bocce-Rules-and-Sports-Information-Guide.pdf
- Solvang, California league rules: https://www.cityofsolvang.com/DocumentCenter/View/4517/Bocce-Coed-Rules-2025
- Bocce and bolas criollas overviews: https://en.wikipedia.org/wiki/Bocce, https://en.wikipedia.org/wiki/Bolas_criollas
