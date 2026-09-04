# OCR Standard — Declined Regimes

**Status:** Founder doctrine, 2026-09-04. Supersedes any reading of the clearance tiers as
"future capabilities."
**Owner:** Matt · **Applies to:** every OCR product that declares a `pool-contract.ts`

---

## 1. The rule

> **Hospital PII and COPPA under-13 child data — including parental-clearance mechanics — are
> off the books.**

OCR does not hold Protected Health Information. OCR does not hold individual child data. OCR
does not implement, store, or reference parental consent records.

These are **declined regimes**, not tiers the platform matures into. There is no roadmap on
which OCR acquires them. The correct posture is permanent refusal, and the architecture is
what makes that refusal true rather than promised.

## 2. Why this is stated as doctrine and not preference

The platform's entire claim is that it counts rooms and never people. A regime that requires
holding a minor's consent record, or a Business Associate Agreement over PHI, is not a larger
version of that claim — it is its negation. Entering either regime would mean the anonymous
architecture is a product tier rather than a property, which is the thing the whole design
exists to prevent.

## 3. Item-tracking is the mechanism that makes refusal viable

This is why the item destination matters, and it is not a convenience.

A library summer reading programme, a rec-centre youth league, a school activity — all of them
are servable **without entering a declined regime**, because what is tracked is the **item**,
never the participant.

| | The institution holds | OCR holds |
|---|---|---|
| Library | The card, the borrower, the minor's registration | The book's scans, by week |
| Rec centre | The membership, the waiver, the guardian's signature | The programme's scans, by week |
| School | The enrolment, the FERPA record, the parental consent | The activity's scans, by week |

The librarian does not care whether the borrower is a child or an adult, because they are
measuring **circulation**, not people. OCR collects the item's behaviour — did this programme
work, over this period, for the people running it — and nothing else.

**Access control stays with the institution.** They control the card. They control who may
join the programme. That control is theirs to exercise and OCR's to never see.

Consequence: a child-adjacent or health-adjacent context does **not** raise OCR into a
declined regime, because item-level tracking produces `general`-pool data in every one of
them. No age bracket. No consent batch. No participant identity. Nothing to protect, because
nothing was taken.

## 4. What in the code contradicts this today

Verified 2026-09-04. All three are live.

### 4.1 `phaseToPool()` routes to declined regimes

`workers/oursharedevents/src/lib/pool-contract.ts`:

```ts
if (phase === 5) return 'coppa';
if (phase === 4) return 'hipaa';
return 'general'; // phases 1-3
```

Live in the export path (`lib/shared-report-export.ts`), brain-conformance-verified. Tiers 4
and 5 are wired to route, not to refuse.

### 4.2 `REGULATORY_POOLS` declares pools OCR will not fill

```ts
export const REGULATORY_POOLS = ['general', 'hipaa', 'coppa'] as const;
```

Its own comment: *"Regulatory pools this product routes writes to."* OSE does not route writes
to either declined pool and must not.

### 4.3 The brain schemas model the exact mechanics that are off the books

`ocr-docs-brain/bigquery-schemas/coppa.json` declares `parental_consent_batch_id`,
`consent_method` (*"signed_form, email_verification"*), `consent_date`, `consent_scope`,
`expiration_date`, `revocation_date`, `age_group` (*"under_13"*), and `participant_count`
(*"Number of minors covered"*).

`ocr-docs-brain/bigquery-schemas/hipaa.json` declares `baa_entity_id` (Business Associate
Agreement), `phi_classification` (*"none, adjacent, **direct**"*), a mandatory access audit log
with `actor_id` / `action` / `record_id` / `justification`, and `consent_reference`.

These describe a consent-management system and a PHI-handling system. **Neither is a thing OCR
builds.** They are aspirational artifacts that read as commitments.

### 4.4 The path by which this could fire silently

1. A tier-4 or tier-5 event type is seeded — migration 0057 already names `school_event` as
   Phase 5.
2. `ALLOWED_MAX_TIER` is raised. It is an **env config value** (`resolveAllowedMaxTier`) — no
   code review required.
3. `phaseToPool()` routes those exports to `oureventring_hipaa` / `oureventring_coppa`.
4. Those datasets expect BAA identifiers and parental consent records.

No step in that chain currently turns a build red.

## 5. What this changes about the open CCR

The CCR's top concern was *"the danger is one env var away."* This doctrine **removes the
danger rather than gating it**, and simplifies the hold:

| Was | Becomes |
|---|---|
| Don't raise `ALLOWED_MAX_TIER` until the WHERE axis is wired | **`ALLOWED_MAX_TIER` never exceeds 3.** Tiers 4–5 are declined, permanently |
| Counsel needed to raise a tier for a school or library vertical | **No tier is raised.** The vertical is served at tier 1–3 by item-tracking |
| Wire the WHERE axis so RESTRICTED/REGULATED nodes constrain sponsors | Still required — but for **sponsor-category and disclosure** constraints, never for admitting PHI or child data |

The WHERE-axis work stands on its own merits (a rec centre must be able to say "not these
sponsor categories"). It is no longer load-bearing for regulatory admission, because there is
no admission.

## 6. Required changes

1. **Cap the ceiling as an invariant, not a config.** `ALLOWED_MAX_TIER` must be structurally
   incapable of exceeding 3. A CI gate fails the build if it is set higher or if a tier-4/5
   type is seeded.
2. **`phaseToPool()` should refuse, not route.** Throw `PoolRoutingError` on 4 and 5 — the
   function already throws on out-of-range input, so refusal is the established shape.
3. **`REGULATORY_POOLS` for OSE becomes `['general']`.** A product should not declare pools it
   will never write.
4. **Mark the brain schemas DECLINED.** `coppa.json` and `hipaa.json` should carry an explicit
   `status: declined` and a pointer to this standard, or be removed. As written they read as
   capabilities on a roadmap.
5. **State the item-tracking rationale in `docs/REGULATORY-PHASES.md`** — that file currently
   presents the 5 phases as a maturity ladder OSE climbs. Phases 4 and 5 are not rungs.
6. **Say it on the front door.** *"We never hold a child's data or a patient's record — not
   because we protect them well, but because we never take them"* is a stronger claim than
   anything currently in the OCR-116 copy, and it is true by construction.

## 7. What this standard does NOT claim

- It does not say OCR is exempt from statute. It says OCR holds nothing those statutes govern.
- It does not resolve library circulation-record confidentiality, which is a separate body of
  state law and remains open with counsel.
- It does not authorise serving a school or hospital without their own compliance review. The
  institution's obligations are unchanged; OCR simply is not a party to the protected record.

---

*Verified against `src/lib/pool-contract.ts`, `src/lib/shared-report-export.ts`,
`src/lib/template-clearance.ts`, `migrations/0057_seed_template_event_types.sql`,
`ocr-docs-brain/bigquery-schemas/{coppa,hipaa}.json`.*
