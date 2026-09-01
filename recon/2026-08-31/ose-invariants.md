# ose-invariants — ourSharedEvents against the OCR invariant register

> **Wave:** 1 (calibration) · **Agent:** `invariant-sweeper` · **Date:** 2026-08-31
> **Repo:** ourSharedEvents @ `14f5c3b` · **Register:** `ocr-docs-brain/architectural-invariants.yaml`
> **Scope:** the 23 of 25 invariants carrying `ose` in `applies_to` (excludes #13, `applies_to: []`, and #20, `[ocr]`)
> **Lead verification:** all five Gate items re-checked directly. All confirmed. See §Verification.

## Gate Queue

**1. #5 `tier_equity` — the covenant's only deployed-worker proof has been dark for 3½ months.**
Layers (a)–(e) are code-shape, pure-function and in-process. Layer (f) — the T3 Newman contract test (`postman/collections/ose-api.json` §11) that asserts the covenant against the live `stg.oursharedevents.com` API — has been red since **2026-05-19**, per the register's own `activation_note`. Still live in the tree today: `oursharedevents-ci.yml:1109` carries a *"CF Access preflight probe (OSE-349) — diagnostic only, does not gate"* whose comment warns the Newman smoke will fail on the OSE-INV5 covenant seed and *"Do not re-run blindly — fix the service token first."* The diagnostic exists because the fix never landed. The register is honest (`status: partial`), but this is the highest-consequence gap in the sweep: the commercial covenant has had no behavioural proof against a running worker for a quarter.

**2. #23 `red_team_coverage` — a complete 1,847-line adversarial suite exists and is wired to nothing.**
`tests/red-team/{auth-attacks,data-exfiltration,input-injection,rate-limit-live,security-headers}.spec.ts` — five files, 1,847 lines, with matching `npm run test:red-team*` scripts. **Zero references to `red-team` in any file under `.github/workflows/`.** Not to the suite, not to `playwright.red-team.config.ts`, not to the directory. This is precisely the failure mode invariant #10's own text names — a guard that lives in scripts but is never invoked by CI is theatre. `partial` / "in construction" undersells it: the tests are written and runnable *today*. The gap is one workflow step wide.

**3. #24 `auditability` — the register's named enforcement test does not exist, and the table it would guard stores operator IP and email.**
`test_file: tests/audit-layer.spec.ts` is **ABSENT** from the repo (verified). Migration `0026_create_admin_audit_log.sql` declares `actor TEXT` (its own comment: "Email (CF Access), 'key:admin'…") and `ip TEXT`, both written by `logAdminAction()` in `src/lib/audit-log.ts`. The register's `protective_statement` says the audit layer "must never become a re-identification surface… enforced by tests that attack the logs." No such test exists. Under the register's "audit operators, never attendees" doctrine this is in-bounds by design — but the boundary is **asserted, not tested**, and it is the one place identity is deliberately retained.

**4. The register carries real enforcement it does not know about — the banned-term lexicon is invisible to the brain.**
`workers/oursharedevents/src/lib/schema-lexicon.ts` and `workers/oursharedevents/tests/schema-lexicon.spec.ts` (OSE-801) read the live D1 schema via `sqlite_master` / `PRAGMA table_info` and fail on any table, column, index, view or trigger identifier tokenizing to a banned word (`attendance`, `impression(s)`, `visit(s)`, `reach`, `unique`, `turnout`, `eyeball(s)`, `people`, `view(s)`), with tracked, ticketed exemptions (`sponsor_impressions` → OSE-931, `visit_count` → OSE-932). It is PR-blocking via the T0 `tests` shard. **The register mentions it zero times** (verified: 0 hits for `schema-lexicon` in the YAML). A second unlisted mechanism exists too: `tests/e2e/0-architecture/cost-metric-never-who.invariant.spec.ts` seals `OperationCostMetric` to seven aggregate keys and forbids identifier tokens by word boundary, also in the T0 `invariants` shard.

This inverts the agent's usual finding. The gap is not prose-without-enforcement; it is **enforcement the law has no record of**. The register undercounts OSE's real coverage, which means the conformance meter built on it is measuring the wrong denominator.

**5. Two register entries are stale in opposite directions, and both mislead.**
- **#21 `shared_report_schema_stability` contradicts itself.** Top-level `status: live`; its own `activation_note` says *"Status PARTIAL (honest)… cannot be committed without the campaigns feature TS changes… not yet wired to CI."* Reality matches the status field: the spec, `shared-report.snapshot.json`, and the campaign fields in `shared-report-builder.ts` all exist and run in the T0 `invariants` shard. The prose is stale.
- **#25 `sponsor_share_covenant` under-claims.** Its `test_file` reads *"…(OSE repo — planned, OSE-663 / OSE-662)"*. The file exists (8,887 B, verified), is fully implemented — 5 code-shape tests plus a WALL-3b template-geometry sub-suite guarding against tier-keyed CSS dimensions on `display/poster/public/shared-report.html` — and is wired into T0 alongside four sibling sponsor specs. **No code path lets a sponsor buy a named slot or a size:** `allocateShares()` in `src/lib/sponsor-allocation.ts` returns only `{id, sharePct}` with no size/slot/position field by construction; `sponsors.ts` forces `placement_formats` non-writable on update; `is_local` is derived server-side from an h3_res7 corridor-cell match, never from the request body.

A reader trusting either entry's prose over the code would draw the wrong conclusion — in #21's case that a live invariant is unenforced, in #25's that the covenant is merely planned.

---

## Full classification — 23 ose-scoped invariants

| # | Name | Register | Verdict | Evidence |
|---|---|---|---|---|
| 1 | anonymous_id | live | MECHANICAL — PR-blocking + T4 runtime | `architecture.spec.ts`, `pii-invariant.spec.ts`, `testid-pyramid.spec.ts` in T0; `anonymous-id.invariant.spec.ts` T4-only by design |
| 2 | hyperlocal_geo_resolution | live | MECHANICAL, split — demo-geo PR-blocking, core resolution T4-only | migrations 0019–0021; `geo-resolution.invariant.spec.ts` **not** in T0 list; `riph-brain-conformance.spec.ts` is PR-blocking |
| 3 | uec_encoding | live | MECHANICAL — PR-blocking | `uec-substrate-static-gate.spec.ts`, `uec-drift-check.spec.ts` in T0 (with brain checkout); `uec-codes.invariant.spec.ts` T4-only |
| 4 | ncr_data_accumulation | live | MECHANICAL, split — PII gate PR-blocking, accumulation T4-only | `ncr-accumulation.invariant.spec.ts` not in T0; `pii-invariant.spec.ts` is |
| 5 | tier_equity | partial | **MECHANICAL, split — deployed layer RED 3½ months** | Gate #1 |
| 6 | inert_monetization_hooks | live | MECHANICAL — PR-blocking + T3 | `monetization-inert.invariant.spec.ts` in T0; `X-Monetization-Inert` ×3 in both Postman collections |
| 7 | aggregate_only_reporting | partial | MECHANICAL — PR-blocking | `aggregate-only.invariant.spec.ts` at `ci.yml:665`; `COUNT(DISTINCT anon_id_hash)` only |
| 8 | bounded_pii_retention | live | MECHANICAL — PR-blocking, self-protecting | `pii-retention.invariant.spec.ts`, `lifecycle.spec.ts`, cron in `wrangler.toml`, placement guard in `infra-consistency.test.js` |
| 9 | tenant_isolation | partial | MECHANICAL — PR-blocking | `tenant-isolation.invariant.spec.ts` (T0) + `tenant-isolation.spec.ts` (L1) |
| 10 | deprecation_lock | live | MECHANICAL — PR-blocking | `guard-no-gas.js` + allowlist + test; lint shard runs both |
| 11 | self_hosted_runner_bash_resolution | live | MECHANICAL — PR-blocking on self-hosted | `runner-env-validation.yml`, `tools/runner/*.ps1` |
| 12 | runner_pool_readiness_probe | live | MECHANICAL (structural only — runtime self-healing not source-verifiable) | `tools/runner/{janitor,install-janitor-tasks,janitor.tests,verify-probe-alive,setup-runner}.ps1` |
| 14 | mobile_workability | partial | **MECHANICAL but weak** — nightly-blocking, PR advisory and path-filtered | `mobile-workability-audit.yml`: `continue-on-error` on PR, blocking only on schedule/dispatch; PR trigger scoped to 4 paths → up to 24h signal lag |
| 15 | cors_allowlist_immutability | live | MECHANICAL — PR-blocking | `cors-allowlist.invariant.spec.ts` (T0); `cors.ts` explicit `Set`, no wildcard |
| 16 | api_response_schema_stability | live | MECHANICAL — PR-blocking | spec in T0; `public-events.snapshot.json` |
| 17 | oer_emission_boundary | live | MECHANICAL — PR-blocking; one reference doc missing | spec in T0; `wrangler.toml` clean (no `[[services]]`); **`docs/architecture/OCR_ARCHITECTURE_oerAggregationBoundary.md` cited in `references` does not exist** — doc drift, not an enforcement gap |
| 18 | slug_permanence | live | MECHANICAL — PR-blocking | spec in T0; `0001_create_events.sql` has `slug TEXT NOT NULL UNIQUE` |
| 19 | migration_monotonicity | live | MECHANICAL — PR-blocking | spec in T0 |
| 21 | shared_report_schema_stability | live *(prose contradicts)* | MECHANICAL — PR-blocking; **register internally inconsistent** | Gate #5 |
| 22 | cross_repo_import_isolation | live | MECHANICAL — PR-blocking | `check-cross-repo-imports.sh` invoked by name in `brain-contract-check.yml` |
| 23 | red_team_coverage | partial | **PROSE-with-code — zero CI wiring** | Gate #2 |
| 24 | auditability | partial | **PROSE** for the log-attack claim; MECHANICAL for the tables | Gate #3 |
| 25 | sponsor_share_covenant | live *(test_file stale)* | MECHANICAL — PR-blocking, register under-claims | Gate #5 |

**Tally:** 20 MECHANICAL (4 of them split or weak), 2 PROSE, 0 ABSENT, plus 2 register-integrity defects and 2 unregistered enforcement mechanisms.

## Targeted checks

- **Banned-term lexicon:** OSE **has** one — Gate #4. Untracked by the register.
- **"Never who, always how many":** no identity-carrying path found in reporting or aggregation surfaces; `shared-report-builder.ts` uses `COUNT(DISTINCT anon_id_hash)` exclusively. The single deliberate retention is `admin_audit_log.actor` / `.ip` — operator, not attendee, in-bounds by doctrine, untested (Gate #3).

---

## Verification (lead session)

| Claim | Result |
|---|---|
| red-team suite: 5 files, 1,847 lines, zero workflow references | ✅ confirmed — `wc -l` gives 1847; `grep -rn "red-team" .github/workflows/` returns nothing |
| `tests/audit-layer.spec.ts` absent | ✅ confirmed — repo-wide `find` returns nothing |
| `sponsor-share-covenant.invariant.spec.ts` exists despite "planned" | ✅ confirmed — 8,887 B on disk |
| `schema-lexicon.ts` + spec exist; register mentions them zero times | ✅ confirmed — both files present; 0 hits in the register YAML |
| CF Access probe still live in CI | ✅ confirmed — `oursharedevents-ci.yml:1109`, "diagnostic only, does not gate" |

## Calibration verdict

**Strongest signal of the four.** The prompt's most valuable output was not the PROSE/MECHANICAL split it was asked for — 20 of 23 came back MECHANICAL, which is a healthy repo — but the two directions it was *not* asked about: enforcement the register doesn't record (Gate #4) and register entries whose prose contradicts their own status (Gate #5). Fold both into §1.2 as explicit asks before Wave 2: *"report enforcement present in the repo but absent from the register"* and *"report register entries whose prose and status field disagree."*

**Open cross-report question:** this report reads the live CF Access probe as evidence OSE-349 was never fixed; `ose-board` found commit `96ba467` (2026-08-21) claiming *"Root cause of the recurring OSE-349/OSE-889 admin-auth failure — a code bug."* Either the fix landed and the probe plus the ticket are both stale, or the fix was partial and the T3 covenant layer is still dark. **Nothing in either report settles it, and it gates the highest-consequence item in the wave.** It is Gate item 1 of the rollup for that reason.
