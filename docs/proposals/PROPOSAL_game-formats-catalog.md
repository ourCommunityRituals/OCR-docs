# PROPOSAL: Game formats catalog (beyond bocce)

**Status:** proposed, first pass. A companion to `PROPOSAL_bocce-team-formats-and-rules.md`.
**Proposed:** 2026-11-27 · **Owner:** Matt
**Lives in** `docs/proposals/`. The presets themselves will live in ourSharedGames (Linear OSG-10).

## 1. What Matt asked for

Matt, 2026-11-27 (voice, lightly edited): do the same format and rules work for the other sports
and the trending bar games (trivia, bags, darts and others), across cultures and across events.
**Soccer (association football) has to be included.**

## 2. The short version

- Every game fits one of **five scoring shapes**. The engine needs those five, not one engine per game.
- Each game then ships as a **preset**: team sizes, the scoring shape and its numbers, and the body
  whose rules it follows. Leagues override what they do differently, as with bocce.
- **Soccer is already an activity** in the brain's taxonomy (`ocr-docs-brain/event-taxonomy.yaml`,
  AC-049), with futsal, beach soccer and blind football. Darts, cornhole and trivia night exist too.
- **Missing from the taxonomy** (section 5): shuffleboard, pétanque, kubb, mölkky, foosball, tejo,
  skee-ball, card and table games. Adding them is a governance change and needs Matt's review.

**How this was made.** The rule bodies below are the well-known ones for each game. Their rulebooks
have **not** been read line by line yet, unlike the bocce matrix. Treat the numbers as the common
defaults, to be checked against each rulebook before a preset ships.

## 3. Five scoring shapes

| Shape | How a game is won | Games |
|---|---|---|
| **Frames to a target** | Points per frame (end, inning) until a side reaches the target | Bocce, cornhole, pétanque, shuffleboard, curling, lawn bowls, tejo |
| **Countdown** | Each side starts high and must reach exactly zero | Darts 501/301, mölkky (count up to exactly 50) |
| **Timed play** | Most goals when the clock ends; draws possible | Soccer, futsal, hockey, basketball |
| **Rounds of questions** | Points per round, highest total wins | Trivia, pub quiz, music bingo |
| **Sets and legs** | Win legs to take a set, sets to take the match | Darts, table tennis, pickleball, foosball |

Standings on top of any shape work the same way: win, draw and loss points, then a tiebreak order
read from the rule set (already planned for bocce).

## 4. Catalog

| Game | Team sizes | Shape and common defaults | Rules body (to read) | Cultures and settings |
|---|---|---|---|---|
| **Soccer** | 11v11; rec leagues 5v5, 6v6, 7v7, 9v9 | Timed; 2 halves; win 3, draw 1, loss 0 | IFAB Laws of the Game; US Youth Soccer small-sided rules; local adult leagues | Worldwide; Latin American, African, European and immigrant community leagues; watch parties |
| Futsal | 5v5 | Timed; 2 x 20 min; accumulated fouls | FIFA Futsal Laws | Latin America, Iberia, indoor winter leagues |
| **Cornhole (bags)** | 1v1, 2v2 | Frames to 21; on board 1, in hole 3; cancellation scoring | American Cornhole League (ACL); American Cornhole Organization | US Midwest and South; bars, tailgates, festivals |
| **Darts** | 1v1, 2v2, teams of 4 to 8 | Countdown 501 double out; Cricket; legs and sets | WDF (steel tip); NDA (soft tip, bar leagues) | UK, Ireland, Netherlands, US bar leagues |
| **Trivia** | Teams of 2 to 6 | Rounds of questions; no wrong-answer penalty by default | No single body; house formats | US and UK pubs, churches, fundraisers |
| Shuffleboard (table) | 1v1, 2v2 | Frames to 15 or 21; 1, 2, 3 zones, hanger 4 | Table Shuffleboard Association | US bars |
| Pétanque | 1v1, 2v2, 3v3 | Frames to 13 | FIPJP | France, North and West Africa, Southeast Asia |
| Kubb | 1v1 up to 6v6 | Knock all kubbs, then the king | US National Kubb Championship rules | Sweden; US Midwest breweries |
| Mölkky | 1 or more a side | Count up to exactly 50; over 50 drops to 25 | International Mölkky Organization | Finland, France, Japan |
| Foosball | 1v1, 2v2 | Goals to 5; best of 3 or 5 | ITSF | Bars, campuses, Europe |
| Tejo | Teams | Frames to a target; exploding mecha bonuses | Colombian Tejo Federation | Colombia and Colombian communities |
| Bolas criollas | 2v2 | Frames to 20 | Venezuelan federation | Venezuela (already in the bocce doc) |
| Skee-ball | 1v1, teams | Total score over games | Brewskee-Ball (bar league) | US bars |
| Card and table games | Pairs or tables | Rounds or hands to a target | Euchre, dominoes, mahjong, chess clubs | Midwest euchre, Caribbean and Latin dominoes, Asian mahjong clubs |

## 5. What to add to the taxonomy (needs review)

Proposed new activities, in a separate brain PR flagged "Needs human review": shuffleboard,
pétanque, kubb, mölkky, foosball, tejo, skee-ball, euchre, dominoes, mahjong. Bocce, bowling and
chess keep their own event types.

**No drinking games** (Matt, 2026-11-27): beer pong and similar games are never listed as a type or preset.

## 6. Questions for Matt

- **Q1.** Which games after bocce come first? Recommended: **soccer, cornhole, darts, trivia**, the
  four Matt named, each read against its rulebook like the bocce matrix.
