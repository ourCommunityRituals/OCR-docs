# PROPOSAL — ourAirwaves becomes the self-serve app

**Status:** proposed, not doctrine. Lives in `docs/proposals/`, so it does not propagate to spokes.
**Proposed:** 2026-11-25 · **Owner:** Matt · **Decisions needed:** D1 to D6 at the end.

## 1. What Matt asked for

Matt, 2026-11-25: ourAirwaves (OA) becomes the self-serve application. A user gets an account there
and some control over the front end of their pages, on both ourSharedEvents (OSE) and ourWKRP (OW).
More and more people expect to take control of their product without waiting; OCR provides the rails.

Matt, same day, on fees: fees unlock more posters, more kinds of configuration and higher SharedReport
levels. The free levels are generous on purpose, to get businesses up and running.

## 2. OA's role, before and after

| | Before (CLAUDE.md, April 2026) | After (this proposal) |
|---|---|---|
| What OA is | Deployment and white label: fork template, onboarding runbook, per-client environment schema. Documents only. | The front door. One account where a business, venue, creator or organizer sets up how its pages look on OSE and OW, inside fixed rails. |
| Who uses it | Matt or a solution engineer, setting up a client | The client, on their own phone or laptop |
| Code | None | A small app of its own: account, tiers, a look editor, a preview |

The old role does not disappear. A full branded fork stays the top of the ladder (the Enterprise row
in OA's CLAUDE.md), and OA is still where it starts. Self-serve is the common path; a fork is the rare one.

The OSM + OA flywheel in `OCR_VISION.md` still holds: OSM documents how, OA is where people do it.

## 3. The account model

- **An OA account is a named account.** OA already sits on the named side in `data-edges.yaml`
  (`oaw: side: named`). The account holds a sign-in and the business it acts for. Nothing more.
- **An account owns one or more brands.** A brand is what OSE and OW already call it (`brand_id`).
  A brand may be OSE only, OW only, or both (Matt, 2026-11-25: every client can skin, whichever products
  it uses).
- **Roles inside a brand:** owner (billing, people, everything), editor (looks and layouts), viewer.
  These are OA's own; they do not change OSE's or OW's admin roles.
- **OA never holds attendee data.** No scan, check-in, vote, registration or email sign-up of the
  public ever reaches OA. OA configures pages; it does not read what people do on them.
- **The anonymous side never learns who the OA user is.** OSE sees a brand id, an OA service token and
  an opaque OA actor id for its audit log. It never receives a name or an email from OA.

## 4. How OA drives OSE and OW: APIs, never a shared database

OA calls each product's own HTTP API with a service token scoped to one brand. Each product stays
the only writer of its own database and keeps its own checks. This is the same pattern as the existing
seams E6 and E8 (a fail-closed service token), and it keeps invariant #22 (no module imports across
products; `@ourairwaves/...` imports are already on its blocked list).

The engines stay where they are, because the rules live there:

| Product | Engine (already built) | API OA would call |
|---|---|---|
| OSE | `lib/layout-skins.ts`, `lib/layout-skin-md.ts` (PR ourSharedEvents#1555) | `GET`/`PUT /api/v2/admin/events/:id/layouts` (skin .md); `GET`/`PUT /api/v2/admin/addons` (today platform only) |
| OW | `lib/layout-skins` and the profile layout (PR ourWKRP#139) | `GET`/`PUT /api/profile/layout` (skin .md); `POST /admin/skins/grant` (today admin token only) |

Each product still parses and refuses a skin itself. OA's editor is a client of those checks, so a
look OA sends that breaks a rule is refused by the product with the same message the product's own
editor shows. OA cannot loosen a rail, because it never holds one.

New API work this needs, in each product, before OA can call it:
1. A **brand-scoped OA service token** (a new `oa` actor class), separate from the platform admin key.
   It may read and write looks and limits for the one brand it names, and nothing else.
2. A **brand-level** layouts read and write on OSE (today it is per event). Per-event looks remain.
3. A **limits** write (section 6) that replaces the single on/off add-on.

## 5. What happens to the two editors (PRs 139 and 1555)

**They stay, as the engines and as the staff tools.** Recommended path:

- **Step 1 (front door):** OA signs the user in, shows their brands, tier and limits, and opens the
  existing editor for the chosen page: OW's `/look`, or OSE's Page layouts card. Nothing is rebuilt.
- **Step 2 (one editor):** OA gets its own editor that writes the one shared skin .md format through
  the APIs above, for every surface of both products, with a live preview. The product editors stay for
  Matt and solution engineers (and for Bruno hand-edits, per the skins model).
- **No third format and no second rule set.** The skin .md format (one block per surface, `surface:`,
  `skin`, `columns`, `order`, `wide`) is the only format. Each surface keeps its own parts, marked
  required or optional; layouts never carry across surfaces, only the abstraction does.

## 6. Tiers and limits (replacing the single skins add-on)

Today each product has one switch: OSE `brand_addons` ('skins') and OW `custom_skins`. Matt's fee
direction needs levels with limits instead. Proposal: OA holds each brand's tier; OA writes the
resulting limits to each product through the API; each product enforces its own limits and, if it
has never heard from OA, uses the Free limits (fail closed to the generous floor, never to nothing).

Starting limits, **for Matt to confirm** (all numbers are a first guess):

| Lever | Free (generous) | Mid | Premium |
|---|---|---|---|
| Poster designs saved per brand | 10 | 50 | No set limit (fair use) |
| Kinds of configuration | Standard look plus every ready-made look, on every surface | Plus custom arrangements: move parts, hide optional parts, save up to 10 own looks per surface | Plus a look per event, one .md file across OSE and OW, and hand edits by us |
| SharedReport level | Level 1: the report page after each event | Level 2: PDF, interactive report, sponsor view, map | Level 3: cross-corridor trends and insights (OER) |
| Brands per account | 1 | 3 | No set limit |
| People per brand | 2 | 10 | No set limit |

Things that are **never** tier-gated, at any level (invariants #5, #7, #8, #9, #24, OSE AGENTS.md 7):
security, audit, isolation and retention; the under-5 floor ("Fewer than 5", never a smaller number);
contrast and colours (design tokens); the required parts of each surface; plain titles and UEC colours
on every code.

Note the conflict with today's `ocr-docs-brain/tier-gates.yaml`: its Free tier has
`shared_reports: false`. A generous Free with a Level 1 SharedReport would change that file (D4).

## 7. New links for the link list (`data-edges.yaml`)

Added in this PR as `status: proposed`. None is built. They name what crosses and how private it is.

| Id | From → to | What crosses | Privacy class |
|---|---|---|---|
| E11 | OA → OSE | A brand's looks (skin .md), its tier limits, and an opaque OA actor id for OSE's audit log. No name, no email. | A |
| E12 | OA → OW | A brand's or contributor's looks (skin .md) and tier limits. | B |
| E13 | OSE → OA | Read back: the brand's current looks and how much of each limit is used (for example 7 of 10 poster designs). No attendee data and no attendee counts. | A |
| E14 | OW → OA | Read back: the brand's current looks and limit use. | B |

The privacy covenant holds by construction: OA reads configuration and usage of the brand's own
allowance, never people. A SharedReport stays on OSE behind its own floors; OA links to it and does
not copy its numbers. If OA ever shows a count from a report, that is a new edge and needs its own row.

E11 to E14 are not OSE–OW edges, so invariant #22's `permitted_seams` check is unchanged.

## 8. Order of work (after the decisions)

1. OCR-docs: this proposal agreed; E11 to E14 confirmed; OA's CLAUDE.md, README and product registry
   rewritten for the new role (governance PRs, human review).
2. OSE and OW: the `oa` service token, brand-level looks API, and limits in place of the on/off add-on.
3. ourAirwaves: the app (Cloudflare Worker + D1, the hub's design system), step 1 front door.
4. ourAirwaves: step 2, its own editor with preview.

## 9. Decisions for Matt

- **D1 Account home.** Recommended: OA owns the business account and sign-in for both products.
  Alternative: each product keeps its own sign-in and OA only links them.
- **D2 Editors.** Recommended: keep the two editors as engines and staff tools; OA opens them first,
  then grows its own editor on the same format.
- **D3 Tier limits.** Confirm or change the starting numbers in section 6.
- **D4 Free SharedReport.** Recommended: Free includes Level 1 (the report page), which changes
  `tier-gates.yaml`.
- **D5 Ready-made looks on Free.** Today any look other than the standard one is paid. Recommended:
  ready-made looks become free, and custom arrangements are what Mid buys. Generous to start.
- **D6 Where limits are enforced.** Recommended: each product enforces its own, written by OA; with no
  word from OA a product uses the Free limits.

*Sources: ourAirwaves CLAUDE.md; ourSharedEvents PR #1555 and ourWKRP PR #139 (routes read from their
router diffs, 2026-11-25); `ocr-docs-brain/data-edges.yaml`; `ocr-docs-brain/tier-gates.yaml`;
`architectural-invariants.yaml` #22.*
