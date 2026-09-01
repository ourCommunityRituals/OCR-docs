# hub-pyramid — ourCommunityRituals CI/CD ↔ test pyramid, four traversals

> **Agent:** `pyramid-tracer` · **Date:** 2026-09-01 · **Repo:** ourCommunityRituals @ `84db6b7` · Wave 6
> **Lead verification:** all three top claims re-checked. Confirmed.

## Gate Queue

**1. `publish-flags.yml` can publish untested `@ocr/flags` from any ref.**
**Verified: the workflow contains zero `needs:` keys.** It is a sibling workflow, not a downstream job — nothing in it checks that `ci.yml` passed on the SHA being published. Its `workflow_dispatch` trigger accepts any ref carrying the file, so a feature branch that never opened a PR, never ran the gate, never ran invariants or brain-parity, can publish to GitHub Packages. The only guards are the `dry_run` input and the `packages: write` permission — neither is a test gate. `@ocr/flags` is the source the conformance meter is generated from and is consumed by OSE.

*Note on the fix:* `ci.yml`'s push filter covers `packages/**`, so it does run on the publishing SHA — but both workflows trigger on the *same* push, so a naive status read races a still-running gate. A correct fix needs a wait-with-timeout loop, not just a status query. Not attempted here; it cannot be validated without executing Actions.

**2. `packages/runner-fleet/README.md:100-104` claims a CI job that does not exist.**
> *"Changes to `packages/runner-fleet/**` trigger the `runner-fleet` job in `../../.github/workflows/ci.yml`."*

**Verified:** `ci.yml` has exactly four jobs — `gate`, `invariants`, `brain-parity`, `shared-gate-drift`. There is no `runner-fleet` job, and `runner-fleet:test`/`:typecheck` appear in no workflow. This is the most dangerous false-green shape: not a gate that passes silently, but **documentation asserting a gate exists**, which stops a reviewer looking for one.

**3. Four of five packages have real test suites wired to nothing.**
**Verified: zero hits for `runner-fleet`, `tokens:test`, `tokens:check`, `@ocr/ui`, or `data-provider` across all workflows.** `packages/tokens` (2 test files + `check:generated` byte-compare + `check:raw` policy gate), `packages/ui` (5 test files, no root proxy script at all), `packages/runner-fleet` (5 test files), `packages/data-provider` (no tests, no tsconfig, excluded from type-aware lint). A merge to `packages/tokens/**` can land with failing tests and stale generated CSS and still show all-green required checks — and `@ocr/tokens` feeds `@ocr/ui` and OSE's Worker, so drift propagates silently downstream.

**4. Typecheck covers one package.** `tsc --noEmit` runs against `packages/flags` only. `data-provider` has no `tsconfig.json` at all — the only package with zero type-checking of any kind. Documented in `BACKLOG.md:99-106`, still open.

**5. `packages/flags`' own chain is genuinely sound — recorded so the contrast is on the record.** L0 security, L2 drift (`check:generated` is a real byte-compare against regeneration output, not a self-referential match), root lint across all five packages, `tsc`, and `flags:test:gate` all reach the blocking `gate` job. `invariants` fails closed if the brain checkout is missing rather than skipping (`invariants.test.ts:57-61`). `brain-parity` and `shared-gate-drift` hard-fail on an absent checkout — the COST-201 false green, verified closed.

## Not false greens, assessed and cleared

- **`.gitattributes` LF-forcing** on `packages/flags/src/generated/*.ts` exists to prevent a false *red* (Windows autocrlf drift), not to manufacture a green. Vestigial since the ubuntu-latest migration, harmless.
- **`pnpm-workspace.yaml` / `.npmrc` `# nosemgrep`** suppressions are honestly labelled as *not enforced* — the comments state real enforcement needs pnpm ≥10.16 and an audited allowlist, tracked under OSE-1089, and that adding those keys to pinned `pnpm@9.15.0` "would be a no-op that only LOOKS hardened." An admitted absence with a ticket, not a false green.
- **`security-bracket.yml`** contributes zero enforcement to this hub, but says so in its own header. Disclosed, not hidden — though see `hub-posture.md` Gate #1 for why that still leaves the hub unscanned.
