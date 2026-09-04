# Content-market fit — OCR hub · OSE foundation · OW spoke vs. the three pain points

**Date:** 2026-09-03 · **Owner:** Matt · **Status:** DRAFT — assessment, not doctrine
**Source research:** [`OCR_REFERENCE_contentMarketFitResearch.md`](OCR_REFERENCE_contentMarketFitResearch.md) (Sept 2025 – Sept 2026 sentiment study, three pain points)
**Home:** fleet discovery hub — the finding spans OCR (front door), OSE (engine), OW (named pole).
**Rule applied:** code wins over docs; anything asserted below that is not in code or `OCR_VISION.md` is marked as drift or decision.

---

## 1. Verdict in one screen

The three pain points the research validates are the same three problems the Launch Front Door epic (Linear OCR-115 / OCR-116, ratified 2026-08-29) already names as the page's opening section. The research is the receipts that ticket asks for. Fit by pain point:

| Pain point (research rank) | Where the answer lives | Fit | The one gap |
|---|---|---|---|
| **#3 Surveillance / false choice of consent** (strongest) | OSE anonymous-by-architecture: two databases, CI invariant gates, `ose_anon` contract, K=5 count floor, honesty lexicon, the anonymity affordance shipped on `/` and `/events`; OW's `no_biometric_identifiers` BIPA absence gate (PR #48 — shipped as a CI gate; its invariant number is unratified, see §9) | **Strong — this is the architecture's native message** | The live landing hero is still generic ("Community events that bring people together"). The privacy anchor sits below the fold. Already flagged as open question 3 in the 2026-08-29 brand discovery report. |
| **#1 Local connection / third places** (strong, rising) | 47 Phase-1 event types in `event_type_registry` (OSE migration 0024) and `ocr-docs-brain/event-taxonomy.yaml`, 8 categories, each UEC-colored. Block parties, potlucks, run clubs, book clubs, game nights, open mics, garden workdays: the third-place inventory, verbatim. | **Strong on inventory, weak on surface** | The attendee discovery surface is designed, not built (hybrid brief §6; OSE-1014, OCR-114 in Backlog, sequenced post-launch). `corridors` has 0 rows and the density census (OSE-804) is unrun. |
| **#2 Small business priced out** (moderate-strong) | Share covenant: money buys rotation frequency only, never size, slot, or position; local businesses hold a guaranteed rotation floor and cannot be outbid; Local sponsor tier is $0 forever; Tier Equity invariant #5; corridor targeting instead of people targeting ("buy the corridor, not the contact list"). | **Strong, and stronger than the research asks for** | The research's Stage-3 proof is "local businesses pay a modest flat fee." OSE's covenant makes the corner store free forever; paid revenue comes from hosts and non-local (Regional / Premier) sponsors. The message and the pricing plan must say the same thing. See §4. |

Net: the platform matches the message. The site does not yet say so, and the discovery promise is ahead of the data.

---

## 2. Pain point by pain point, against code

### 2.1 Surveillance — the hook

What exists, in code or CI:

- Two physically separate D1 databases (`DB` / `FORMS_DB`), no cross-database joins, static invariant gate in CI (OSE ADR-001, ADR-002).
- Scans store hour buckets, no IPs, hashed non-reversible fingerprints (hybrid brief §2).
- SharedReport K=5 floor server-side; sub-floor rows dropped; floor declared in the payload.
- Honesty lexicon lint: "attendance, impressions, reach, unique, people, views" are banned words on report surfaces.
- The anonymity affordance, live on `/` and `/events` since 2026-08-29 with four regression guards (`tests/brand-voice-surfaces.spec.ts`).
- OW: the `no_biometric_identifiers` BIPA absence gate — the anchor OCR-116 wants on the page is already a CI check (`tests/security/no-biometrics.invariant.test.ts`). Its invariant number is unratified; see §9.
- Discovery design law (OSE-1014, OSE-1015): responses are a function of (cell, k, filters), byte-identical for every requester; the area is picked, never detected; tourism mode is a toggle, not detection.

How this maps to the research's copy guidance:

- The research's guardrail is "privacy as a gain, not a sacrifice." The hybrid brief already states the same rule: "Copy is load-bearing and plain. The privacy promise is stated as fact where it applies, in situ." The two documents agree.
- The research's recommended arc, "resignation to relief," is the epic's ratified page architecture: problems → relief → product → doors → proof.
- Research phrase "you're being tracked right now" has an honest OSE counterpart already in production: "Nothing about your device, location, or identity was collected to display this page."

Gap: hero copy. The hook the research ranks first is the one element the live page leads with least.

### 2.2 Third places — the promise

What exists:

- 47 event types seeded and tested (`reg1-event-types.spec.ts` asserts exactly 47). Eight taxonomy categories: Community Rituals 7, Music & Culture 8, Games & Recreation 6, Food & Drink 6, Wellness & Health 5, Youth & Education 5, Civic & Commerce 5, Seasonal & Special 5.
- Every type joins to an event template (`template_event_types`, migrations 0056/0057) and every template ends at a poster with UEC codes. A type is not a label; it is a runnable ritual with a printable door.
- The research's own third-place examples (board game nights at breweries, run clubs, community gardens, book clubs) are all Phase-1 types. No permit required. That is the research's "grow, not find" thesis, as a schema.

What does not exist:

- A "What's on" surface. The hybrid brief lists it under "Designed, not built." OSE-1014 (corridor discovery), OSE-1015 (tourism mode), OCR-114 (Pulse Map) are all Backlog and deliberately sequenced after launch: "density precedes discovery."
- Density. OSE-804 (one hour, no code) has not been run. Until it is, nobody knows whether a Beverly week uses 5 types or 40.

Drift to flag: `docs/positioning/COMPETITIVE-BRIEF-2026-05-14.md` says "Discovery is zero … Discovery isn't OSE's job." OCR-114 (2026-08-29, Matt's decision) places the discovery map in OSE as the base layer. The August decision supersedes the May brief; the brief should be amended so the front door does not inherit the old line.

Count to flag: the working number is **47**, not 50. VISION.md, the taxonomy YAML (`total_types_v1: 47`), migration 0024, and the reg1 test all agree. Copy may say "nearly fifty"; documents should say 47.

### 2.3 Small business — the proof

What exists:

- Share covenant (built, per hybrid brief §8): every sponsor renders identically; local status is geo-derived from the corridor cell and is never purchasable.
- Allocation weights 7× / 3× / 1× with a 30% local floor and locals-first ordering (`sponsor-allocation.ts`, drift-checked byte-for-byte against `ocr-docs-brain/sponsor-allocation.yaml`).
- Two-sided acceptance: either party proposes a placement, the other accepts; a decline is durable.
- Pricing plan (COST-112): Local $0 forever; Mid $25–75 per event or $99/mo; Premier $149–199/mo. All of it sits under the research's CTV minimums ($2,000–3,000/mo) and outside the CPM inflation curve.
- The SharedReport answers the sponsor's honest question, including "are local organic advertisers out-performing paid spend?"

**Decision (Matt, 2026-09-03):** Local splits three ways by who is sponsoring, and "Local $0 forever" stays for the first of them.

| Local sponsor | Price | Keyed on |
|---|---|---|
| Community use: a block party host, a neighbor, a community group, a league, a charity | $0 forever (the existing row) | `sponsor_business.business_type` in the non-commercial set (community_org, charity, nonprofit, league_org, sports_club; faith_org already free by brain rule) |
| Established local business (the barber) | Small flat fee | commercial `business_type` (bar, brewery, retail, restaurant, professional_services, photographer, corporate) |
| New local business, license issued within the last 12 months | First placement free, then the flat fee | commercial `business_type` + a self-attested license issue month (new field) |

What the decision does not touch, because it lives in code or the brain and governs prominence, not price: the 30% local floor and locals-first ordering (`sponsor-allocation.ts`), the 7× / 3× / 1× weights, `local_always_present` and `faith_always_free` in `tier-gates.yaml`, and Tier Equity (invariant #5). Money still buys frequency only. The mechanism doc (`SPONSOR-PRICING.md`) already said the Local price point is a go-to-market decision; this is that decision.

Read against the research: this is now the exact Stage-3 proof the research asks for (local businesses pay a modest flat fee to reach a verified local audience without tracking), with a sharper opener for the newest businesses. The pain-#2 line on the front door becomes: opened this year, your first ad is free; after that it's cheap, it's your own corridor, and nobody can outbid you for it.

---

## 3. The three repos in the design

| Repo | Role on the front door | Ready? |
|---|---|---|
| **OCR hub** (`OCR-docs` + `ourCommunityRituals` monorepo) | Owns the page architecture (OCR-115), the copy (OCR-116), the trust story (OCR-118), and the design system: `@ocr/tokens` (brand axis `ose · ow · client`, surface axis `console · public · tv · poster`) and `@ocr/ui` partials. | Design system exists and is tested. Copy has not been written. OSE-231 "harmonize landing to OCR design system" is Backlog. |
| **OSE foundation** | Hosts the page. The epic says "new waves = new doors on the same page, never new sites." The site is `oursharedevents.com` `/` (`src/templates/landing.html`) until a decision says otherwise. Engine for the product section; the 47 types; the poster; the SharedReport. | Landing exists with anonymity affordance, six-node ring, email capture. Hero and feature cards are generic. Mobile workability drain (OSE-299) open. |
| **OW starting spoke** | The named pole. Proves The Choice is real: OSE counts the room, OW puts your name on what you bring, and the two never join. Wave-one door on the page. Fist of Five is the third-place ritual example with a season. | Register-first auth, vanity slugs, OG meta, BIPA gate all shipped. The connect page carries no privacy copy at all ("Bring Your Music / Browse the Catalog" only). If OW is a door on a privacy-led page, its own front step needs one sentence: browse without an account; your name goes only where you put it. |

The OW nuance the research supplies: Gen Z is the most privacy-anxious cohort and also the most willing to trade data for a better experience. The 5-rung consent ladder (Listener → Contributor → Curator → DJ → Crew) is the product answer to that paradox. It should appear on the page as the "here's what a real choice feels like" beat, not as a feature list.

---

## 4. Decisions the research forces

1. **Hook order.** The research ranks surveillance as the hook, connection as the promise, business as the proof. OCR-116 orders the problems connection → business → surveillance. Recommendation: keep OCR-116's problem section in the visitor's words, but make the hero the surveillance-relief line. The two are compatible. The research's Stage-1 benchmark (privacy-led vs local-led engagement) can be run by time window, not by requester, so the byte-identical-per-cell rule holds.
2. **The Local price. Decided 2026-09-03:** Local $0 forever stays for community use (block party, neighbor, community group); an established local business pays a small flat fee; a business licensed within the last 12 months gets its first placement free. Three sub-decisions remain, each with a recommendation in Linear OSE-1198: the dollar figure for "cheap" (hypothesis: a flat monthly number under Mid's $25–75 per event); the unit of "first placement" (recommend one event template + one area for one cycle); and whether the Local tier sits on the pricing plan's 3-month free flip at all (recommend no: Local is cheap from day one, and the new-business credit is the only Local free window, so the two rules never stack). Schema note: the community/business split derives from the existing `business_type` field; only the first-year credit needs a new self-attested license issue month, never the license number.
3. **47, presented honestly.** Show all 47 types as what a host can run (the spiderweb is a "bring your ritual" picker), not as what is on tonight. The attendee view of the same web inherits OSE-1014's honest activation state: "this area hasn't lit up yet" plus plant-a-flag. Run OSE-804 first; it decides whether the web renders 8 categories or the top handful.
4. **Domain.** The epic implies one page with doors. It does not name whether that page is `oursharedevents.com` or an OCR-branded domain. Record the decision in VISION §10 before design starts.
5. **Surface count.** VISION says six OSE surfaces; the hybrid brief says five; OCR-114 calls the map the sixth. One number, one home.

---

## 5. Recommended path to a site design

Ordered. Each step names the skill or connection best suited to it. Steps 1–3 are copy and data; nothing visual should start before them, per the epic's "copy first, design second."

| # | Step | Best tool | Output |
|---|---|---|---|
| 1 | Attach the research to OCR-116 as its receipts; add the hook-order and Local-is-free decisions (§4.1, §4.2) to the ticket. | Linear connector; `/story` skill for any new child | OCR-116 has its evidence; two decisions queued for Matt |
| 2 | Run the density census (OSE-804). One corridor, one week, four numbers. | Airtable or a plain sheet; no code | Whether the spiderweb is 47 nodes or a top-N with 47 available |
| 3 | Write the page copy: hero, three problems, relief, product, doors, trust, footer. Obey `.claude/brand-voice-guidelines.md` (voice constant, anti-promises, no "flywheel"), the honesty lexicon, and OSE-1011 least-mental-tax (one idea per screen, the single More control for depth). | `/ccr` gate the copy at ≥95% before design; the OSE brand-voice enforce skill named in the guidelines | Copy draft that can be lifted straight into HTML (the OSE-268 shape) |
| 4 | Design canvas: mobile-first 390 px, dark default, `[data-brand=ose]` `[data-surface=public]` tokens from `@ocr/tokens`; UEC hues never re-themed. Artboards: hero · three problems · relief · Triangle · the 47-type web · doors (OSE, OSR, OSG; wave slots OW, OA) · trust · footer with the anonymity affordance. Empty and below-floor states designed first. | `/design` (Claude Design canvas — the dependency OCR-115 names); `/dataviz` for the category web and any count tiles; `/artifact-design` for the review page | Reviewable, editable artboards |
| 5 | Build it in `landing.html` using `@ocr/ui` partials and the shared stylesheet (closes OSE-231), with mobile workability (OSE-299) and regression guards extended from `brand-voice-surfaces.spec.ts`. | OSE repo; Cloudflare connector for staging verification | The page live on staging behind the existing CI pyramid |
| 6 | Reconcile drift surfaced here: competitive brief "discovery isn't OSE's job"; 50 vs 47; five vs six surfaces; domain. File one story per inconsistency at its home. | `/brain-check`, `/story`, this document | Zero inconsistencies between brief, VISION, and the page |

### 5.1 The 47-type spiderweb, specifically

- **Structure:** eight spokes (the taxonomy categories, each in its UEC category color with a word label, never color alone), 47 nodes on the spokes, the corridor ring (the six founding nodes) around the outside. Ring ⊃ Corridor ⊃ Node ⊃ Event, drawn.
- **Host reading:** tap a node → the event template → "print the poster." Every spoke ends at a QR door. That is "predominantly serving the community": the web is a menu of things a neighbor can run this month, not a catalog of things to consume.
- **Attendee reading:** the same web, filtered to what is published in the picked area, with OSE-1014's widen-the-ring and honest-activation rules. Below floor, a node reads "not here yet — bring one," never an empty shelf.
- **Sponsor reading:** a business subscribes to an event template + area (two-sided acceptance, built). The spoke is the SKU. The covenant line sits beside it: local businesses are matched by corridor and never outbid.
- **Honesty:** a node with no published events in the picked area is drawn dashed (the "claimed / dormant / planned" convention from the hybrid brief §11), solid only when counted.

---

## 6. What this assessment did not verify

- No Chicago-specific grassroots signal was in the research; the research itself flags this. The Founding Six corridors are asserted from VISION, not from field data.
- OSE-271 (five bar-owner interviews) is marked Done in Linear, but no findings file was read for this assessment. Fold its findings into step 3 copy.
- The `/brand-voice:enforce-voice` skill is referenced by the guidelines; its presence in the OSE repo was not confirmed here.
- Whether the Front Door is meant to live at an OCR-branded domain is not recorded anywhere read.

---

*Written 2026-09-03 on branch `claude/content-market-fit-site-design-1lj7j8`. Source of truth remains `docs/OCR_VISION.md`; this file is discovery evidence, not doctrine.*

---

## 7. Pricing-plan vision (captured from Matt, 2026-09-03)

Recorded here so the thread survives; the ticket of record is OSE-1198.

**The unit is the activity, not the organization.** A church is free all the time for its own community services. If the church runs something truly for profit, that activity cannot ride the free plan; it takes a for-profit plan like anyone else. Same entity, two plans, no contradiction. Qualification is mutually exclusive per placement, never per letterhead. (Drift: `tier-gates.yaml` "faith_always_free" and ADR-006 read as entity-level; amend to host-side platform access, with sponsor placements priced by class regardless of who buys.)

**A pricing plan is an object, and an entity can hold several.** Price (zero, flat, per cycle) · term (this event, a period, open-ended) · eligibility as facts on the record (entity type, license age, corridor match, nature of the activity) · exclusions · adjustments. "Free forever for the block party" and "first placement free for a first-year business" are plans with price zero and a term, not special cases.

**Year one scope:** pricing plans, the ability to apply for one, the free plan, and the first-year credit. Nothing else.

**Later (explicitly deferred):** discount grammar — kind (flat, percent, fixed price) · amount · cadence (once, every cycle, every other, a named cycle) · window (six months of plan A, then plan B) · stacking · scope — then coupons and rebates. The catalog becomes brain YAML with a resolver `(record, placement, date) → price`, proven by a fixture matrix in CI while billing stays inert (invariant #6). Computing a rebate at runtime is the line where billing stops being inert and needs an ADR. The pricing plan's "quarantined billing-clock" is the time axis those windows will need.

---

## 8. Reassessment against staging (2026-09-04, same prompt, same research)

**Staging build:** still `stg-11ed7a5-20260903`. Nothing from branch `claude/content-market-fit-site-design-1lj7j8` (12 OSE commits, 7 OCR-docs commits, no pull request) has merged, so the live site is byte-for-byte the site the first pass reviewed. Re-probed: poster CSP still has no img-src; hero still generic; four Tailwind-blue values on the landing; one post-event event still listed with Register; `/sharedReport` still raw JSON 403 to a browser; no consent line on the display; poster QR still greyscale with no `uec` in the bundle.

**Fit verdict, live vs. branch:**

| Pain point | Live staging today | On the branch (unmerged) | Decided, not yet built |
|---|---|---|---|
| #3 Surveillance (hook) | Strong in architecture; anchor below the fold; TV silent | TV consent line; poster prints consent tier per code; recap no longer claims "attendance" | Hero hook order (OCR-116) |
| #1 Third places (promise) | 47 rituals in schema; no surface shows them; list phase-blind | List is phase-aware | Density census (OSE-804); the 47-ritual web; discovery rails (OSE-1014) |
| #2 Small business (proof) | "Local $0 forever" in plan; puffery card on landing | Pricing plan carries the three-way Local split (OSE-1198) with doc guard | Flat-fee number; 3-month-clock ratification; license month (OSE-1207); the apply door |

**What changed since the first pass, all off-staging:** seven tickets filed and reconciled (OSE-1198–1207 minus none; 1204 folded under 818), six defects fixed with tests, three drift items fixed with tests, pricing decision recorded, front-door copy handed to OCR-116, staging walkthrough published. **What did not change:** the user-visible site. The gap between "fixed" and "live" is one pull request per repo.

**Reassessed path to the site design (unchanged in order, sharper in status):**
1. Merge the branch (PR + CI) so staging shows the fixes before any demo.
2. OSE-804 density census — still the gate for how many of the 47 the web renders.
3. OCR-116 copy from the 3×3 grid (§ above), hero hook order decided.
4. Design canvas on `@ocr/tokens` — the accent question is now settled (platform indigo, OSE-221).
5. Build into `landing.html` with the scan-path guard suite extended.

---

## 9. Drift found by the phantom gate (2026-09-04) — Article #27 is claimed twice

Writing §2.1 above, I cited OW's BIPA gate by a registry number taken from its commit subject. The OCR-docs phantom scanner rejected it on PR #112, correctly: **the registry holds 1–25; there is no Article #26 or #27.** Chasing the number surfaced a genuine collision, not just a bad citation:

| Claimant | What it calls Article #27 | State |
|---|---|---|
| `docs/proposals/PROPOSAL_invariants-26-27-mutual-acceptance-honesty-lexicon.md` | **Honesty Lexicon** (with Article #26 = Sponsor Placement Mutual Acceptance) | Proposed, unratified |
| ourWKRP, PR #48 | **`no_biometric_identifiers`** (BIPA absence gate) | **Shipped** — `tests/security/no-biometrics.invariant.test.ts`, `tests/support/biometric-scan.ts` |

Two different articles both claim the number, and one of them is already enforced in a spoke's CI. The proposal additionally plans to re-cite OSE's honesty lexicon from Article #25 to Article #27, which would collide head-on with the shipped OW gate.

This is precisely the failure ADR-003 names — numbers asserted before the registry encodes them, the same mechanism that produced the earlier phantom pair. The brain must assign both numbers, and one claimant must renumber. Filed for resolution; nothing in this assessment depends on which number wins, only on the gates existing, which they do.

*(Note on phrasing: unratified articles are written "Article #N" throughout, matching the proposal doc's own convention — the scanner reserves the literal "invariant #N" form for registry-encoded articles, which is the point of the gate.)*
