# Brain amendment — Articles #26 and #27

Staged for `OCR-docs/ocr-docs-brain/architectural-invariants.yaml`.

> **HARD PRECONDITION (verified 2026-08-26, CCR loop 3):** articles #23–#25 are
> THEMSELVES UNCOMMITTED — they exist only in `feat/ose-390`'s working tree;
> committed law at HEAD tops out around #22. Therefore: (1) `feat/ose-390`
> merges FIRST; (2) re-check the numbering and #25's final shape against what
> actually merged before applying these drafts — #26/#27 assume both;
> (3) note that OSE migrations 0061/0067 already cite "#25" from committed
> code — a committed citation of uncommitted law — which is the strongest
> live argument for the registry-version mechanism (item 5 below).
> RESOLVED 2026-08-27: `applies_to` IS a machine-read field —
> `scripts/check_brain_contract.py` filters invariants by it and requires each
> applicable invariant's `test_file` to EXIST in the spoke repo (spoke-relative
> path, checked per product). CONSEQUENCE FOR THESE DRAFTS: `test_file` as
> written uses OSE paths with prose annotations — landing #27 with
> `applies_to: [ose, wkrp]` as drafted would FAIL wkrp's brain-contract-check
> (path absent in OW) and open a spurious drift ticket. Before landing, either
> (a) give multi-spoke invariants a per-product test_file mapping in the
> checker + registry, or (b) list the spoke-resolvable path per spoke:
> OSE `tests/schema-lexicon.spec.ts`, OW `tests/security/count-floor.invariant.spec.ts`.

Entry shape mirrors #25's rich form. Ruled 2026-08-26: **law leads, implementations
conform** — #26 is registered from one spoke's implementation, deliberately ahead of
the second spoke (QA dissent recorded in session; Co-Arch position adopted).

---

## Article #26 — Sponsor Placement Mutual Acceptance

```yaml
  # ── #26 SPONSOR PLACEMENT MUTUAL ACCEPTANCE ─────────────────────────────────
  - id: 26
    name: sponsor_placement_mutual_acceptance
    label: "#26 — Sponsor Placement Mutual Acceptance"
    group: commercial_governance
    group_order: 3
    title: Sponsor Placement Mutual Acceptance
    status: partial
    applies_to: [ose]   # hybrid transition planned: extend to wkrp when the
                        # OW artist/venue sponsor surface goes live
    test_file: tests/sponsor-lifecycle-acceptance.spec.ts (OSE repo — live, 0068)
    enforces: >
      A sponsor placement is a relationship between two parties, so either party
      may initiate it and either party may reject it. A placement renders on any
      public or report surface only when neither side has rejected it
      (organizer_accepted and sponsor_accepted are NULL-permissive: NULL means
      "not answered" and does NOT hide — rejection is the operative act, so
      pre-existing placements need no backfill). Whoever initiated a placement
      is accepted-on-insert; sponsor_placement.source records who that was.
      A rejection is durable: template+geo matching (Path 2) must not re-propose
      a business the organizer has already rejected for that event. Business
      deletion is a business-level fact (sponsor_business.is_active), read at
      join time by every resolver path — never a cascade denormalised onto
      child rows.
    protective_statement: >
      Without this, placement is unilateral in both directions: an organizer can
      attach a business that never agreed to appear, and a subscribed business
      can surface on an event whose organizer never agreed to host it. Mutual
      acceptance is also what permits generous matching — an unwanted proposal
      costs one durable rejection, so the network can propose liberally without
      making any match a fait accompli.
    enforcement_statement: >
      Read side LIVE (OSE 0068): resolver Paths 1+2 and the public event page
      filter on business lifecycle + both acceptance flags; born-red suite
      sponsor-lifecycle-acceptance.spec.ts pins delete-hides, either-side
      rejection hides, NULL does not hide. Write side PENDING: accept/reject
      endpoints do not exist yet — scoped as a security story (per-role authz +
      audit rows), not CRUD. Status is partial until the write side lands.
    activation_criterion: >
      partial → live when the accept/reject write endpoints exist with per-role
      authz and audit rows, and the born-red suite covers them.
```

## Article #27 — Honesty Lexicon

```yaml
  # ── #27 HONESTY LEXICON ─────────────────────────────────────────────────────
  - id: 27
    name: honesty_lexicon
    label: "#27 — Honesty Lexicon"
    group: commercial_governance
    group_order: 3
    title: Honesty Lexicon
    status: live
    applies_to: [ose, wkrp]   # OW facet LIVE 2026-08-26: tests/security/
                        # count-floor.invariant.spec.ts bans the lexicon on OW's
                        # count-publishing handlers (word-boundary token match)
    test_file: tests/schema-lexicon.spec.ts (OSE repo — live, OSE-801 born-red)
    enforces: >
      No persistence-layer identifier (table, column, index) may carry a term
      that claims a count of PEOPLE when the system counts SIGNALS, nor ad-tech
      audience vocabulary: attendance, impression(s), visit(s), reach, unique,
      turnout, eyeball(s), people, view(s). The honest replacements name the
      measurement fact (display = an ad rendered; distinct_agent_hashes = the
      COUNT(DISTINCT hash) it computes). Exemptions are tracked per-identifier
      with the ticket that removes them, and a stale exemption fails the gate
      in the other direction.
    protective_statement: >
      A surface lint that stops at the boundary while storage speaks the banned
      words is aspirational and gets routed around by accident — every ORM
      type, export header, log line and error message inherits column names.
      The platform's market position is that it underclaims by construction;
      the lexicon is where that promise is enforceable rather than editorial.
    enforcement_statement: >
      LIVE via schema-lexicon.spec.ts (reads sqlite_master + PRAGMA against
      BANNED_SCHEMA_TERMS; born-red OSE-801, 2026-08-20). KNOWN GAP, recorded
      not gated: the lint reaches schema identifiers only — API field names
      (unique_gatherings), code comments ("campaign reach", shared-report-
      builder.ts), and report copy are out of scope. Presentation-layer
      vocabulary is governed editorially by the nomenclature rule "a term must
      never claim more than the underlying count supports."
    references: >
      CITATION FIX REQUIRED in OSE: migration 0064 and related comments cite
      this doctrine as "Invariant #25". Registry #25 is sponsor_share_covenant
      — the lexicon had no number until this article. Applied migration files
      stay untouched (#19 append-only); fix the citation in living source
      (src/lib/schema-lexicon.ts header, tests/schema-lexicon.spec.ts header)
      to read "#27".
```

---

## Apply checklist (one brain PR)

1. Append both articles to `architectural-invariants.yaml`; bump the registry's
   count/changelog per house pattern (changelog entries `invariant_id: 26, 27`).
2. OSE follow-up (separate small PR): re-cite "#25 → #27" in
   `src/lib/schema-lexicon.ts` + `tests/schema-lexicon.spec.ts` headers.
   Migration 0064 stays as-is, append-only.
3. CANDIDATE #28 — uniform_count_floor. The K-anon family (OSE-665/683/711)
   is enforced in TWO spokes now (OSE builder + OW sponsor report,
   src/lib/count-floor.ts + tests/security/count-floor.invariant.spec.ts) but
   has NO article. Two implementations = pattern; register it.
4. Sequencing per the precondition above: this entire bundle lands AFTER
   feat/ose-390 merges, in its own PR, re-validated against merged numbering.
5. Also staged, same session, still pending: UEC v1.2 LIVE demotion
   (`uec-v1.2-live-demote.md`) and the amendment-propagation / registry-version
   mechanism (deferred — staged item 3 of the scrum plan).
