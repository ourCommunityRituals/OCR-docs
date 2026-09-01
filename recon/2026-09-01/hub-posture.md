# hub-posture — ourCommunityRituals dependency, secrets, and agent-trust posture

> **Agent:** `posture-scanner` · **Date:** 2026-09-01 · **Repo:** ourCommunityRituals @ `84db6b7` · Wave 6
> First audit this repo has ever had. **Lead verification:** all claims re-checked. Confirmed.

## The headline is a clean bill on the thing it was sent to find

**The hub does NOT have the ourSharedEvents credential pattern.** Every `ci.yml` job carrying `OCR_PROPAGATE_TOKEN` sets `persist-credentials: false` on both its checkouts — `gate` (`:101`), `invariants` (`:214`), `brain-parity` (`:283`), `shared-gate-drift` (`:366`) — with `permissions: contents: read` declared workflow-wide. **Verified: eight `persist-credentials: false` in `ci.yml`.** `pnpm install` runs later in `gate`, but with no persisted credential to take. This is the discipline OSE's two deploy jobs lack, already implemented here.

## Gate Queue

**1. Semgrep never runs on this hub's own source.** `security-bracket.yml` is a reusable `workflow_call` for spokes; nothing in `ci.yml` calls it. Its only caller, `security-bracket-selftest.yml`, is path-filtered to changes in the bracket files themselves (`:26-30`). An ordinary PR touching `packages/runner-fleet` (handles GitHub tokens) or `packages/flags` (published externally) gets **zero SAST coverage**. Not a bypass of a gate — a gate never wired to the code it protects.

**2. L0 secret-pattern scanning covers `packages/flags` only.** `level0_security.py:24-30` scopes `PKG_ROOT` to that package. The vendored `security_gate.py` patterns (GitHub PAT/OAuth/app tokens, AWS, Slack, JWT-shaped, OpenAI-shaped) therefore never run against `tokens`, `ui`, `runner-fleet`, `data-provider`, or root scripts. Manual grep found no secret in those paths today; nothing rechecks that going forward.

**3. `publish-flags.yml:55` is the one checkout in the repo without `persist-credentials`.** Left at its default of `true`, on the job holding a `packages: write` token. Mitigating: the credential is the ambient `GITHUB_TOKEN`, and `packages/flags/package.json` declares no `prepublish`/`prepack`/`postinstall`, so `npm publish` executes no injected dependency code. Still the only checkout that departs from the workspace's own stated pattern, on its most privileged job.

**4. The runner-fleet operational CLI depends on an undeclared `tsx`.** Root scripts `runner-fleet:{status,watch,dashboard,bounce,register}` (`package.json:23-27`) run `node --import tsx/esm src/cli.ts`, but `tsx` is declared nowhere for that package or at the root — only in `packages/tokens` and `packages/ui`. These are the token-rotation and re-registration scripts for the self-hosted runner fleet. Drop `tsx` from either unrelated package and this operational tooling breaks with nothing in the dependency graph pointing at why.

**5. Two local ops scripts are tracked in git despite `.gitignore` saying they never should be.** `_provision-runner-4.ps1` and `_reregister-runner-3.ps1` are **verified tracked** (`git ls-files`), while `.gitignore` carries `/_*.ps1` with the comment that such scripts "carry local paths/creds and are never part of the repo." A `.gitignore` rule added after a file is committed does not untrack it. They hold no live secret, but they expose a local username, local filesystem layout, and self-hosted-runner topology — and they target **ourSharedEvents'** runner fleet from inside the hub, which is a scope-boundary leak in a repo that keeps the estate's sibling repos deliberately separate.

## Appendix

- **`fleet.config.json` is clean.** Correctly gitignored, confirmed via `git check-ignore -v`; `git log --all -p` found no `ghp_`/`github_pat_` pattern anywhere in history. `src/{token,github,watchdog,cli,dashboard}.ts` reviewed line by line: tokens pass through typed fields into `Authorization: Bearer` headers and a discrete `execFile` argv element (deliberately not shell-interpolated). `dashboard.ts` renders only status, error code and timestamp.
- **`.claude/` trust surface.** No `settings.json`, no hooks, no `mcpServers` anywhere. Six agent definitions, none granting `Edit`, `Write`, or `Agent`; the only network-capable grant is `board-reconciler`'s three read-only Linear tools. The README documented four workers while six exist — **fixed this session**.
- **Dependency drift.** Two full vitest majors installed side by side: `2.1.9` for `tokens`/`ui`, `3.2.7` for `flags`/`runner-fleet`/`data-provider`. `packages/ui` declares `tailwindcss: ">=3.4.0"` as an unbounded optional peer while `.npmrc` sets `auto-install-peers=true` and `resolution-mode=highest`, so pnpm resolves `tailwindcss@4.3.3` — and `packages/ui/src/tailwind.ts` exports a v3-style JS preset, which v4's CSS-first config model only partially supports.
- No genuinely unused `package.json` entries found in any package.

## The self-report that mattered

Asked to list its Bash commands and any refusals, this worker reported running `find`, `cat`, `grep -r`, `ls`, `git ls-files`, `git tag -l`, `git check-ignore`, and `git log --all -p` — none refused — and stated that **its runtime grant was the full unscoped `Bash` tool, not the `Bash(git log:*)` declared in its own definition.** It noted this is exactly the failure `.claude/README.md` asks an operator to verify before Wave 1. See runbook §8.7; that finding is now the fleet's own top item.
