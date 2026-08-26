# ADR-007: The demo sites are a permanent reference installation, not a per-meeting stand-up

**Status:** Accepted
**Date:** 2026-08-25
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

## Context

Every product in the OCR line needs something to point at: sales conversations, onboarding,
documentation, essays, and memos all need a live, honest surface a prospect can open and understand
in minutes. The recurring failure mode in this category is the **bespoke per-meeting demo** — a
throwaway dataset stood up the night before, drifting from the real product, going stale the moment
the meeting ends, and quietly teaching the wrong thing because nothing keeps it true.

OSE has already built the raw material. `getRiphDataset()` (`workers/oursharedevents/src/lib/
mock-data.ts`) is a pure, deterministic, multi-league RIPH property — campaigns and sponsors at
Local / Mid / Premium, a season with realistic scan distributions, real Blue Island H3 cells, and a
deliberately-visible K-anon ladder fallback (the honesty feature on display). It is served today by
`handlers/demo.ts` at `/demo` and `/demo/:tier`, spec-locked by `riph-demo-dataset.spec.ts`
(OSE-608), and its identity/geo was reconciled to the brain in OSE-995. What is **not** yet decided —
and what has blocked every build child of the demo epic (OSE-605: OSE-607 / OSE-609 / OSE-610) — is
the **constitution**: what the demo *is*, how its data is classed, and what keeps it from going
stale. `demo.ts` itself records the gap in its header: the `data_class`-at-write path and naming
doctrine are "deferred until this rides OSE-606."

This is the landing of that constitution. It is fleet-scoped because the demo-as-reference pattern,
the third data class, and onboarding-by-relabeling are product-line doctrine (OSM/OA provision demos
for every spoke), not an OSE-only concern — it satisfies fleet-ADR criteria 2 and 4 (see
[`README.md`](README.md)). Trigger: OSE-606, born from the OSE-605 demo epic and the 16-Aug
adversarial review's demand that the showcase be a durable asset, not a disposable prop.

## Decision

The demo installation is governed by five doctrine lines. They are the reference contract every demo
surface, dataset, and CI gate in the fleet must honor.

1. **Permanent reference installation.** The demo sites are the platform's permanent reference
   installation. Everything points at them — sales, onboarding, documentation, essays, memos. They
   are **never stood up per-meeting and never allowed to go stale.** A drifted or dark demo is a
   defect, not a cosmetic gap.

2. **Three-site trio = Invariant #5 as a live exhibit.** `demo-free`, `demo-mid`, and `demo-premium`
   are three standing installations of the **same venue and the same dataset**, each rendering the
   full experience at its tier depth. Same data underneath, three depths on top: **Tier Equity
   (Invariant #5)** made permanently visible — the paid tiers buy *depth of report*, never a
   different or privileged underlying truth.

3. **Demo is the third data class.** `data_class` is a single enum with three members —
   **`production` | `synthetic` | `demo`** — defined once. Demo rows live in production storage,
   labeled `demo` **at write time**, and are permanently excluded from vintage, reports-for-sale, and
   the research corpus. Demo is not "test data left lying around"; it is a first-class, self-declaring
   provenance state (see the provenance self-declaration already shipped in OSE-1012/1013).

4. **Break the demo = break the build.** Demo URLs and tokens are standing CI fixtures. A release
   that breaks any demo surface — an empty section at a tier's depth, a stale identity, a dead route,
   a suppressed-bucket honesty label gone missing — is a **broken release.** Demo currency is
   enforced by machinery, not by remembering (this is the contract OSE-609 implements).

5. **Onboarding is relabeling, not rebuilding.** A founding client's real venue **replaces** the
   demo venue; the `data_class` flag flips `demo → production`. The demo URL a prospect saw is
   *structurally* the URL they receive as a client. There is no separate "real product" to migrate
   to — the demo is the product, one flag away.

### Verification note — the `data_class` enum (confirmed against code, not assumed)

Doctrine line 3 requires exactly one enum, three members, defined once. Confirmed on OSE `origin/main`:

```sql
-- workers/oursharedevents/migrations/0052_add_data_class_to_events.sql
ALTER TABLE events ADD COLUMN data_class TEXT NOT NULL DEFAULT 'production'
  CHECK (data_class IN ('production', 'synthetic', 'demo'));
```

The enum is CHECK-constrained at the schema layer (not merely a convention), the demo dataset already
stamps every row `data_class: 'demo'` (`getRiphDataset()`), and the provenance banner already derives
its `live | demo | degraded` state from this class rather than a remembered label (OSE-1012/1013). The
one piece still owed by the build children: demo rows are currently *rendered* from the in-memory
fixture; writing them into production storage under `data_class='demo'` (the true "labeled at write
time" path) rides the OSE-605 build stories now that this constitution is landed.

## Alternatives Considered

### Alternative A: Bespoke per-meeting demos

Stand up a fresh dataset for each sales conversation or onboarding.

**Rejected because:** it is the exact failure mode this ADR exists to kill. Per-meeting demos drift
from the product, go stale immediately, cost human effort every time, and — worst — teach prospects
things that aren't true because nothing keeps them honest. It also makes "break the demo = break the
build" impossible: there is no standing surface for CI to guard.

### Alternative B: One demo site with a tier switcher

A single installation with a UI toggle that changes the rendered depth.

**Rejected because:** it undercuts the Invariant #5 exhibit. Three *standing* installations of the
same data at three depths let a prospect open all three side by side and see with their own eyes that
the underlying truth is identical — that depth is bought, not privilege. A switcher makes tier equity
a claim again instead of a visible, comparable fact, and it complicates onboarding-by-relabeling
(which flips one installation, not a mode).

### Alternative C: Demo data in a separate database / separate deploy

Keep demo rows physically out of production in their own store.

**Rejected because:** it breaks doctrine lines 3 and 5. If demo lives elsewhere, onboarding is a
*migration* (rebuild), not a *relabel* (one flag), and the "same URL structurally becomes your client
URL" promise is lost. Isolation is achieved correctly by the `data_class` column + exclusion rules
(demo never enters vintage / reports-for-sale / research corpus), not by a separate database — one
enum, enforced at write and at every export seam.

## Consequences

### Positive

- **The showcase becomes a durable asset.** One canonical, spec-locked dataset (OSE-608) behind three
  standing surfaces; sales/onboarding/docs all point at the same honest thing.
- **Tier Equity stops being a claim.** Invariant #5 is demonstrable live — three depths, one truth,
  openable side by side.
- **Staleness becomes a build failure**, not a person's responsibility to remember (OSE-609).
- **Onboarding collapses to a flag flip** — no "demo-to-real" migration project; the prospect's URL is
  the client's URL.
- **Provenance is structural, not professed** — demo self-declares via `data_class`, consistent with
  the transparency-by-construction posture (OSE-1012/1013).

### Negative / costs

- Demo rows in production storage require every export/aggregation seam (vintage, reports-for-sale,
  research corpus, SharedReport) to **honor the `demo` exclusion** — a `data_class != 'demo'` filter
  that must be enforced and tested, not assumed. This is a real, ongoing obligation.
- "Break the demo = break the build" adds standing CI fixtures (demo URLs/tokens) that must be kept
  current — the machinery has a maintenance surface, deliberately traded for currency.

### Neutral / follow-on

- **Public naming** (a fictionalized venue name for the public demo URLs, vs. showing Jen her own
  recognizable shop in the RIPH meeting) is a product decision this doctrine enables but does not
  itself fix — it is resolved with the build children (OSE-607).
- This ADR is the *why*; the machine-gateable *what* (the `data_class` write-time stamp + the
  export-seam exclusions + the break-demo-break-build fixtures) is encoded by OSE-605's build stories
  and the conformance loop (OSE-997/OSE-609). ADR and gate are complementary, not redundant.
