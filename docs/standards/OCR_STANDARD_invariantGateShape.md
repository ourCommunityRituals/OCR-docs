# OCR_STANDARD_invariantGateShape

**Status:** ACTIVE · **Since:** 2026-09-05 · **Owner:** Matt
**Promoted from:** `ourSharedEvents/tests/e2e/0-architecture/README.md` (OSE-1246)
**Applies to:** every product repo that enforces an invariant in CI.

---

## The rule

> **An invariant gate asserts a PROPERTY over a derived subject list, or it
> names ONE artifact deliberately. It never states a rule about a class and
> enforces it on a single member.**

The third case is the failure, and it is silent. The gate stays green while the
invariant is violated somewhere it does not look.

---

## Why this is a standard and not a tip

A right that depends on whoever currently holds the room is a courtesy, not a
right. The same is true of an invariant: the commitment lives in the
**mechanism**, not in the sentence. A gate that can be routed around by ordinary
refactoring is a protection that can be repealed by accident.

This was found the expensive way. In one day, on one repo, **three** gates were
discovered enforcing a class-level rule on one named member — and none was found
by looking. They surfaced because a sibling file happened to be created.

---

## The three shapes

### 1. Property-asserting — derives its subjects

Scans a directory, parses the schema, reads a generated source map. **A file
added next month is covered the day it is written.**

Correct when the invariant is about a class: *"every handler that queries a
multi-tenant table binds `brand_id`"*, *"every PII column has a TTL"*, *"no
served template contains an inline event handler"*.

### 2. Subject-naming — names one artifact, correctly

Correct when the invariant is genuinely about **one thing's shape**: a sealed
payload's exact key set, one module's contract, one config's contents. Naming
the subject is right here, and rewriting it to scan would weaken it.

### 3. Meta-gate — asserts the mechanism exists and is wired

**The best shape available, and the most underused.** The gate does not scan; it
asserts that the *scanner* exists, is self-tested, has an allowlist, has a
runbook, and **is invoked by CI**. The scanning is done by that tool, which walks
the tree.

Reference implementation:
`ourSharedEvents/tests/e2e/0-architecture/deprecation-lock.invariant.spec.ts`
guarding `scripts/guard-no-gas.js`.

A meta-gate is the answer when enforcement needs real machinery. It also closes
the "the spec exists but nothing runs it" hole, because *is it wired* is one of
the things it asserts.

---

## What went wrong, concretely — keep these, they are the argument

**`tenant-isolation` (OSE, Invariant #9).** Asserted *"public list queries use
`WHERE brand_id = ?"`* of exactly one function in one file. A second public list
query shipped in a new file with no brand scoping; the gate never saw it.
Rewritten to scan every handler — and **on its first run it found a pre-existing
cross-brand leak on the public post-event recap page** that the named-subject
version had been green through for the entire life of the leak.

**`pii-retention` (OSE, Invariant #8).** Kept a hand-maintained registry whose
own instructions read *"to add a new PII table: 1. Add a row here"* — a guarantee
that binds only someone who has already decided to open the file. Its header
named the exact failure mode (*"a new PII column added to the schema without
wiring into the cleanup loop silently over-retains"*) and it could not catch it.
The registry was **complete**; it simply could not notice if it stopped being.

**`api-response-schema` (OSE, OSE-INV16).** Read `handlers/events.ts` for
`function enrichWithPhase`. When that function was extracted to a shared module —
so a second consumer could not skip it, which strictly improved the thing the
gate guards — the gate went red. **A gate that a correct refactor breaks is a
gate people learn to route around.**

---

## Two requirements when you write a derived gate

### A negative control is mandatory

**A completeness check that finds nothing is indistinguishable from one that
looks at nothing.** The first draft of the `pii-retention` parser anchored its
identity regex to line start, matched **zero** columns in a schema full of them,
and passed.

Every scanning gate ships with a test asserting the parser sees what it is meant
to see.

### A triaged exemption list, with a reason per entry

Legitimate exceptions exist — dynamically-built `WHERE` clauses, correlated
sub-selects, cross-product emission that is meant to be unscoped. **A gate that
cannot express an exception gets deleted rather than fixed.**

Entries carry a written reason for the next reader, not for the linter. New
violations fail; the baseline does not grow silently.

### Parse the path the drift actually travels

`pii-retention`'s scanner had to read `ALTER TABLE ... ADD COLUMN`, not only
`CREATE TABLE`, because that is how columns arrive in that schema. A scanner
that covers the wrong syntax is a subject-naming gate wearing a scan.

---

## Known exposure at time of writing

`ourWKRP/tests/security/ccr-invariants.test.ts` uses
`SRC = (f) => readFileSync(join(__dirname, '../../src', f))` — a named-subject
helper, zero directory scanning. **It has the same shape as the three OSE gates
that failed.** Audit tracked in the WKRP backlog; this section is removed when
that closes.

This is the reason the standard lives in the brain rather than in one repo's test
directory: an OSE-local fix would have re-entered as drift through WKRP.

---

## Checklist for a new gate

- [ ] Is the invariant about a **class** or **one artifact**? Answer before writing.
- [ ] Class → derive the subject list. One artifact → name it and say why in a comment.
- [ ] Needs real machinery → write a meta-gate, and assert **CI invokes it**.
- [ ] Derived → ship a negative control.
- [ ] Derived → ship a reasoned exemption list.
- [ ] Derived → confirm the parser reads the syntax the drift actually uses.
- [ ] Verify the gate **fails**: revert the thing it guards and watch it go red.
