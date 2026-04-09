# AC Audit — OSE-12 (P1-7): Secrets + First Staging Deploy

> **Status:** RECOMMEND CLOSE — prerequisites complete, AC updated below
> **Flagged by:** Bloodraven sync (2026-04-09) — stale AC referencing GAS/Sheets artifacts
> **Original problem:** AC listed `GOOGLE_SA_CLIENT_EMAIL`, `GOOGLE_SA_PRIVATE_KEY_PEM`, `SHEETS_SPREADSHEET_ID` as required secrets. These are obsolete since the D1 pivot.

---

## What changed

OSE completed Phase 2 (D1 migration). The following are now Done:

- **OSE-16** (D1 database creation + schema migrations) — completed 2026-04-08
- **OSE-129** (Doppler secrets management) — completed 2026-04-06
- **OSE-161** (`/api/v2/events` 503 fix) — completed 2026-04-07

All Google Sheets secrets have been removed from active code, CI, and wrangler config. Only stale references remain in archived files (`deploy-manifest.json`, `.github/workflows/archive/`).

---

## Updated acceptance criteria

### GitHub Actions Secrets (3 required)

- [ ] `CLOUDFLARE_API_TOKEN` — scoped: Workers:Edit, Workers Routes:Edit, Account Settings:Read
- [ ] `CLOUDFLARE_ACCOUNT_ID`
- [ ] `ADMIN_KEY` — Bearer token for `/admin` endpoints

### Cloudflare Worker Secrets (2 required, staging env)

- [ ] `ADMIN_KEY` set via `wrangler secret put ADMIN_KEY --env staging`
- [ ] `FORMS_ENCRYPTION_KEY` set via `wrangler secret put FORMS_ENCRYPTION_KEY --env staging` (AES-GCM, 32+ chars)
- [ ] `wrangler secret list --env staging` shows both secrets

### D1 Staging Databases

- [ ] Main DB (`ocr-db-staging`, ID `4c4381db-...`) — migrations applied, 6 tables verified: `events`, `sponsors`, `poster_deployments`, `scans`, `scan_aggregates`, `subscribers`
- [ ] Forms DB (`ocr-forms-db-staging`, ID `ff1cb46d-...`) — migrations applied, 5 tables verified: `form_registrations`, `checkin_counts`, `form_surveys`, `email_signups`, `feature_flags`

### Staging Deploy

- [ ] CI triggers on push to main (Job 02: Deploy to Staging)
- [ ] D1 migrations applied to both databases via CI
- [ ] `npm run deploy:staging` completes without error
- [ ] `https://stg.oursharedevents.com/health` returns `{ "ok": true, "env": "staging" }`
- [ ] Post-deploy functional smoke passes (Job 03b: API + UI + Newman)

### Cleanup (confirmed complete)

- [x] No Google Sheets secrets in active code or CI
- [x] No `GOOGLE_SA_CLIENT_EMAIL`, `GOOGLE_SA_PRIVATE_KEY_PEM`, `SHEETS_SPREADSHEET_ID` anywhere in production paths
- [ ] Optional: update `deploy-manifest.json` to remove archived secret references

---

## Recommendation

This story is a **documentation close**, not a code task. The infrastructure work is done (OSE-16, OSE-129, OSE-161). Update the AC in Linear to match the above, verify the checkboxes, and close OSE-12.

Estimated effort: 30 minutes.

---

*Reviewed: April 9 2026*
*Source: OSE codebase audit — CLOUDFLARE_SECRETS.md, wrangler.toml, CI workflow*
