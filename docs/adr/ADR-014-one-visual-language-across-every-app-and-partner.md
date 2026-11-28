# ADR-014: Use one visual language in every OCR app and for every partner type; only the labels change

**Status:** Proposed. Needs the owner's review. One open question (Q1) is the owner's.
**Date:** 2026-11-28
**Deciders:** Owner (Matt)
**Scope:** Fleet-wide
**Enforced-by:** none - proposed; a hub design check becomes the enforcement once the shared tabs and chips exist (standard, next step 6)

## Context

The owner, 2026-11-28 (project thread "Make one design language org-wide"):

> "the idea also is to use the same visual language across the hyperlocal UIs. The users all get used
> the same experience without having to adjust to a new role between the bars, events, schools, places
> of worship, and government services as they have opportunities to work together. This same design
> paradigm goes up a level higher to the organizational and ORC-doc level so it applied across the infra"

The pieces already exist, but per screen and per app:

- the hub design system sets colours, type and contrast (`packages/ui/design-system/README.md`, 2026-10-08);
- mobile workability sets floors (invariant #14);
- the owner's phone rules (26 to 28 Nov): no scrolling, one screen per tab, tabs and chips, cards and
  buttons, More for long lists, 5th to 8th grade reading, must-knows on screen, one Deeper Dive component;
- Deeper Dive is in the hub (`styles.ts`, hub PR 95); tabs and chips are not, so each app builds its own.

Without an org rule, each app and each partner type drifts into its own layout, and a person crossing
from a bar night to a school fundraiser has to learn a new screen.

## Decision

1. **One set of blocks** for every app and partner type: tabs, chips, cards, buttons, Deeper Dive, More,
   UEC colours. Defined in `docs/standards/OCR_STANDARD_oneVisualLanguage.md`.
2. **One set of screen rules:** one phone screen per tab, must-knows on screen, 5th to 8th grade reading,
   44 px taps, hub tokens only.
3. **Only labels change** between apps, partners and roles. A new screen copies an existing pattern.
4. **One home:** every block lives in the hub (`@ocr/ui`), in both the shared stylesheet and the React kit.
   Apps never build their own versions.
5. **Skins and tiers never change the blocks.** A skin may change accent, images and words, not structure,
   order, tap sizes or screen rules.

## Alternatives Considered

### Alternative A: A look per partner type (a school look, a church look, a bar look)

**Rejected because:** it makes people relearn the screen when partners work together, which is the exact
cost the owner wants gone; it also multiplies the design and test work by the number of partner types.

### Alternative B: Leave it to each app's design system notes

**Rejected because:** that is today's state, and the apps already differ (see the standard, "Where apps
differ today"). Only an org rule binds ourAirwaves, ourWKRP and the docs-only products alike.

## Consequences

### Positive

- A person learns the app once and can act in any role, at any partner.
- New partner types cost words, not designs.
- One set of accessibility tests in the hub covers every app.

### Negative

- The hub must grow tabs and chips (CSS and React) before apps can drop their own; until then the rule
  is partly prose.
- ourWKRP's pin is a month behind; adopting needs a pin bump with visual baseline changes.
- Some rich screens (admin, SharedReport) will need splitting into tabs to fit one screen each.

### Neutral

- Colours, type and contrast stay where they are (hub design system); this ADR does not move them.

## Open questions for the owner

- **Q1. Top tabs or bottom nav?** ourAirwaves uses a bottom nav today; the rule says tabs across the top.
  Recommendation: bottom nav for moving between whole sections of an app, top tabs inside a page.

## Implementation Notes

- Standard: `docs/standards/OCR_STANDARD_oneVisualLanguage.md`
- Hub: `ourCommunityRituals/packages/ui` (`.deeper-dive` in `src/styles.ts`; tabs and chips to add)
- Affected repos: all product repos and partner deployments

## References

- ADR-008 (spokes consume the hub through a pinned commit)
- ADR-013 (one layer map; the same "one component, every surface" idea for maps)
- `OCR_STANDARD_mobileWorkability.md` (invariant #14)
- ourAirwaves self-serve proposal (skins never change rails)

## Revisit Criteria

- If a partner type needs an action the blocks cannot express, add a block to the hub; do not fork the layout.
- If research with 50 to 75 year-old users shows tabs fail on one screen, revisit the one-screen rule.
