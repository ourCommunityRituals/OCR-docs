# Staging walkthrough — every OSE surface against the message (2026-09-03)

**Build:** `stg-11ed7a5-20260903` · **Method:** headless Chromium 141 at 390 / 1280 / 1920 px, mobile-workability measurements (scroll width, touch targets, input font size, CTA above fold), source verification for every defect · **State of staging:** one seeded event (post-event phase), zero sponsors, free tier.
**Visual version with screenshots:** published as an Artifact from this session (link in the session summary).
**Companion:** [`OCR_REFERENCE_contentMarketFitAssessment.md`](OCR_REFERENCE_contentMarketFitAssessment.md) · Linear OCR-115 (Front Door), OSE-1198 (pricing plans).

> **Verdict in one line:** the engine is honest, the doors are unpainted, and the poster prints no code.

---

## 1. Defects verified in source and filed

| Linear | Surface | What | Priority |
|---|---|---|---|
| **OSE-1199** | `/poster` | All four QR images refused by CSP: `securityHeaders()` in `pages.ts` has no `img-src`, so `data:` PNGs fall to `default-src 'self'`. Poster prints alt text. `demo.ts` already carries `img-src 'self' data:`. | Urgent |
| **OSE-1200** | `/poster` | Decoded QR PNGs are greyscale, modules `#000000`. No UEC hue, word, path, or consent tier on the cards. "The color IS the instruction" is not on the wall. | High |
| **OSE-1201** | `/events/:id` post-event | "75% attendance rate" — banned lexicon word; `schema-lexicon.ts` covers identifiers only, no rendered-surface gate exists. Also: empty "What this was" card when 5W fields are null; unmarked test-traffic counts (449 / 602). | Medium |

## 2. Drift and notes by surface

| Surface | Works | Drift / note |
|---|---|---|
| Landing `/` | Affordance live + 4 regression guards; CTA above fold; no h-scroll; ring renders | Hero is the generic line the research says to avoid; privacy anchor at the bottom. Three feature cards carry puffery ("real partnerships, real impact"). Ring hues arbitrary. "Admin" in public nav. No doors, no 47 rituals, no proof section (OCR-116/117/118 Backlog). |
| Events `/events` | Affordance; clean card | "Upcoming Events" + "Register" on a May 1 event whose own page says it's a wrap — list does not know the phase. No area picker (OSE-1014 Backlog, post-density). |
| Event page (post) | Best-voiced page on staging: "This one's a wrap," share, next doors, affordance with "single click" | OSE-1201. Desktop and curl get Cloudflare's "Just a moment" challenge on this path — if it reaches production, link-preview scrapers never see OG tags. Verify the bot-management rule. |
| Display (TV) | 10-foot scale, clock, ticker; sponsor slots hide cleanly when empty | ~80% empty; no "we count the room, never the person" line on the surface a whole room watches; no live count, no rotating key, no next-in-corridor strip. |
| Poster | Event picker, print button | OSE-1199, OSE-1200. Picker input 15 px on desktop (minor). |
| Forms ×4 | One-tap check-in; 44 px buttons; 16 px inputs; no h-scroll | Register and email inputs 42 px tall at 390 (under the 44 px floor). Different palette (near-black header, indigo button) from the navy landing. 70 words of GDPR under a single anonymous tap; one voice line should precede the legal block. |
| SharedReport | — | Raw JSON 403 `REPORT_DISABLED` at free tier. The proof surface is invisible on staging. Pick: raise tier, mint a signed link, or route the demo trio (OSE-606). |
| Admin | CF Access sign-in, as designed | Not reviewed past the gate. Pricing plans have no surface yet; sponsor-onboarding data model exists (migrations 0053–0068). |
| ui-preview | — | Title only at 390; desktop behind the challenge. |

Mobile-workability summary at 375–390 px: zero pages with horizontal scroll; all inputs ≥16 px; primary CTA above the fold on every page that has one; two inputs under the 44 px floor (register, email).

## 3. Where the flow lands

| Research element | Surface | Today | Needs |
|---|---|---|---|
| Hook: surveillance relief | Landing hero | Generic; anchor below fold | OCR-116 hero; affordance's first sentence promoted to the top |
| Three problems in the visitor's words | Landing §2 | Three generic cards | "Nothing to do around here" · "The little guys got priced out" · "Everything watches you now," each with a receipt |
| Relief: The Choice | Landing, forms, display | Affordance on 3 pages; nothing on forms or TV | One voice line per surface; consent tier in words on every code |
| Promise: third places, 47 rituals | Landing web, events area view, poster | Absent | 8-category web; host reading ("bring one"); attendee reading gated by OSE-1014's honest state; OSE-804 first |
| Proof: local covenant + pricing plans | Landing card, admin onboarding, one public door | Puffery card; no door; schema only | "Community free forever · first-year business first ad free · established cheap · never outbid" + apply door (OSE-1198) |
| Doors + proof of process | Landing §4–5 | Absent | OSE/OSR/OSG doors; OW/OA wave slots; OCR-118 trust story |

## 4. Release shape (research stages over OSE-942 phases)

- **Stage 0, before anyone sees it:** OSE-1199 fixed and guarded; OSE-1200 (UEC color + word/path/tier); OSE-1201; SharedReport reachable on staging; Cloudflare challenge rule checked; OCR-116 copy written and CCR-gated.
- **Stage 1, voice and validation (Phase A Jeremy + Founding Six ignition):** front door live in the ratified order; posters on real walls (RIPH, Eagles Hall, Open OutCry); one TV at one venue; privacy-led vs local-led hero tested by time window, never per requester.
- **Stage 2, seeding (Phase B AJ demo + Beverly September):** density census run; what's-on rails v1 with honest below-floor state; weekly return as the benchmark; first SharedReports earned.
- **Stage 3, monetization proof (Phase C):** pricing plans live (OSE-1198); first five local businesses set the flat fee; Mids on Layer-1 proof; civic only with receipts; discount grammar stays deferred.

## 5. Deck (12 slides, page order)

1 Bus stop on Western at 7am · 2 Three problems in your words (with receipts) · 3 The shared villain · **4 The relief: The Choice** · 5 The Triangle · 6 The wall (poster, fixed) · 7 The night (TV) · **8 The morning after (one real SharedReport)** · 9 The web (8 categories, 47 rituals, 6 corridors) · **10 The corner store is never outbid** · 11 Why you can believe this (OCR-118) · **12 Doors and the ask.**

Cuts: hosts 1–9 + 12 (slides 6–7 are the pitch); sponsors 2, 4, 8, 10, 12; civic 1, 2, 4, 8, 11, 12. Rules: no banned words, no "flywheel," every number counted or chipped "claimed," every screenshot live or demo-bannered, status legend on the last slide.

## 6. Marketing

The channel is the message: no Meta or Google ad buys for an anti-tracking promise. Channels in order: the wall (poster kit ships with the front door), the walk-in, corridor-of-mouth referral codes (OSE-267), the league network lane, the warm civic path after receipts, the corridor Substack (parked). Hooks translated into the voice: "You've been trained to expect no choice. Here's what a real one feels like." · "Nothing about your device, location, or identity was collected to show you this." (already live; say it first) · "The wall, the night, the morning after." · "Community free forever. First-year businesses, first ad free. Established, cheap and never outbid." Guardrail enforced: no account, no app, one tap, privacy line beside the button.

## 7. Next, in order

1. OSE-1199 + poster QR assertion in UI smoke. 2. OSE-804 density census. 3. OCR-116 copy, CCR-gated. 4. SharedReport route for staging. 5. Design canvas on `@ocr/tokens` (hero, problems, relief, Triangle, web, doors, trust, footer; poster and TV artboards). 6. OSE-1200 + OSE-1201 with the port slices they touch. 7. Verify the Cloudflare challenge rule before production.
