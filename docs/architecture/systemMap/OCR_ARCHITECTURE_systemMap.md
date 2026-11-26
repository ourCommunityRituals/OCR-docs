# OCR system map

A clickable map of the whole ourCommunityRituals system: the products and the
allowed links between them, who it serves, the shared pieces every event uses,
and how a change reaches staging. It was built on 25 Nov 2026 so the owner can
see the system instead of holding it in his head, and updated on 26 Nov 2026.

- **Open it:** use the private artifact link the owner keeps. The page itself
  is not stored in this repo: it carries its own colours and stylesheet, and
  OCR-docs must hold no design of its own (the design-system check, ADR-008).
  The page template and the built page live with the owner's project files,
  in `transcripts/map/`.
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
   page names a real box and every status exists.
3. Commit the JSON here, copy it to `transcripts/map/` in the project files,
   run `python3 build-map.py` there (where `template.html` sits, so it also
   writes `infrastructure-map.html`), and republish that page to the owner's
   artifact link.

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

### Audience presets: Sales, Product, Engineering

`audiences` in the JSON names, for each audience, the pages to show in order,
the boxes and links to tap while talking, and the one-line point to make. A
deck or dashboard can read it; the page itself does not use it yet.

The Sales view and any coverage dashboard communicate functionality to the
end user, not details (owner, 26 Nov 2026): what the system does and where it
is available. They never name the places, people, sponsors or contacts on a
launch-target list, and show no counts or technical detail. Target lists stay
private and out of this repo.

| Audience | Pages, in order | Tap these | The point |
| --- | --- | --- | --- |
| Sales | `#people`, `#pieces` | Curated playlists, Skins, UEC codes, SharedReport, Voting, ourAirwaves | What the system does for each customer and where it is available, in plain words |
| Product | `#products`, `#pieces`, `#people` | ourSharedEvents, ourWKRP, ourAirwaves, Curated playlists, Voting, Skins, Layout rule | What exists, what is decided but not built, and which shared pieces every product reuses |
| Engineering | `#runs`, `#products` | T0 Gate, Done, Production, Live switch, OSE Worker, Security gates, links E1, E6, E7 | How a change reaches staging, and the allowed links and their privacy class |

## Files

| File | Role |
| --- | --- |
| `infrastructure-map.json` | The data: nodes, edges, views, statuses, audiences |
| `build-map.py` | Checks the JSON; builds the page where `template.html` is present |
| `template.html` (project files only) | The page, with a placeholder for the data |
| `infrastructure-map.html` (project files only) | The built page (generated; do not edit by hand) |
