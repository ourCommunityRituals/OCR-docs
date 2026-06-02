---
name: story
description: Draft a Linear story with the canonical OCR shape (Goal / Scope / Definition of Done / Why / Source). Infers project/team/parent from working dir + active branch + recent session context. Outputs a draft for review before firing.
allowed-tools: Read Bash Grep
argument-hint: "<one-line story description>"
---

# Draft a Linear story

Take **"$ARGUMENTS"** as the story seed and produce a fully-formed Linear story draft using the canonical OCR shape.

## Step 1 — Infer context

### Working directory → team + project hint

- `ourWKRP/` (or any worktree thereof) → team `OurWKRP`. Default project depends on cwd subdir (`src/handlers/playlist.ts` → playlist work; `docs/features/fist-of-five-*.md` → Fist of Five project; etc.).
- `OCR-docs/` → team `OCR-doc`. Default project depends on what's in cwd / recent edits.
- `ourSharedEvents/` → team `OurSharedEvents`.
- `ourSharedMagnets/` → team `OurSharedMagnets`.

If `cwd` is outside a recognized product repo, ASK.

### Active branch → parent issue hint

```bash
git branch --show-current
```

If the branch matches `claude/<TEAM>-<NNN>-*` or `<team-name>/<team>-<NNN>-*` → parent = `<TEAM>-<NNN>`.

If no parent inferable, ASK.

### Recent session context → related work hint

Look for the last Linear ticket touched in this session (recent tool calls to `save_issue` / `get_issue`). If present, propose as `relatedTo` or `parent`.

### Active Initiative → priority context

If recent work has been under "Self-Checking Infrastructure — Invariants as the Core Framework", default project to one of the Initiative's projects (ADR-002 implementation, Brain invariant hygiene, Brain Ops, OCR-Enforcement, OCR-RedTeamAgent, L5 — Auto-emit drift tickets, L5 — Per-product framework onboarding, L5 — Framework-readiness telemetry, L5 — Continuous-improvement cadence). Otherwise leave priority unset.

If any context is ambiguous, ASK 1-2 clarifying questions max BEFORE drafting.

## Step 2 — Canonical draft shape

Always include:

```markdown
## Goal

<1-2 sentences — what this story accomplishes>

## Scope

- <bulleted concrete deliverables>

## Definition of done

- <bulleted observable success criteria — not "feature works" but "tests cover X; endpoint returns Y; CI passes Z">

## Why

<1-2 sentences — what this unlocks or prevents>

## Source

<where this came from — a CCR finding, a phantom catch, a sibling Story, the user's request, an ADR>
```

Optional sections (include when relevant):

- **Open design questions** — if the story has unresolved decisions; each question should propose a recommendation.
- **Concept doc** — link to the canonical doc the story implements.
- **Blocked by / Blocks** — explicit dependency declarations against existing Linear IDs.
- **ADR-002 alignment** / **ADR-003 alignment** — if the story touches identity surfaces, per-surface invariants, or framework layers; name which.
- **Sequencing note** — if there's a deliberate ordering with sibling stories.

## Step 3 — Title discipline

- Title is imperative + concrete. **Yes:** "Tighten check_invariant_test_files beyond glob-presence". **No:** "Improve conformance check".
- Title ≤ 80 chars where possible.
- Title starts with the verb. **Yes:** `"Resolve phantom invariant #<N>"`. **No:** `"The phantom invariant <N> resolution"`. (Use `<N>` as placeholder in examples — referencing a literal number would make this skill file itself a phantom claim under the scanner it depends on.)

## Step 4 — Output for review (don't auto-fire)

Print:

```
PROPOSED STORY

Title:    <title>
Team:     <inferred>
Project:  <inferred>
Parent:   <inferred or 'none'>
Priority: <inferred or 'medium'>
BlockedBy: <inferred or 'none'>

---

<full description body>

---

To create, confirm or edit and I'll call save_issue.
```

Wait for user confirmation before invoking `save_issue` via Linear MCP.

**ONE exception**: if the user's invoking message includes "fire it" / "ship it" / "go", skip the review and create immediately.

## Step 5 — After creation

Echo the new Linear ID and URL. If the new story should be referenced in any other recent artifact (an ADR, a doc), surface that as a follow-up note.

## Anti-patterns

- **Don't use vague verbs** in the title — *"Improve X"* → *"Tighten X to reject Y"*; *"Update Z"* → *"Replace Z with W"*.
- **Don't write Definition of Done as "the feature works"** — name observable signals.
- **Don't put implementation detail in Goal** — Goal is the outcome; Scope is the how.
- **Don't omit Source** — every story should trace back to a CCR finding, a doc, a phantom catch, an ADR, or a user request.
- **Don't draft for a project that doesn't exist** — confirm the project name resolves before firing.
- **Don't pile in optional sections** — every section costs review attention; only include what's relevant.
