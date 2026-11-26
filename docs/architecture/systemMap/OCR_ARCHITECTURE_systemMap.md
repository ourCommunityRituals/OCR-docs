# OCR system map

A clickable map of the whole ourCommunityRituals system: the products and the
allowed links between them, who it serves, the shared pieces every event uses,
and how a change reaches staging. It was built on 25 Nov 2026 so the owner can
see the system instead of holding it in his head, and updated on 26 Nov 2026.

- **Open it:** download `infrastructure-map.html` and open it in a browser, or
  use the private artifact link the owner keeps. GitHub shows HTML as source,
  not as a page.
- **Source of truth for the map:** `infrastructure-map.json`.
- **Scope:** only the ourCommunityRituals org repos. americanbocceco,
  zeventbook and MVP-EVENT-TOOLKIT are history only and stay off the map.

## The four pages

| Page | What it shows |
| --- | --- |
| The products | The anonymous side (ourSharedEvents, ourSharedMagnets) on the left, the plant-your-flag side (ourWKRP shown as ourSharedMosaics, ourAirwaves, curated playlists) on the right, OCR-docs and the hub on top, the formats and on-ramps below, and every allowed data link |
| Who it serves | Attendees, organizers, sponsors, venues, neighbourhoods, creators, partners, leagues, and what each gets |
| Shared pieces | Skins, the layout rule, UEC codes, posters, TV screens, voting (Room Pick, Online Pick, Access Pass), SharedReport, the under-5 rule, the map, curated playlists |
| How it runs | Pull request, T0, merge, T1 to T4 on staging, Done, production and the live switch, Cloudflare and data, guards and the work list |

Tap any box or line to see what it does in plain words, its status, and the
source of each fact.

## How it relates to the brain

The product-to-product links (E1 to E14, C1, G1) copy
`ocr-docs-brain/data-edges.yaml`. That file is the source of truth for links;
this map only draws it. When `data-edges.yaml` changes, change the matching
`edges` entries here. Rule counts and statuses on the map are read from the
repos on the date in `meta.checked`; the code and the brain win when they
disagree.

## How to update it

1. Edit `infrastructure-map.json`:
   - `nodes`: one entry per box (label, short sub-line, plain description,
     status, details, sources).
   - `edges`: one per line.
   - `views`: which boxes and lines appear on each page, and where (x, y on
     the page grid).
   - `statuses`: the status words and colours.
   - `meta.checked`: the date the facts were last checked.
2. Run `python3 build-map.py` in this folder. It checks that every line and
   page names a real box and every status exists, then writes
   `infrastructure-map.html`.
3. Commit the JSON and the rebuilt HTML together, and republish the HTML to the
   owner's artifact link.

`template.html` holds the page's look and behaviour; `build-map.py` puts the
JSON into it. The page needs no server and loads only fonts from Google Fonts.

## Reusing it for dashboards and presentations

The owner plans to reuse the map for dashboards and for business and
engineering presentations. It is built so that is easy:

- **Open one page directly.** Add the page name to the link: `#products`,
  `#people`, `#pieces` or `#runs`. A deck or dashboard can link straight to
  the page it needs.
- **Slides and screenshots.** Each page fits one screen on a laptop. Open the
  page, tap the box you want to talk about so its links light up, and take a
  screenshot. The page follows light and dark mode, so pick the one that
  matches the deck.
- **The data on its own.** `infrastructure-map.json` has no layout code in its
  `nodes` and `edges`. A dashboard, a slide tool or a script can read those
  directly (for example, count products by `status`, or list every data link
  with its `privacy` class). Positions live only in `views`, so a new page for a
  talk is a new entry in `views` that reuses the same nodes and edges.
- **Keep one source.** Add facts to the JSON, not to a copy inside a deck, so
  every view stays in step.

## Files

| File | Role |
| --- | --- |
| `infrastructure-map.json` | The data: nodes, edges, views, statuses |
| `template.html` | The page, with a placeholder for the data |
| `build-map.py` | Checks the JSON and builds the page |
| `infrastructure-map.html` | The built page (generated; do not edit by hand) |
