# Decision: Supported languages across the OCR product line

> **Status:** DECIDED (owner, 2026-10-29). The language list, timing, rollout order and translation method are set (see "Owner answers"). Chicago leads, with 22 languages (see "First region").
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

- **This changes a prior scope line.** `ourSharedEvents/docs/mvp/MVP_SCOPE.md` lists "i18n/localization" under OUT OF SCOPE (v2+). This decision says which languages. The owner kept i18n at v2+ (below), so there is no conflict.
- **Right-to-left layout is required.** Arabic and Urdu (and Persian, on the watch list) need RTL support in `@ocr/ui`. That is design-system work in the spine repo and follows `packages/ui/design-system/` rules.
- **Fonts must cover Chinese, Korean, Arabic, Devanagari and Urdu scripts.** Input text stays ≥ 16 px (invariant).
- **Translation never touches identity or counts.** Translated strings change wording only. They never change what a count means, and the under-5 floor wording ("Fewer than 5") is translated, never replaced with a number.

## Owner answers (2026-10-29)

1. **Timing:** i18n stays v2+, as `ourSharedEvents/docs/mvp/MVP_SCOPE.md` already says. Nothing in MVP scope changes. (The owner answered "number one", meaning the first option offered: stay v2+.)
2. **Rollout order:** city by city, driven by demand. The first region is the **Chicago reach**, defined below. It must be fully covered.
3. **Who translates:** machine translation first for every language. Spanish and Arabic then get a paid human reviewer, a native speaker from the owner's local network. Every other language has no outside reviewer for now. The owner handles those alone, with machine translation as the only check. Experience on earlier sites showed that machine translation alone was not good enough for Spanish. Translations are made ahead of time, never at request time, because the OSE runtime is LLM-free.

## First region: the Chicago reach

The owner's definition is everywhere Chicago's pull reaches, roughly 10 million people:

- **Greater Chicagoland:** Cook, DuPage, Lake (IL), Will, Kane, McHenry, Kendall, DeKalb, Grundy and Kankakee counties
- **Northwest Indiana:** Lake, Porter and LaPorte counties
- **Southwest Michigan:** Berrien, Cass, Van Buren, St. Joseph and Kalamazoo counties
- **Southern Wisconsin:** Kenosha, Racine, Walworth, Rock and Milwaukee counties
- **West to the Quad Cities:** Rock Island (IL) and Scott (IA) counties, with the I-88 corridor between them

The county list is a working draft of the owner's description. The owner confirms or edits it.

**Chicago leads, so the Chicago reach ships with every language in the national 12 plus these regional languages** (owner, 2026-10-29). Where they are spoken comes from the same unverified ACS estimate; pull B16001 by county to confirm.

- **Polish:** Chicago, Northwest Indiana, Milwaukee. Likely the #3 language in the region.
- **Gujarati:** Chicago's west and northwest suburbs
- **Ukrainian:** Chicago
- **Greek:** Chicago
- **Serbian / Croatian / Bosnian:** Chicago, Northwest Indiana, Milwaukee
- **Hmong:** Milwaukee
- **Burmese, Karen, Swahili and Kinyarwanda:** the Quad Cities, from refugee resettlement

That makes 22 languages for the Chicago reach: the national 12 plus 10 regional ones (Serbian, Croatian and Bosnian count as three). This also settles the per-corridor question: a region can turn on languages the national list does not have. The regional languages use machine translation only, the same as the other non-Spanish, non-Arabic languages.

## Still open

1. **Chinese:** ship Simplified and Traditional both, or one first?
2. **County list:** confirm or edit the Chicago-reach counties above.

---

*Recorded 2026-10-29. Owner: Matt.*
