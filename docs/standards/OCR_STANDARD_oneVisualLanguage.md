# OCR Standard — One visual language

**Status:** Proposed (needs the owner's review) · **Owner:** OCR governance · **Date:** 2026-11-28 · **Decision record:** [ADR-014](../adr/ADR-014-one-visual-language-across-every-app-and-partner.md)

## Rule

Every screen in every OCR app uses the same building blocks, in the same places, the same way.
Only the **labels** change between apps, partners and roles.

- **Apps:** ourSharedEvents, ourWKRP, ourAirwaves, ourSharedMagnets, ourSharedGames, ourSharedRecords, ourSharedPulse, and every white-label or partner deployment.
- **Partners:** bars and venues, event organizers, schools and boosters, places of worship, government and village services, leagues.
- **Why:** these groups work together. A person who volunteers at a church fundraiser, referees a league game and checks in at a bar night should never have to relearn the screen.

## The building blocks

| Block | What it is | Use it for |
|---|---|---|
| **Tabs** | A row across the top; one tab = one phone screen | Splitting a page into parts (Schedule · Roles · Board) |
| **Chips** | Small one-tap pills, one or many selected | Picking: nights, roles, categories, filters |
| **Cards** | A boxed item with a picture or code, a title, must-knows and one button | Any item in a list: an event, a shift, a game, a sponsor |
| **Buttons** | Big, one tap, a short verb that names the outcome | Every action ("Take this shift", "Check in") |
| **Deeper Dive** | An arrow plus the words "Deeper Dive"; tap to open, tap to close | The longer explanation, never the must-knows |
| **More** | A button that shows the next screen of items | Long lists (6 rows a screen, then More) |
| **UEC colours** | The Universal Event Code colours, with a word or glyph beside each | Codes, map cells, categories, everywhere |

## The screen rules

- **One phone screen per tab.** No scrolling (375 × 812 baseline). Too much for one screen means another tab, paging, or More.
- **Must-knows stay on screen.** Price, cash only, sign-up needed, age limits: on the card, never behind Deeper Dive.
- **Reading level: 5th to 8th grade.** Short words, short labels, cards and buttons instead of paragraphs.
- **Taps at least 44 px** (org floor, invariant #14; the hub targets 48). Input text at least 16 px.
- **Colours only from the hub tokens** (`packages/tokens`). Colour is never the only signal.
- **Same pattern, new labels.** Before designing a new screen, copy an existing one (below) and change the words.

<details>
<summary>Deeper Dive: the same pattern, three partners</summary>

A sign-up uses one layout everywhere: tabs **Schedule · Roles · My shifts**, chips for the night, a card per slot with one button.

| Partner | Tab labels | Chip labels | Card button |
|---|---|---|---|
| Boosters (school) | Games · Roles · My shifts | Fri · Sat · Gate · Concessions | Take this shift |
| League | Games · Referees · My games | Week 3 · Court 1 · Court 2 | Take this game |
| Church fundraiser | Days · Helpers · My times | Sat · Sun · Kitchen · Setup | Sign me up |

The person who learned one already knows the other two.
</details>

<details>
<summary>Deeper Dive: reference screens to copy</summary>

- **Create an event or sponsor in two screens:** ourSharedEvents draft PR 1593 (create flows).
- **Tabs and chips for roles:** the boosters roles mockups (project files, `boosters/mockups/`).
- **Tabs, More and a big table on one screen:** leagues, ourSharedEvents PR 1584.
- **Deeper Dive:** hub `packages/ui/src/styles.ts` (`.deeper-dive`, `.needs-you` when the person needs it to act); ourSharedEvents `src/lib/deeper-dive.ts`.
</details>

<details>
<summary>Deeper Dive: Deeper Dive details</summary>

- One name and one icon everywhere. Never "More info", "Details", "Learn more" or "How X works ›" for the same thing.
- A real control: `<details class="deeper-dive"><summary>Deeper Dive</summary>…</details>` or a button with `aria-expanded` and `aria-controls`. Enter and Space open and close it; focus is visible.
- Highlighted (`.needs-you`) only when the person needs that information to finish an action.
- Text inside also reads at a 5th to 8th grade level.
</details>

<details>
<summary>Deeper Dive: where each block lives</summary>

- **One home:** the hub, `ourCommunityRituals/packages/ui` (`@ocr/ui`). Apps consume it through their `.ocr-hub-ref` pin (ADR-008). An app never builds its own tabs, chips or Deeper Dive.
- **Both forms:** each block is in the shared stylesheet (server-rendered pages) and in `@ocr/ui/react` (ourAirwaves and later React apps), with the same class names.
- **Skins** (ourAirwaves self-serve) may change the brand accent, images and words. They never change the blocks, their order, tap sizes or the screen rules. Same rail as "never tier-gated" in the ourAirwaves proposal.
- **Languages:** labels are translated strings; the layout never changes by language.
</details>

<details>
<summary>Deeper Dive: how this relates to other standards</summary>

- **Mobile workability** (`OCR_STANDARD_mobileWorkability.md`, invariant #14): sets the measurable floors (no sideways scroll, 44 px taps, 16 px inputs, CTA above the fold). This standard adds the shared blocks and the one-screen-per-tab rule on top.
- **Hub design system** (`packages/ui/design-system/README.md`): colours, type, contrast, "choice, made easy". This standard does not repeat them.
- **One layer map** (ADR-013): maps follow that ADR; a map sits inside a tab like any other block.
</details>

## Space and flow (owner, 2026-11-28)

Keep the clean, modern look. Use more of the screen, keep the breathing room, and make moving from screen to screen feel like one smooth app.

- **Pictures go edge to edge;** text keeps a 16 px side margin. The picture gets more room without crowding words.
- **Space by grouping, not boxes.** 8 px inside a group, 16 to 24 px between groups. Fewer borders inside cards.
- **One spacing scale:** 4 · 8 · 12 · 16 · 24 · 32 px, as named hub tokens. The 12 px gap between taps never shrinks.
- **Fit the real screen:** size one-screen tabs with `svh`/`dvh` and the phone's safe areas, so browser bars and notches never push the button off screen.
- **Thin, sticky top and bottom:** the header shrinks once you move; tabs stay pinned; the main button sits at the bottom, in thumb reach.
- **Screens flow into each other:** the event picture on a card grows into the event page header; tabs slide left or right in the direction you tapped; Deeper Dive opens smoothly.
- **Quick and calm motion:** 150 to 250 ms, easing out. Instant for anyone who turns motion off. Nothing moves under a finger.
- **Fresh comes from the content:** event art, photos and short muted loops change; the blocks, colours and layout rules do not. Event lists may mix card sizes; sponsor cards stay the same size (fairness covenant).

<details>
<summary>Deeper Dive: our rules next to modern web practice</summary>

Hub rules read from `packages/ui/design-system/README.md` and `src/styles.ts`, hub main `2c6699c`.

| Topic | Ours today | Modern practice (2026) | Gap and recommendation |
|---|---|---|---|
| Spacing | Exact values: page 16 to 20 px, section 24, card 16 | A 4 px base scale held as tokens | Add named space tokens (4 to 32) so every app spaces alike |
| Taps | 48 px, 56 px primary, 12 px gap | 44 to 48 px, spacing between taps matters as much as size | Ahead of practice. Keep |
| Screen height | `100dvh` in one place | `svh`/`dvh`/`lvh` plus safe-area insets | Use `svh` for one-screen tabs, `dvh` for full-screen panels |
| Pictures | Fixed frame, crop photos, fit flyers | Full-bleed media, fixed aspect ratio while loading | Make the frame full-bleed on phones |
| Separation | Lines and radius, no shadows | Flat with lines, or light elevation | Keep lines (it is the modern flat look); optional later: one soft shadow for sheets only |
| Screen-to-screen | Plain page loads | View Transitions: shared pictures morph, tabs slide | Add it. Works with no framework |
| Open/close | Deeper Dive snaps open | Smooth height (`interpolate-size`, `@starting-style`) | Animate open and close, instant under reduced motion |
| Lists of pictures | Scroll-snap in one place | Snap rows for galleries | Use snap rows for photos only, never for must-knows |
| Reduced motion | Honoured | Honoured | Keep |
</details>

<details>
<summary>Deeper Dive: screen-to-screen motion, who gets it</summary>

- **Cross-page View Transitions** (`@view-transition { navigation: auto; }`): Chrome and Edge 126+, Safari and iPhone 18.2+, about 90% of users (caniuse, October 2026). Firefox and Samsung Internet do not have it yet: they just load the page normally, so nothing breaks.
- **Same-page transitions** (tabs, Deeper Dive, React in ourAirwaves): in every major browser since October 2025.
- **How a shared picture morphs:** the card picture and the page header carry the same `view-transition-name` (one per event). One CSS rule in the hub, no script.
- Sources: [caniuse](https://caniuse.com/cross-document-view-transitions), [web.dev](https://web.dev/blog/same-document-view-transitions-are-now-baseline-newly-available), [Chrome docs](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document), [web.dev tap targets](https://web.dev/articles/accessible-tap-targets).
</details>

## Where apps differ today

Read on default branches, 2026-11-28. Method in the PR description.

- **Hub (`@ocr/ui`):** has Deeper Dive (CSS only). No shared tabs or chips. The React kit has `BottomNav` but no Tabs, Chips or DeeperDive.
- **ourSharedEvents:** pinned to current hub main, uses Deeper Dive in 3 source files. Tabs and chips are hand-built per page (about 10 source files).
- **ourWKRP:** pinned to an older hub commit (`b039d2f`, 22 Oct) that has no Deeper Dive. Uses its own `.filter-chip`. No tabs.
- **ourAirwaves:** uses `@ocr/ui/react`, with a bottom nav instead of top tabs. No chips or Deeper Dive yet.
- **ourSharedMagnets, Games, Records, Pulse:** docs only; no screens yet, so they start on this standard.

## Next steps (not done in this PR)

1. Add shared **tabs** and **chips** to the hub (CSS + React), with tests for 44 px taps and keyboard use.
2. Add **DeeperDive**, **Tabs** and **Chips** to `@ocr/ui/react`.
3. Bump ourWKRP's hub pin; swap `.filter-chip` for the shared chips.
4. Move ourSharedEvents' hand-built tabs onto the shared ones, page by page.
5. Decide (owner): top tabs vs the ourAirwaves bottom nav. See ADR-014, open question Q1.
6. Add the space tokens, full-bleed frame, View Transitions and smooth Deeper Dive to the hub (one hub PR), then show them on one ourSharedEvents page on staging before rolling out.
7. A design check that fails a page using a non-hub tab, chip or "Learn more" label, once the blocks exist.
