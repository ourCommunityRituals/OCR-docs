# ADR-013: Draw every map in the fleet with one layer-map component; each surface picks its layers, each layer carries its own privacy class

**Status:** Proposed. Nothing in it is built. Two choices in it are the owner's and are marked "Open, for the owner".
**Date:** 2026-11-25
**Deciders:** Owner (Matt). Whether a SharedReport may show ring shapes is a separate open question for the owner and is not decided here.
**Scope:** Fleet-wide
**Enforced-by:** none - proposed; the component's contract tests (D7) become the enforcement when it is built

## Context

The owner, 2026-11-25: the Node, Corridor and Ring layer map "should be available wherever there
is a map referenced in any application across the infra, and then it's a matter of which layers
are in play." That covers ourSharedEvents (OSE), ourWKRP (OW), ourAirwaves (OA) and every other
product.

The layer map exists today only as a prototype in ourEventRings (OER) draft PR 6 (head `2cafcb2`,
`tools/prototype/ncr-layer-map.html`, and the GeoJSON writer `ncr/layers.py`). Its stack order is
the owner's (2026-11-25), bottom to top:

1. a see-through base map: streets, and towns in light tints with neighbours in different tints;
2. the H3 hexagons at resolution 7, 6 and 5;
3. corridors and their nodes, which show where the map measures;
4. rings, on top.

The owner also asked that the stack order and the meaning of each layer live **in the data**, so an
agent can read the map as well as a person can see it.

The OSE SharedReport is getting this stack now (ose:ADR-041, OSE draft PR 1557; not duplicated here),
with rings drawn empty until the owner decides whether reports may show ring shapes under
ose:ADR-026. The owner's options for that question are written up at
<https://claude.ai/artifact/XeWyHNmMj61u3Cbh1cnivx>.

### Every map in the fleet today (read 2026-11-25, default branches)

| # | Surface | Where | What it draws | Who sees it |
|---|---------|-------|---------------|-------------|
| 1 | Landing attendee map (`/events`) | OSE `src/lib/attendee-map.ts`, `handlers/pages.ts` | Res-7 areas with listed events, on the street base; pan/zoom and tooltip scripts | Public |
| 2 | Zoomed area view and place panel | OSE `src/lib/landing-area.ts`, `map-place-panel.ts`, `map-pan-script.ts`, `map-tip-script.ts` | The same, one area up close | Public |
| 3 | Public area-map read `GET /api/v2/map/areas` | OSE `handlers/map-areas.ts` (ose:ADR-033) | Parts, not a picture: frame, res-7 outlines, street layer, credit | Other apps' builds |
| 4 | SharedReport corridor map (`corridor_map`, Mid depth and up) | OSE `src/lib/corridor-map.ts`, `shared-report-builder.ts`, `report-depth.ts` | Floored poster-placement cells, own frame, no streets yet (ose:ADR-036 D2 proposes the base) | Organizer, sponsor |
| 5 | Venue thumbnail on the event page | OSE `handlers/venue-image.ts`, `lib/maps.ts` | A Google Static Maps image (billed, not H3) | Public |
| 6 | Street-map proof | OSE `proofs/street-map/` | Tile proof Worker, not a product surface | Internal |
| 7 | Creator showcase "where" map | OW `showcase/lib/map.mjs` | Res-7 event areas drawn from surface 3's answer | Public (static pages) |
| 8 | Layer-map prototype and public/admin layers | OER `tools/prototype/`, `ncr/layers.py`, `tools/corridor_map.py` (PR 6) | Towns, streets, transit, hex 7/6/5, corridors, nodes, busy places, rings | Internal, prototype |
| 9 | `HexMap` mock-up | hub `packages/ui/design-system/components/bundle.js` | A fixed grid with no real cells (fails OCR_STANDARD_hexMaps rules 3, 5, 10) | Design system only |
| 10 | Map canvases and `MapDetail` | hub `design-system/canvas/MapSystem.dc.html`, `SiteMap.dc.html`, `components/MapDetail/` | Design references for the corridor, area and site maps | Design system only |

Products with no map code: OA, OurSharedMagnets (OSM), OurSharedGames (OSG), OurSharedRecords (OSR)
and OurSharedPulse (OSP) hold docs only. OSG's bocce reference
(`docs/corridors/OCR_REFERENCE_chicagoBocce.md`) already expects "the node, corridor and ring map
layers". OA deploys new corridor and client instances, so every OA deployment will inherit
whatever OSE and OW do. Links out to Google or Apple Maps (OSE `lib/geo-link.ts`) are not maps we
draw and are out of scope.

So there are three real renderers (OSE's landing, OSE's SharedReport, OER's prototype), one
consumer of OSE's parts (OW's showcase), one billed image, and two design mock-ups. Each draws its
own frame, its own styles and its own idea of a layer.

### Rules already in force that this decision keeps

- `OCR_STANDARD_hexMaps` (Proposed 2026-10-08): res 7 or coarser in public; the outline from the
  cell; the K = 5 floor with no exceptions; readiness before a map of two things; colour carries
  the event category, never the person; no named/anonymous split; no cross-product cell except
  from OER; server-rendered inline SVG with no client fetch of raw cells; a neighbour-dataset test
  for every map that draws counts.
- fleet:ADR-011: res 9 only for physical places; res 7 is the corridor.
- ose:ADR-033 and ose:ADR-036 D1: street tiles stay in OSE's bucket and are read only through
  `loadStreetLayer`, with cells only. Other apps get streets as parts from `/api/v2/map/areas`.
- ose:ADR-026: no OER dataset value reaches anyone who can create an event, scan, or read a
  SharedReport until rule C (noise) exists. The owner's ruling of 2026-11-23: the public OER layer
  is shapes only, no numbers.
- fleet:ADR-008 and the `@ocr/ui` design system: tokens only, guideline `30-uec-and-maps.md`
  (`--map-ground`, `--map-cell-line`, stroke-only empty cells, `-ui` hues plus glyphs) and
  `60-map-archetypes-and-venues.md` (corridor, area and site maps are different objects).

## Decision (proposed)

**D1. One component draws every geographic map.** A single layer-map renderer draws every map in
the fleet that sits on real geography: surfaces 1, 2, 4 and 7 above, OER's published maps, and
every future OA, OSG or OW map. It is a pure function: layers and a frame in, inline SVG out. It
reads nothing, fetches nothing and stores nothing, so it runs in a Worker, in a static build and in
a test alike. Site maps (inside one venue, no basemap) are a different archetype under guideline 60
and stay out of it. Where the component lives is open (O1).

**D2. One layer registry, with order and meaning in the data.** Every layer has an entry in one
registry, and a surface can draw only registered layers:

| Order | Layer id | Step | Meaning (the sentence an agent reads) | Privacy class | Source |
|------:|----------|------|---------------------------------------|---------------|--------|
| 10 | `base.towns` | base | Towns and community areas, light tints, neighbours differ | geometry | OER jurisdictions |
| 20 | `base.streets` | base | Streets, see-through, under everything | geometry | OSE `loadStreetLayer` only |
| 25 | `base.transit` | base | Rail and transit lines | geometry | OER |
| 30 | `hex.7` | hexagons | Small areas: the res-7 hyperlocal grid | geometry | H3 |
| 40 | `hex.6` | hexagons | Medium areas: res 6 | geometry | H3 |
| 50 | `hex.5` | hexagons | Large areas: res 5 | geometry | H3 |
| 55 | `areas.events` | hexagons | Areas with listed events, by category hue and glyph | listing-count | the product's own listings |
| 60 | `corridors` | corridors | Corridor strips: where the map measures; amber where one crosses a town line | geometry | OER corridors (synced copy) |
| 70 | `nodes` | corridors | Crossroads, retail at a town line, stations, founding places | geometry | OER |
| 75 | `busy` | rings | Busy places from OER | oer-derived | OER public layer |
| 80 | `rings` | rings | Small, medium and large rings of concentration | oer-derived | OER public layer |
| 90 | `report.cells` | rings | This report's floored scan cells, drawn over the stack | people-count | the SharedReport's own floored counts |
| 95 | `labels` | all | Place names | geometry | place names |

The step is one of the four the owner walks through (base, hexagons, corridors, rings). OSE's
SharedReport layer stack (`src/lib/ncr/layer-stack.ts`, ose:ADR-041, OSE draft PR 1557) already
uses these ids, steps, classes and numbers for its nine layers, so moving the report onto the
component changes no layer. The numbers leave room to add layers without renumbering. Every drawn map carries the stack
it actually drew as data: each layer is a `<g data-layer="…" data-step="…" data-order="…" data-class="…">`, and
the SVG's `<metadata>` holds one JSON object listing the surface, the as-of week, and each layer's
id, step, order, meaning, class and whether it was shown or withheld (and why: "below the floor", "not
ready", "not allowed for this audience"). A person sees the drawing; an agent reads the same facts
without guessing from colours.

**D3. Each layer's privacy class decides who may see it.** The audience is a property of the
surface (public, organizer, sponsor, internal). The renderer refuses a layer whose class the
audience may not see, and the refusal is a build or test failure, not a silent omission.

| Class | Public | Organizer / sponsor (own event) | Internal, named (ose:ADR-026 rule A) |
|-------|--------|----------------------------------|--------------------------------------|
| geometry | Yes | Yes | Yes |
| listing-count | Res 7 or coarser, after the readiness gate (hexMaps rule 4) | Yes | Yes |
| people-count | Res 7 or coarser, each count floored at K = 5 as a sum of floored parts (hexMaps rule 3) | As today's accepted rules allow (res 9 placement cells on the organizer's own screens and the floored SharedReport cells; ose:ADR-017, ose:ADR-025) | Yes |
| oer-derived | Shapes only, no numbers (owner, 2026-11-23) | **Open.** The owner has not decided whether a SharedReport may show ring shapes and has asked for time; until then the layer is listed and drawn empty. Numbers never before ose:ADR-026 rule C | Shapes and numbers |

Three cross-layer rules ride on top, from `OCR_STANDARD_hexMaps` rules 6 and 7: no map splits OW
(named) from OSE (anonymous) people in one area; an OSE count and an OW count share a cell only
when OER produced it; and an oer-derived figure is never drawn on the same map as a per-event
people-count figure, because the two could be subtracted. Shapes without numbers do not trigger
the last rule.

**D4. Each surface declares its layers in a small config.** A surface names its audience, the
layers it may show, which are on at first, and whether the step-through is offered:

```ts
{ surface: 'ose.shared-report', audience: 'sponsor',
  layers: ['base.towns', 'base.streets', 'hex.7', 'hex.6', 'hex.5', 'corridors', 'nodes', 'rings', 'report.cells'],
  on: ['base.towns', 'base.streets', 'hex.7', 'corridors', 'nodes', 'report.cells'],
  steps: true }
```

The config is checked against the registry and the D3 table when the app's tests run. Who may
change it after deploy is open (O2).

**D5. One frame, one door for streets.** Every map is drawn in the Web Mercator frame OSE already
uses (`frameForCells`), fitted to res-7 cells that are shown, never to a withheld one
(ose:ADR-036 D4). Streets come only through OSE: `loadStreetLayer` inside OSE, and the parts from
`/api/v2/map/areas` for anyone else (ose:ADR-033). The component takes the street layer as an
input and never reads tiles itself. A missing street layer leaves the rest of the map whole.

**D6. One way to see the layers.** With no script, the surface's `on` layers are drawn at once,
and the list beside the map is still the real content (guideline 60). Where `steps` is true, a
small script offers the owner's step-through (Base map, Hexagons, Corridors, Rings, All layers),
focus layer full and earlier layers faded, under the same bans the landing's map scripts keep: no
request and no storage. Styles come from `@ocr/ui` tokens only.

**D7. Tests come with the component.** The registry test fails on a layer with no meaning or
class; the audience test fails when a config asks for a layer its audience may not see; the
neighbour-dataset test (hexMaps rule 11) ships as a helper every people-count or listing-count
surface runs; and the metadata test checks that the JSON stack matches the `<g>` order drawn.

### Open, for the owner

- **O1. Where the component lives.** Recommended: in the hub's `@ocr/ui` package
  (`packages/ui`), beside the tokens it draws with, so every product pins one version through
  `.ocr-hub-ref` (fleet:ADR-008). The alternative is to keep drawing inside OSE and have every other
  app ask OSE for a finished picture, which ose:ADR-033 D2 already declined ("parts, not a finished
  picture").
- **O2. Who may change a surface's layers.** Recommended: the config is code, changed by pull
  request; an organizer or an OA deployment may turn a layer **off** at runtime but never on beyond
  what the config allows. The alternative is code only, with no runtime switch.

## Alternatives Considered

### Alternative A: each app keeps its own renderer and copies the layer list

**Rejected because:** three renderers already disagree on frame, styles and what a layer is, and
the privacy rules would be re-implemented, and re-reviewed, in each one. A rule fixed in one would
stay broken in the others.

### Alternative B: one renderer in OSE, other apps embed OSE's finished SVG

**Rejected because:** OW, OA and OER would depend on OSE's runtime for every map, OSE would need to
know each other app's audiences and layers, and ose:ADR-033 already chose parts over a finished
picture so the caller keeps its own labels and accessible name.

### Alternative C: a browser map library (MapLibre, Leaflet) with client-side layers

**Rejected because:** it fetches tiles and cells from the browser, which `OCR_STANDARD_hexMaps`
rule 10 and ose:ADR-033's limits forbid, and it adds a cost the free-forever guardrails
(fleet:ADR-006) do not budget for.

## Consequences

### Positive

- A new map anywhere in the fleet is a config, not a new renderer: pick layers from the registry,
  name the audience, and the privacy rules come with it.
- The privacy review moves from every map PR to one table (D3) and one set of tests (D7).
- Agents read a map's stack and what was withheld from the map itself (D2), which is the owner's
  goal for the layer map.
- OA deployments, OSG game nights and OW stations get the layer map without new map code.

### Negative

- OSE's landing and SharedReport maps must move onto the component without changing what they
  draw; their exact-markup specs and goldens will change in those PRs.
- The hub package becomes a dependency every map surface must keep current.
- The D3 table is now the rulebook for maps alongside `OCR_STANDARD_hexMaps`; a change to either
  must update both.

## Proposed rollout

1. **This ADR.** The owner settles O1 and O2.
2. **The component** in the chosen home: registry, config check, renderer, metadata, step-through
   script, the D7 tests. The `HexMap` mock-up is marked as a design reference only.
3. **OSE SharedReport** moves onto it first: its layer stack (ose:ADR-041) already uses this
   registry's ids, steps and classes.
4. **OSE landing and zoomed area** move onto it with no visible change.
5. **`/api/v2/map/areas`** also returns geometry layers (corridors, nodes, towns) as parts, so the
   OW showcase can pick them; OER's shapes-only public layer is synced into OSE as the source.
6. **OA and OSM** templates carry a default surface config, so a new deployment starts with the
   map. OSG's bocce nights use it when OSG has pages.
7. **Venue thumbnail** (surface 5): a separate decision later on whether a base-map tile of the
   event's area replaces the billed Google image.

## References

- `docs/standards/OCR_STANDARD_hexMaps.md`
- fleet:ADR-006, fleet:ADR-008, fleet:ADR-010, fleet:ADR-011
- ose:ADR-017, ose:ADR-025, ose:ADR-026, ose:ADR-033, ose:ADR-035, ose:ADR-036, ose:ADR-041 (OSE draft PR 1557)
- `@ocr/ui` guidelines `30-uec-and-maps.md`, `60-map-archetypes-and-venues.md`,
  `70-pre-maps-and-rotating-displays.md`
- OER draft PR 6 (`ncr/layers.py`, `tools/prototype/ncr-layer-map.html`)
