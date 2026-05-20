# The Choice

Every person at every event chooses how they participate:

- **Named** — your name is on it, you're visible, you chose to be known
- **Anonymous** — you're counted but not identified
- **None** — you just showed up

This document defines the rules that make that choice real in the code.

---

## How It Works in 30 Seconds

Every product declares its identity mode in CLAUDE.md:

```
identity_mode: anonymous    ← OSE (events, scans, sponsors)
identity_mode: named        ← OW (playlists, profiles, stories)
identity_mode: both         ← OurAirwaves (white-label, supports The Choice)
```

The brain contract reads this declaration and runs the matching checks. If the code doesn't match the declaration, CI fails.

---

## Three Contracts

### 1. Anonymous Contract — "We never know who you are"

For products like OurSharedEvents where privacy is the architecture.

| Rule | Plain English |
|------|--------------|
| **A-1** No personal info in the main database | Names, emails, phone numbers — none of it touches the event data |
| **A-2** Personal data lives in a separate database with a timer | Registrations expire in 90 days. Emails in 30. Automatic. |
| **A-3** Scans are anonymous by design | We record THAT someone was there, WHEN (roughly), and WHERE — never WHO |
| **A-4** Every piece of personal data has an expiration date | Nothing lives forever unless it's anonymous |
| **A-5** Personal data is encrypted at rest | Even if someone breaches the database, they get scrambled data |
| **A-6** A cleanup job runs on schedule | Expired data actually gets deleted, not just marked |
| **A-7** The two databases never talk to each other | You can't join anonymous scans to personal registrations. Ever. |
| **A-8** Timestamps are rounded to 15-minute windows | You can't pinpoint exactly when someone scanned |

### 2. Identity Contract — "You chose to be known"

For products like OurWKRP where people plant their flag.

| Rule | Plain English |
|------|--------------|
| **I-1** Every contribution is attributed | Your name is on the tracks you brought. Always. |
| **I-2** Provenance is tracked | We know where it came from — Spotify, CSV, manual — and when |
| **I-3** Roles are earned, not declared | You start as a contributor. You become a curator by curating. A DJ by DJing. |
| **I-4** Sessions are secure | Your identity is protected by HttpOnly cookies, not JavaScript |
| **I-5** Identity actions require a name | Browse the catalog anonymously. But to add music, you need to be you. |
| **I-6** One catalog, deduplicated | If Matt and P both bring the same song, it exists once with both names on it |
| **I-7** No platform lock-in | Your music identity works whether you use Spotify, Apple Music, or a CSV file |
| **I-8** Be honest about limitations | If Spotify only allows 5 users, say so. Don't hide it. |

### 3. Bridge Contract — "The person decides"

For moments when both layers exist at the same event.

| Rule | Plain English |
|------|--------------|
| **B-1** The choice is always offered | At check-in: Named, Anonymous, or Skip. Every time. |
| **B-2** The choice is enforced in the code | Named data goes to the identity layer. Anonymous data goes to the anonymous layer. They never cross. |
| **B-3** Anonymous means anonymous forever | No query, no report, no clever join can connect an anonymous scan to a named person |
| **B-4** Sponsors see the total, not the split | The SharedReport shows "42 people attended" — not "30 were anonymous and 12 were named" |
| **B-5** The choice is per-event | You can be Named at bocce on Thursday and Anonymous at the Sunday dinner. Your call. |
| **B-6** The default is anonymous | If you don't actively choose, you're counted but not identified |
| **B-7** History is history, the future is free | You can't undo a past Named check-in. But you can choose differently next time. |

---

## Which Products Follow Which Rules

| Product | Mode | What applies |
|---------|------|-------------|
| **OurSharedEvents** | Anonymous | Universal rules + Anonymous Contract |
| **OurWKRP** | Named | Universal rules + Identity Contract |
| **OurAirwaves** | Both | Universal + Anonymous + Identity + Bridge |
| **OurSharedRings** | Anonymous (read-only) | Universal + Anonymous (reads data, doesn't write) |
| **OurSharedGames** | Both | Universal + Anonymous + Identity + Bridge |
| **OurSharedRecords** | Named | Universal + Identity (stories are always attributed) |
| **OurPulse** | Named | Universal + Identity (belts require a name) |
| **OurSharedMagnets** | Internal | Universal only (tooling, no user identity) |

---

## Universal Rules (Every Product)

These apply to everything, regardless of identity mode:

| Rule | Plain English |
|------|--------------|
| **U-1** Security basics are in place | CORS, CSP headers, rate limiting — the baseline |
| **U-2** CI pipeline exists | Typecheck, lint, security scan on every PR |
| **U-3** The product knows what it is | CLAUDE.md exists and declares its identity mode |
| **U-4** Tests exist at every layer | Unit, integration, and smoke at minimum |
| **U-5** Standards are current | The OCR-docs standards match what's in this repo |
| **U-6** No secrets in the code | Automated scanning catches leaked credentials |
| **U-7** The Choice is declared | Every product says: I'm anonymous, named, or both |

---

## The One Test That Matters

For any new feature, in any product, ask:

1. Does this feature know which identity mode it's in?
2. Does the data go to the right place?
3. If it touches both layers, does it follow the Bridge rules?
4. **Can the person still choose?**

If the answer to #4 is no, the feature is wrong. Redesign it.

---

*The Choice is not a policy. It's architecture. The brain contract enforces it. CI validates it. Every commit, every product, every time.*
