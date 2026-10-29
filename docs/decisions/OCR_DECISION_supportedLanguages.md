# Decision: Supported languages across the OCR product line

> **Status:** DECIDED (owner, 2026-10-29). The language list is set. Rollout order and timing are open.
> **Decided by:** Matt (owner)
> **Applies to:** every OCR product with a public surface (OSE, OW, OSM, OA, and later spokes)

---

## The decision

These are the languages OCR supports from now on:

| # | Language | Notes for implementation |
|---|----------|--------------------------|
| 1 | English | Default and source language |
| 2 | Spanish | |
| 3 | Chinese | Mandarin and Cantonese speakers. Written as Simplified and Traditional |
| 4 | Tagalog (Filipino) | |
| 5 | Vietnamese | |
| 6 | Korean | |
| 7 | Russian | |
| 8 | Arabic | Right-to-left |
| 9 | French | |
| 10 | Haitian Creole | |
| 11 | Hindi / Urdu | One spoken language, two scripts. Urdu is right-to-left |
| 12 | Portuguese | Brazilian and Cape Verdean communities |

## Why

The owner's founding and target cities: New York, Detroit, Chicago, Milwaukee, Minneapolis, St. Louis, Omaha, Austin, Albuquerque, Los Angeles, San Francisco, Seattle, Portland, Salt Lake City, Philadelphia, Atlanta, Birmingham, Nashville, Cincinnati, Washington, D.C., and Boston.

**Method:** the ranking is an estimate of US Census American Community Survey (ACS) figures for "language spoken at home" (table B16001) over 2015–2024, added up across the metro areas of those cities. It came from an assistant session on 2026-10-29 and was **not** re-pulled from the source tables. Places 1–8 are clear. Places 9–12 are close and could swap with the watch list below. Pull B16001 before anyone cites exact speaker counts.

## Watch list (not committed)

These languages are close behind the top 12 overall, or among the largest in one city. Since OCR is hyperlocal, a corridor may need one of them before the national list would suggest it.

- **Close behind overall:** Bengali, Armenian, Persian (Farsi), Polish, Yiddish, Amharic
- **Large in one city:**
  - Hmong: Minneapolis, Milwaukee
  - Somali: Minneapolis, Seattle, Portland
  - Chaldean (Neo-Aramaic): Detroit
  - Navajo (Diné): Albuquerque
  - Karen and Nepali: Omaha
  - Kurdish: Nashville
  - Tongan and Samoan: Salt Lake City
  - Bosnian: St. Louis
  - Ukrainian: Portland, Seattle
  - Tigrinya and Yoruba: Atlanta, DC

## Consequences

- **This changes a prior scope line.** `ourSharedEvents/docs/mvp/MVP_SCOPE.md` lists "i18n/localization" under OUT OF SCOPE (v2+). This decision says which languages, not when. Whether i18n stays v2+ is still open (below).
- **Right-to-left layout is required.** Arabic and Urdu (and Persian, on the watch list) need RTL support in `@ocr/ui`. That is design-system work in the spine repo and follows `packages/ui/design-system/` rules.
- **Fonts must cover Chinese, Korean, Arabic, Devanagari and Urdu scripts.** Input text stays ≥ 16 px (invariant).
- **Translation never touches identity or counts.** Translated strings change wording only. They never change what a count means, and the under-5 floor wording ("Fewer than 5") is translated, never replaced with a number.

## Open questions for the owner

1. **Rollout order:** all 12 at once, or in waves (for example Spanish first, then by corridor)?
2. **Timing:** does i18n stay v2+ per MVP_SCOPE, or move earlier?
3. **Per-corridor languages:** can a corridor turn on a watch-list language (for example Hmong in Minneapolis) before it reaches the national list?
4. **Who translates:** professional translators, community volunteers, or machine translation reviewed by a person? (The OSE runtime is LLM-free, so translations are produced ahead of time, never at request time.)
5. **Chinese:** ship Simplified and Traditional both, or one first?

---

*Recorded 2026-10-29. Owner: Matt.*
