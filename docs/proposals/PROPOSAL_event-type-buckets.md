# PROPOSAL: Event type buckets (a simpler first screen)

**Status:** proposed, waiting on Matt. No code changes until approved.
**Proposed:** 2026-11-27 · **Owner:** Matt
**Lives in** `docs/proposals/`, so it does not propagate to spokes.
**Mockups:** [category row, today and tuned](assets/event-type-buckets-row.png) · [bucket grid and a bucket opened](assets/event-type-buckets-phone.png)

## The ask in one line

Visitors see a few plain, picture-first buckets ("Bargains", "Sports & Recreation"), tap one, and see every event in it.

## Rules this keeps (Matt, 2026-11-27)

- **The guts stay the same.** Buckets are a display layer. Type ids, UEC codes, `category_code`, exports, BigQuery and reports do not change.
- **Few words on screen.** Cards and buttons with pictures; a small arrow opens the longer explanation.
- **Mobile first.** The category row stays where it is, at the top of the home screen; events start higher.
- **Easy to read.** Every name on screen reads at a 5th to 8th grade level, the reading level of most adults (Matt, 2026-11-27).
- Drinking games are never a type. Soccer stays in.

## The buckets (9, plus "Everything")

| # | Bucket | Short name on the row | What a visitor finds there |
|---|--------|----|----------------------------|
| 1 | Sports & Recreation | Sports & Rec | Things you do with your body: leagues, pickup games, lawn games, runs, walks, skating, day trips |
| 2 | Games & Trivia | Games | Trivia, bingo, board and card games, pinball, foosball |
| 3 | Music & Shows | Music & Shows | Live music, karaoke, open mic, comedy, film, art shows |
| 4 | Parties & Festivals | Parties | Block parties, cookouts, dinners, festivals, dances, parades, New Year's |
| 5 | Bargains | Bargains | Flea markets, swaps, yard sales, resale, craft fairs, store deals |
| 6 | Kids & Family | Kids | Kids' parties, camps |
| 7 | Learn & Connect | Learn | Classes, lessons, workshops, book clubs, networking |
| 8 | Give Back | Give Back | Volunteering, food drives, fundraisers, charity nights |
| 9 | Neighborhood & Faith | Community | Community meetings, forums, faith services |

## Tuning the category row (Matt: "90 to 95% there")

Matt likes where the row sits and the cards, "more" buttons, footer and top-left menu below it. What changes is how the row draws:

- **9 short names instead of 15 long ones.** "Social & Community Dining" becomes "Parties".
- **Smaller tiles** (about 74 px, icon 30 px), so 4 show plus a peek of the 5th, which says "swipe".
- **One arrow on the end of the row** instead of a second row of arrows under it.
- **No "Kinds of events" heading.** The pictures say it; screen readers still hear it.
- Result: the first event card starts about 80 px higher on a phone.

Today's look in the mockup is drawn from the code (`.icon-slider` in the hub's `styles.ts`: 120 px tiles, 40 px icons, arrows below), because staging could not be opened from this session.

Tapping a bucket opens its list: type chips across the top (Flea, Yard sales, Swaps), then event cards. A card's arrow opens a two-line description and an "Open event" button.

## Plain names for today's types (display only)

The name people see changes; the type's id and code do not. Names over a 6th grade level today:

| Today | Plain name |
|-------|------------|
| Professional Development Workshop | Job Skills Class |
| Business Networking Meetup | Business Meetup |
| Industry Mixer | Work Mixer |
| Mutual Aid Distribution | Free Supplies Giveaway |
| Neighborhood Association Meeting | Neighborhood Meeting |
| Block Captain Election | Block Captain Vote |
| Community Faith Service | Faith Service |
| Interfaith Community Gathering | Many Faiths Together |
| Art Show & Gallery Opening | Art Show |
| Community Mural Unveiling | New Mural Reveal |
| Photography Exhibition | Photo Show |
| Tabletop RPG Session | Role-Playing Game Night |
| Silent Auction Fundraiser | Silent Auction |
| Walkathon / Fun Run Fundraiser | Fun Run or Walk for a Cause |
| Community Garden Planting Day | Garden Planting Day |
| Garden Harvest Festival | Harvest Festival |
| Neighborhood Potluck | Potluck |

New types use plain names from the start (Yard Sale, Bingo Night, Kids' Party). Proper game names (Pétanque, Kubb) stay, with a one-line "what it is" behind the arrow.

## Before and after

**Before:** 15 categories on the landing slider and in the Create Event picker. **After:** 9 buckets.

| Today's category (code) | Its types go to |
|-------------------------|-----------------|
| Sports & Recreation (REC) | Sports & Recreation |
| Fitness & Running (FIT) | Sports & Recreation |
| Tabletop & Board Games (TAB) | Games & Trivia |
| Entertainment & Trivia (ENT) | Trivia, Game Night → Games & Trivia · Film, Karaoke → Music & Shows |
| Performing Arts & Open Mic (PER) | Music & Shows |
| Arts, Culture & Live Music (ART) | Music & Shows · Cultural Festival → Parties & Festivals |
| Social & Community Dining (SOC) | Parties & Festivals |
| Neighborhood Markets (MKT) | Bargains |
| Literary & Book Clubs (LIT) | Learn & Connect |
| Business & Networking (BIZ) | Learn & Connect |
| Fundraisers (FND) | Give Back |
| Volunteer & Mutual Aid (VOL) | Give Back |
| Gardening & Outdoor (GAR) | Trail Walk → Sports & Recreation · Planting Day → Give Back · Harvest Festival → Parties & Festivals |
| Civic & Neighborhood (CIV) | Neighborhood & Faith |
| Faith Community (FAI) | Neighborhood & Faith |

<details>
<summary>Every type, one by one (49 today + 20 new = 69)</summary>

Method: `event_type_registry` rows in OSE migrations `0024` (47), `0097` (Watch Party) and `0115` (Storytime). New types are marked **new**.

- **Sports & Recreation (8 + 7 new = 15):** Bocce Tournament, Softball League Game, Volleyball Meetup, Cornhole Tournament, Pickup Basketball, Kickball Game, Running Club Meetup, Nature Trail Walk · **new:** Soccer, Bar League (darts, pool), Shuffleboard, Pétanque, Kubb, Skating, Day Trip
- **Games & Trivia (4 + 4 new = 8):** Trivia Night, Game Night, Board Game Night, Tabletop RPG Session · **new:** Bingo Night, Pinball, Foosball, Card Games
- **Music & Shows (11):** Live Music Event, Karaoke Night, Film Screening, Open Mic Night, Poetry Slam, Storytelling Night, Storytime (adults telling stories), Stand-Up Comedy Night, Art Show & Gallery Opening, Community Mural Unveiling, Photography Exhibition
- **Parties & Festivals (7 + 3 new = 10):** Community Dinner, Neighborhood Potluck, Block Party, Community Cookout, Watch Party, Cultural Festival, Garden Harvest Festival · **new:** Dance, Parade, New Year's Party
- **Bargains (3 + 2 new = 5):** Flea Market, Craft Fair, Community Swap Meet · **new:** Yard & Garage Sale, Resale & Deals Day
- **Kids & Family (0 + 2 new = 2):** **new:** Kids' Party, Camp
- **Learn & Connect (4 + 1 new = 5):** Book Club Meeting, Business Networking Meetup, Professional Development Workshop, Industry Mixer · **new:** Class or Lesson
- **Give Back (7 + 1 new = 8):** Neighborhood Cleanup, Food Drive, Mutual Aid Distribution, Community Garden Planting Day, Silent Auction Fundraiser, Walkathon / Fun Run Fundraiser, Car Wash Fundraiser · **new:** Charity Night
- **Neighborhood & Faith (5):** Neighborhood Association Meeting, Community Forum, Block Captain Election, Community Faith Service, Interfaith Community Gathering

New types take a home `category_code` from today's 15 (for example Soccer → REC, Bingo → ENT, Yard Sale → MKT), so reports keep grouping the same way.

</details>

## What it touches (checked in OSE code, 2026-11-27)

- **Changes (display only):**
  - Landing "Type" slider (`lib/landing-area.ts`, `lib/category-slider.ts`): shows 9 buckets instead of 15 categories; 9 new icons.
  - The row's sizes and arrow place in the hub's `.icon-slider` (sizes only; no colours change).
  - Create Event picker (`lib/event-type-catalog.ts`): "Bucket > Type" instead of "Category > Type".
  - Spanish names for the 9 buckets (i18n catalog).
- **Does not change:**
  - QR code colours. UEC colours follow what a code does (enter, vote, live), not the event type.
  - Posters, TV display, voting: none of them read the event type.
  - Exports, BigQuery, corridor flow, SharedReport: keyed on `uec_code`, unchanged.
  - Dashboard "by category" (`handlers/dashboards.ts`): keeps `category_code`. A "by bucket" view can be added later.
  - Practice accounts on staging (PRs #1581, #1588, #1589, #1590) and leagues (PR #1584): they use existing type ids, which all stay.

<details>
<summary>How it would be built (after approval)</summary>

- One additive migration: a `event_type_bucket` lookup (code, name, order) and a `bucket_code` on each type. Nothing renamed or dropped.
- The new types as one seed migration, `INSERT OR IGNORE`, each with a legal clearance tier.
- Tests that would move: `event-type-catalog.spec.ts` (every type has a bucket, no orphans), `category-slider.spec.ts` (an icon per bucket), the `landing-categories*` specs (labels).
- A type with no bucket shows under "Other", last, never dropped (today's zero-waste rule).

</details>

## Decisions for Matt

- **D1. The 9 buckets and their names.** Recommended: as above.
- **D2. Add the 20 new types.** Recommended: yes, except the ones in D3 wait.
- **D3. Types that may need a permit or licence.** Bingo, charity nights with raffles, parades and camps can need a licence or permit, so they would sit above today's launch clearance tier (tier 1) and stay hidden until cleared. Recommended: add them now at a higher tier, so they appear when the tier opens.
- **D4. Craft Fair under Bargains.** It is shopping, so it fits, but it could sit in Music & Shows with the art. Recommended: Bargains.
- **D6. Plain type names** (table above). Recommended: yes, as a display-name change only.
- **D5. Row or grid.** The tuned row keeps today's position. A 3 × 3 grid (second mockup) shows every bucket at once but pushes events down. Recommended: the tuned row.
