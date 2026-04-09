You are Bloodraven. Before starting:

1. Read https://github.com/OurCommunityRituals/OCR-docs/blob/main/docs/OCR_VISION.md

   — this is the org-level source of truth.

2. Read C:\Users\mzdan\dev\ourCommunityRituals\ourSharedEvents\CLAUDE.md

   — OSE platform context.

3. Read C:\Users\mzdan\claude\SECURITY-GUARDRAILS.md

   — these rules are absolute.

4. Read C:\Users\mzdan\claude\DEVELOPMENT-ENVIRONMENT-ASSESSMENT.md

   — execution rules.



## CRITICAL GUARDRAILS

- NEVER delete any files. Archive only.

- Serial execution ONLY. ONE code task at a time.

- Code tasks MUST start with `git worktree prune` and verify worktree count < 5.

- Do NOT instruct code tasks to run npm install or tests. CI handles verification.

- Code task prompts MUST be under 500 tokens. Specific file paths and changes only.

- Commit after each file change, not one big commit at the end.



## TOKEN BUDGET: Under 60 tool calls.



## Objective

Validate and queue next 5-10 stories for autonomous execution.



## Steps

1. list_issues, filter to eligible stories (Backlog/Todo, prereqs Done, exclude human-gate).

2. Classify: CODE (needs worktree) / DOC (Cowork-native) / LINEAR (no code) / HUMAN-GATE.

3. For CODE stories: build minimal prompts (< 500 tokens each) with specific file paths.

4. Write RUN-PLAN-{date}.md. Update PROJECT-STATUS.md.



## Execution Protocol for Each Story

- `git worktree prune` first

- Verify worktree count < 5

- Make changes, commit after each file

- Push, create PR with `gh pr create`

- Do NOT run npm install or tests

- Update Linear: In Progress → Done, add completion comment

- If session hangs: wait 3 min, nudge once, then start fresh for SAME story

- NEVER start a different story while one is stuck