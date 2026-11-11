# ADR-013: Hand enterprise customization to the customer's solution engineer, and accept their work back through a mechanical gate

**Status:** Proposed
**Date:** 2026-11-11
**Deciders:** mzdan (PO) — pending review
**Scope:** OSM (artifact), OA (execution), OSE and OW (the surfaces being customized)

`[Claude]` Scaffold drafted 2026-11-11 from the founder's stated concept. The core decision
(Section "Open decision") is **not made**. Everything below the open decision is conditional on it.
Marked `[Matt]` where the founder's own words are carried verbatim.

---

## Context

Today a white-label customization is a conversation. The customer describes what they want, OCR
builds it, the customer reacts, OCR revises. Every cycle costs a round trip and OCR's attention is
the bottleneck. That is survivable at corridor scale, where the customer is a venue owner with no
technical staff. It does not survive at anchor and enterprise scale, where the customer has a
dedicated technical team that is perfectly capable of doing the work themselves and is slowed down
by having to ask.

`[Matt]` From the 2026-11-11 session:

> Here is this pre-loaded template from a solution engineer perspective. Figure this out, tweak it.
> Here is a snapshot of the application you can run. You can tweak and apply your own custom front
> end tweaks to however you like it. Once you've determined what those tweaks are, then you send me
> back that file. I apply it within my system. There's your custom website. That's how we go faster
> within customization, and we're not going this push and pull back and forth. We're using that
> technology transfer of skills for the more technologically advanced to be able to do this type of
> solutioning.

`[Claude]` This is the standard enterprise integration pattern: ship an SDK, ship templates, let the
customer's solution engineer do the last mile. It is proven and there is no reason it would not work
here. What is different in OCR's case is what a bad customization can do.

### Why OCR's version carries a risk the standard pattern does not

In an ordinary white-label product, a botched customization is ugly. In OCR, the surface being
customized is the surface that publishes counts. A customer SE who does not know the invariants, and
who should not have to, can weaken a privacy guarantee by accident:

- A layout change that surfaces a count on the display, which is required to show none (invariant 5).
- A copy or template change that renders a withheld count as `0` instead of "Fewer than 5", which
  turns a withheld value into a disclosed one (invariant 2).
- A reorder that changes what is shown alongside what, altering the disclosure context of a figure.
- A raw hex that bypasses `packages/tokens`, which is a brand break rather than a privacy break, but
  is caught by the same mechanism (invariant 8).

So the acceptance gate on returned work is **a privacy gate that also catches brand problems**, not
a style check that grows privacy assertions later. The invariant assertions have to exist before the
first customer file is accepted, not after.

### What makes a mechanical gate possible at all

Most products cannot gate customization mechanically because the customization surface is unbounded.
OCR's is already constrained for reasons that had nothing to do with this: colors come only from
`packages/tokens`, a raw hex never appears in a page, and `packages/ui` colors are never changed
(monorepo `CLAUDE.md`; OSE invariant 8). A constraint adopted for design-system hygiene turns out to
be what converts "run this stranger's branch" into "validate this declared token set."

### Current state, verified 2026-11-11

| Thing | State | Evidence |
| -- | -- | -- |
| Bruno requests in OSE | 282 across 3 collections (`ose-api`, `ose-pages`, `ose-sharedreport`) | `find bruno -name '*.yml' \| wc -l` |
| Browserless page-skeleton assertions | Live. `ose-pages` asserts on rendered HTML without a browser | e.g. "@media print block exists in rendered HTML" |
| Collections in OSM | **None.** OSM holds `CLAUDE.md`, `README.md`, `SKILL.md` only | `ls oursharedmagnets/` |
| OSM's stated tooling | Postman / Newman | `oursharedmagnets/SKILL.md`, `README.md` |
| Org standard's stated tooling | Postman, at `<repo>/postman/collections/<surface>.json` | `.ocr-standards/standards/OCR_STANDARD_perStoryTestPyramid.md` |
| OSE's actual tooling | Bruno (ex-Newman, OSE-1191) | `.github/workflows/oursharedevents-ci.yml:1442` |

Two drifts follow from that table and are filed separately: OSM's own docs name the wrong tool, and
the propagated org standard mandates a path no repo uses.

---

## Phase gate: this does not activate at launch (owner, 2026-11-11)

`[Matt]` From the 2026-11-11 session:

> The initial launch is only for the locals and the anchors. So think like bars, restaurants, and
> local establishments in the community, and not enterprise. Then that will give me time to get some
> income, get everything lined up, and then get the entire system super solid for enterprise, and
> then make the next level jump and be prepared for them.

`[Claude]` Layer 1 customers have no solution engineers, want no snapshot, and will never ask for the
collections. **No SE handoff machinery is built, promised, or sprinted on until layer 2.** An agent
or session that finds this ADR is reading a decision scheduled for later, not a backlog item.

What layer 1 must avoid, because each is cheap now and painful to retrofit:

1. **Collections stay file-based and in-repo.** Already true (282 requests under `bruno/`). Do not
   migrate to a hosted workspace for convenience.
2. **Invariant enforcement stays mechanical.** Already true. This is the certification asset at
   layer 2, not a cost incurred then.
3. **Any demo or snapshot instance is seeded with synthetic data, never cloned from a live
   corridor.** Not yet a rule, and no snapshot exists yet, so adopting it now costs one fixture file.
   Retrofitting it after demo fixtures exist means auditing every one.

Nothing else about layer 1 is constrained by this ADR.

**The commercial and legal work this ADR depends on is also deferred by the owner**: IP counsel,
trademark on the OCR marks, whether the certification can be structured as a conformance mark, and
licence terms on the collections and snapshot. Those are layer-2 questions and are not open items
for layer 1.

---

## Open decision (NOT MADE)

**How wide is the customization surface a customer SE may change?**

The gate's cost, and whether it can be mechanical at all, follows entirely from this. Three options,
with the honest cost of each:

### Option A: Tokens only

The SE changes colors, type scale, spacing. The returned file is a token set.

- **Gate:** cheap and close to complete. Valid values are enumerable; the gate validates against a
  schema OCR owns.
- **Cost:** an enterprise SE will find it limiting quickly, and limiting is what sends them back to
  asking OCR for changes, which is the problem this decision exists to solve.

### Option B: Tokens plus a constrained layout schema

The SE composes from a fixed vocabulary of blocks and arrangements. The returned file declares
intent, not markup.

- **Gate:** moderate. OCR validates a declaration against a schema it owns, and the invariant
  assertions attach to the schema rather than to rendered output.
- **Cost:** the schema has to be specified, which is the bulk of the work, and every new block is a
  new gate obligation.

### Option C: Arbitrary templates

Full control, which is what the OA tier table promises Enterprise today ("event-level overrides,
full control").

- **Gate:** very hard. Validating arbitrary output means asserting on rendered pages rather than on
  declared intent, and Bruno is browserless, so a meaningful share of the gate would need Playwright
  and a deployed instance per customer.
- **Cost:** the gate story for this option does not currently exist. OA promises it anyway. That gap
  is the reason this ADR was written.

`[Claude]` Recommendation, offered not decided: **Option B**, with Option A shipped first as the
walking skeleton so the loop is proven end to end before the schema is specified. Option C is
reachable later by widening B's vocabulary; it is not reachable by starting there.

---

## Decision (conditional on the above)

*Pending. Fill once the surface width is chosen.*

The shape the decision will take, whichever option is chosen:

1. **OSM owns the shipped artifact.** Backend and frontend Bruno collections, the SE handoff
   documentation, and the returned-file contract live in OSM, not OSE. OSE's collections test OSE;
   OSM's collections are a product handed to someone who has never seen the codebase. Different
   acceptance criteria, different repo.
2. **OA executes.** The returned file is applied and deployed by OA. OSM tells them how; OA does it.
   This is the existing OSM/OA split, unchanged.
3. **The frontend collection is the contract of acceptance**, not a test. Green means OCR applies
   the file without reading the diff line by line. That is the whole value; without it every
   returned file needs the founder's attention and the loop collapses back to push-pull.
4. **Bruno stays file-based and that is the reason.** The 282 requests are plain `.yml` files in
   folders: they diff, review in a PR, and ship to a customer as a directory. Postman's equivalent
   is JSON in a cloud workspace behind an account invite. For an artifact handed to a customer's
   technical team, the folder is the product. Recorded here so the stale org standard is not treated
   as a reason to revert.

---

## Consequences

### Positive

- OCR's attention stops being the bottleneck on enterprise customization.
- The customer's technical team does work they are better positioned to do than OCR is.
- The invariants become the thing that makes outside contribution safe, rather than a constraint on
  what customers may have.

### Negative

- **The gate is partial and must be described as partial.** Bruno is browserless. It sees markup,
  headers, CSS rules and response shape. It cannot see layout, interaction, or whether the result
  actually looks right. Structure is gated; appearance remains the SE's eye and OCR's. An SE told
  "green means approved" will be misled.
- **Born red applies harder here than anywhere else in the fleet.** A collection that cannot fail a
  bad token file is worse than no gate, because customer files would be applied on its authority. An
  injected raw hex and an injected 12px input must each be watched going red before this gates
  anything real. Per AGENTS.md: a gate that cannot fail counts as absent.
- **A new trust boundary exists.** OCR accepts and applies a file authored outside the org. The gate
  is what bounds it. Its coverage is therefore a security property, not a quality property, and
  belongs in the threat ledger.
- Every new block or token added to the customizable vocabulary is a new gate obligation, carried
  forever.

### Neutral

- The loop reuses the snapshot mechanism already discussed for outside reviewers: a runnable instance
  without repository history.

---

## References

- OSM role and the OSM/OA split: `oursharedmagnets/CLAUDE.md`, `ourairwaves/CLAUDE.md`
- White-label tiers (Free / Mid / Enterprise): `ourairwaves/CLAUDE.md`
- Design-system constraint that bounds the surface: `ourcommunityrituals/CLAUDE.md`,
  OSE AGENTS.md invariant 8
- Privacy invariants the gate must carry: OSE AGENTS.md invariants 1, 2, 5, 6
- Bruno collections as they exist today: `ourSharedEvents/bruno/`
- Born-red doctrine: OSE AGENTS.md, Quality gates

## Revisit criteria

- **When the surface width is decided** — the Decision section is filled and this ADR moves to
  Accepted.
- **When the first customer file is accepted** — record what the gate caught and what it missed.
- **If Option C is ever promised to a named customer** — the gate story must exist first, or the
  promise is made without a mechanism.
