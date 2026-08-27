# UEC v1.2 — demote LIVE from core

Staged change for `OCR-docs/ocr-docs-brain/uec-codes.yaml`. Not applied: OCR-docs is
mid-work on `feat/ose-390-oer-aggregation-boundary`.

## The change

`LIVE` moves from the 7-core block to the extension block. **`num: "02"` is unchanged** —
core-vs-extension is a role, not a position, and the artifact's own rule is that numbers
are stable (`future v1.2 additions append starting at 12`). Renumbering would repoint
anything already referencing code 02 for no gain. Core becomes 01, 03–07 — non-contiguous,
which is the correct cost of stable numbering.

Add to the LIVE entry:

```yaml
    status: DEMOTE
    extension_priority: LOW
```

Move the whole `- id: LIVE` block below the `# ┌─ 4 EXTENSION CODES ─` marker, and update
the two block header comments:

```
# ┌─ 6 CORE CODES ──────────────────────────────────────────────────────────────
# ┌─ 5 EXTENSION CODES ─────────────────────────────────────────────────────────
```

## Changelog entry

Append to `changelog:`:

```yaml
  - from: LIVE (v1.1 core, num 02)
    to: LIVE (v1.2 extension, num 02 — number unchanged)
    code: LIVE
    type: core_demotion
    reason: >
      LIVE has no implementation anywhere in the ecosystem — no route, no handler,
      no consumer. Its only occurrences are this definition and mock-data.ts. The
      features it names (live scoring, brackets, thermometer) exist only as mock
      data.

      The deeper reason is a distribution mismatch: core codes go on posters, and
      posters are durable artifacts printed ahead of time. LIVE content exists for
      the duration of an event. Printing a permanent code for something live means
      printing something dead almost all the time — which is why the code was
      defined and never built.

      LIVE's real channels are (a) a destination reached from the session an
      attendee already established by scanning ENTER at the door, requiring no
      second scan, and (b) a screen-rendered code, which unlike a poster can
      change — allowing a code to carry a unit id directly rather than inferring
      one from a timestamp, which OSE's scan path forbids (qr-scan.ts: only
      hour-granularity scan_bucket is stored, no exact timestamp).

      Neither channel is print. LIVE is therefore not a core code. It remains a
      valid extension and returns when a consumer exists.

      Open when it returns: LIVE currently conflates a READ job (see what you
      cannot see from where you stand — brackets, totals) with a WRITE job (vote,
      affect the outcome). All the hard requirements — unit resolution, dedup,
      proof-of-presence — belong to the write job alone. Settle whether that is
      one code or two before reinstating.
```

## Not included, still open

- **SHOP promotion to core.** Discussed but not settled. If it lands, same rule:
  keep `num: "11"`, change the role only.
- **ARCHIVE / UTILITY demotion.** Discussed. Note UTILITY is the declared catch-all
  (`anything without a dedicated UEC color receives charcoal`), so demoting it needs
  an answer for what absorbs WiFi passwords and venue maps — and that successor
  should carry the most conservative consent tier, or the default widens.
- **`consent_tier` field.** Does not exist yet. Every tier statement in this thread
  was inferred from `data_generated`.

## Must land together

Brain-only edits break the drift-check. All three currently agree at 11 codes:

1. `OCR-docs/ocr-docs-brain/uec-codes.yaml`
2. `ourSharedEvents/workers/oursharedevents/src/lib/uec/uec-codes.ts` (`VERSION = '1.1'` → `'1.2'`)
3. Claude Design DS `_ds/oursharedevents-design-system-.../tokens/uec.css`

## Accessibility note

Demoting LIVE removes two of the four cross-tier CVD failures in the core-6 set
(ENTER|LIVE dE 13, LIVE|HELP dE 8). It does not fix the rest: ENTER|SHOP (14) and
SHOP|HELP (17) remain, and the four codes treated as locked — ENTER, SPONSOR, HELP,
FEEDBACK — already fail among themselves at ENTER|FEEDBACK dE 14 under protanopia.

The palette is saturated. Colour cannot carry the set; the word and the URL path
must. See `level3_unit_3Z.py` for the gate that measures this.
