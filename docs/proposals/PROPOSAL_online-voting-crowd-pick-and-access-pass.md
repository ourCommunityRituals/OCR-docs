# PROPOSAL: Include online people in voting without loosening the room

**Status:** proposed, for Matt's decision. Lives in `docs/proposals/`, so it does not propagate to spokes.
**Proposed:** 2026-11-26 · **Owner:** Matt
**Permission to build Online Pick:** Matt, 2026-11-26 05:22 UTC (project thread): "If 'Online Pick' means voting from outside the room, please check it with Matt before building it. I give permission." Online Pick is voting from outside the room, kept apart from Room Pick, so this is that check. The build still follows section 7: ADR-040 decision 13, then the CCR, then stories.
**Touches when built:** OSE ADR-040 (a new decision 13, amending decision 12's "remote or link voting is out").

## 1. What Matt asked for

Matt, 2026-11-26: "Event and sponsors will want to open voting to online, but this needs to be resisted
for this very reason. The physical in the room voting requirement is one of the first layer security
checks to maintain security and foster in person participation. While online would be better for
marketing and the bottom line, it also exposes privacy concerns and vastly more triggers and exposure
vectors."

Then: "Is there another way to include online users in voting in a safe manner?" Of the four options
offered, he said yes to writing up two together:

1. **A separate online result, the Online Pick**, always shown apart from the official **Room Pick**.
2. **An Access Pass**: a small, capped, logged way for someone who cannot be in the room to vote in the
   Room Pick.

Matt, same day: "I am one of the accessibility passes, so this hit for me." So the Access Pass is
designed from the voter's side first: dignified, low friction, no need to explain or prove anything,
and never a second-class vote.

## 2. What does not change

These hold for everything below. Nothing in this proposal loosens them.

- **The Room Pick is the official result, and it needs the room.** A Room Pick vote still needs a
  scan of the room's vote code (ADR-040 decision 6), now the rotating code chosen for OSE-2234 (PR OSE#1562).
  The only other way in is the Access Pass in section 4, which is capped and logged.
- **Never who, only how many** (OSE invariant 1). No new path stores a name, an email, a reason, a
  device id, an address or a location.
- **The under-5 floor** (OSE invariant 2). No new number below 5 is published, and the count of access
  passes is never published at all.
- **Results only after final, one result per set** (ADR-040 decision 7): the winner, or "too close to call,
  the champion retains", with the secret margin T and voter floor V. Nothing on the display before final.
- **Integrity in both directions** (Matt, 2026-11-26). No path lets a voter, sponsor, host or bot boost
  an entry, and none lets them bury or smear one.
- **Campaigns and sponsors stay out of the vote.** A sponsor can never open, close, issue or see anything
  in this proposal.

## 3. Part one: the Online Pick

### What it is

An optional second vote, run beside the room's, that anyone online can join. It has its own result. It
never touches the Room Pick, and the Room Pick never touches it.

### The rules

1. **Two channels, never mixed.** A vote set has a channel, `room` or `crowd`, fixed when it is made.
   The Room Pick is the `room` set. The Online Pick is a second set on the same event, on the same
   objects, with its own tallies, receipts, T and V. No query adds, compares or joins the two. No crowd
   number is ever a tiebreak, a weight, a bonus or a seed for the room. A gate test fails if any code path
   reads both channels' tallies, the way `votes-never-who` guards the vote tables today.
2. **The belt and the champion follow the room only.** "The champion retains" means the room's champion.
   The Online Pick has no belt and no title that carries over.
3. **Off by default, the host turns it on.** Per event. A sponsor cannot. The host's Voting card says what
   it is in one line: "Lets people who aren't here vote for fun. It never changes the Room Pick."
4. **The same publishing rules.** Winner only, or "too close to call", after final, with its own secret
   T and V. No per-entry number, no count of crowd voters, nothing on the display before final.
5. **Fixed words that no one can rename.** The labels "Room Pick" and "Online Pick"
   are platform text, like the plain titles on codes. A skin, a host or a sponsor cannot relabel them,
   hide the "for fun" note, or show the Online Pick above or larger than the Room Pick. This is the
   rail that stops the marketing pull Matt warned about: the crowd result can never be dressed up as the
   real one.
6. **How an online vote is counted.** The event page offers a "Vote in the Online Pick" link while the
   crowd set is open. The link goes through `/q`, which stays the only cookie reader (OSE invariant 4),
   and mints a crowd pass the same way the room pass works (sealed, in the fragment, held in memory,
   30 minutes), under its own key label, so dedup is one vote per entry per browser. That is weak on purpose, and the page says so: "Anyone can vote here, so this can
   be gamed. That's why it's for fun and never the official result."
7. **Its own flood flag.** The crowd set gets its own flood counter (the OSE-2234 mechanism) at a higher
   threshold. A flooded crowd set shows "may be padded" beside its result. It never flags the room.
8. **On-site still wins the night.** The Online Pick closes when the Room Pick closes, so it cannot be
   announced first, and both results come out together.

### Why this is safe for the room

The room result is computed from room tallies only. A bot farm, a sponsor's mailing list or a host's
friends can win the Online Pick, and the Room Pick does not move. Section 5 checks each way that could
fail.

## 4. Part two: the Access Pass (vote in the Room Pick from elsewhere)

### What the voter sees

1. They ask the host, any way they like (a text, a word in advance, a message on the event page). They
   never give a reason. No form asks for one, and the host is told not to ask.
2. The host taps **"Give an Access Pass"** on the Voting card. OSE shows a link and a QR code once. The
   host sends it however they like. OSE never learns who it went to.
3. The voter opens the link when voting opens. They land on **the same voter page** as everyone in the
   room: the same list, the same house rule, the same buttons. One small line says: "You're voting with
   an Access Pass. Your vote counts the same as everyone in the room."
4. Their vote is a normal Room Pick vote: the same receipt, the same weight, the same tally. Nothing in
   the tally or the result marks it as different. It is never a second-class vote.
5. They can come back to the link all night, from any device. Each opening renews their pass, like a
   re-scan in the room. It always gives the same voter key, so it is always one voter.

The words are "Access Pass", never "disability pass". It fits illness, a seizure day, caregiving,
mobility, distance, anything. The person decides whether they need it.

### How it works

- **A pass is a token, not a person.** 128 random bits, made by the host's admin action, scoped by brand
  (`guardAdminObjectScope`). Its URL carries it in the path, like the vote code.
- **One pass, one voter.** Redeeming it mints the same sealed vote pass as the room code, but the voter
  key comes from the token: `k = HMAC(K_access, token ‖ event_id)`, under its own HKDF label. So a
  forwarded or shared pass still gives one vote per entry, never more. Sharing it gains nothing.
- **Only while the event is live and the room set is open** (ADR-040 decision 11). A pass can be given
  in advance, while the set is in draft, so the voter has it ready.
- **The host can take a pass back.** Revoking stops new votes from it. Votes already cast stay, because
  a receipt has no side and is not linked to the pass.
- **A cap per vote set.** Proposed default: 4. Section 6 asks Matt to confirm. Why 4: the smallest secret
  margin is 5, so passes alone can never turn a tie into a winner. They can still help a close lead
  across the line, the same as 4 people walking in. Pass voters count on top of the host's room size,
  so a full room never locks a pass holder out.
- **Logged, never published.** Each give and revoke goes in the admin audit log with the host's admin
  identity and the time. Hosts are on the named side, so this is allowed. The recipient is never
  recorded. The count of passes is never published, to anyone, because it is always under 5.
- **No free text.** The pass has no name field, no note field and no reason field. So no health
  information can ever be typed into OSE.
- **The report says only that passes were available.** After final, the result may say "Access Passes
  were available for this vote" if the host had any to give. Never a number.

### Host abuse, and what stops it

A host could give passes to themselves or friends to push an entry. The rails:

1. **The cap.** At most 4 extra voters per set, below the smallest margin.
2. **No information to aim with.** A host sees no count before final (ADR-040 decision 7), so they
   cannot see who is behind or by how much.
3. **A named trail.** Every give and revoke carries the host's admin identity. A host who gives the full
   cap night after night shows up in the platform's review (OCR, not the host's own view), as a pattern
   to look at, never as an accusation on a public page.
4. **Not a sponsor tool.** Only an event admin of the brand can give a pass. Sponsor roles cannot.
5. **The room still decides.** A room of 20 outvotes 4 passes. On a tiny night, V (10 to 14 voters)
   still has to be met, and the house rule card already says a small group can sway a small night.

## 5. Threat check (STRIDE + LINDDUN) on the new paths

The three new paths are: **C** the Online Pick, **G** giving an Access Pass, **R** redeeming one.

### STRIDE

| Threat | Path | What could go wrong | Control | Left over |
|---|---|---|---|---|
| Spoofing | C | Bots or many browsers vote many times | Per-browser dedup, flood flag, "for fun" label, room never reads it | Crowd result can be bought. Accepted: it is labelled as such |
| Spoofing | R | Someone uses a pass that is not theirs | One pass is one voter key; sharing gives no extra votes; host can revoke | The holder of the link votes in place of the intended person, as with a forwarded room pass (ADR-040 decision 9) |
| Spoofing | G | A sponsor or another brand gives passes | Event admin role only, brand scope, write guard | None known |
| Tampering | C | Crowd tallies leak into the room result | Channel fixed at creation; gate test that no path reads both channels | A future code change. The gate is the control |
| Tampering | G | A host stacks passes to push an entry | Cap 4 (below smallest T), no counts before final, named audit, platform pattern review | A host can still nudge a close night by up to 4. Accepted if Matt keeps the cap |
| Tampering | R | Guessing a pass token | 128 random bits, rate limit at the route | None in practice |
| Repudiation | G | A host denies giving passes | Audit row per give and revoke, with the admin identity | None |
| Info disclosure | C, R | The crowd result or a pass reveals how the room voted | Separate T and V per set; results only after final; no counts | Same residual rates as ADR-040 decision 7, per set |
| Info disclosure | G | The pass count reveals who needed one | Count never published; no recipient stored | The host knows who they gave passes to. That is outside OSE, as it is today |
| Denial of service | C | A crowd flood slows the room's vote | Own rate limit and flood counter per channel; room path unchanged | Shared Worker capacity. Same as any public read |
| Denial of service | R | A host revokes a pass to silence one voter | Logged, named | A bad host can do this. Pattern review can catch it |
| Elevation | G | A host raises their own cap | Cap is a platform setting, not a host or skin setting; OA tiers never touch it | None |

### LINDDUN

| Threat | Path | Risk | Control |
|---|---|---|---|
| Linking | R | Linking a pass holder's votes across events | Key is per token and per event; a pass works for one event only |
| Linking | C | Linking a crowd voter to a room voter | Separate keys under separate HKDF labels; no join across channels |
| Identifying | G | The pass becomes a list of disabled people | No name, no reason, no note, no recipient stored. Only "a pass was given by this host at this time" |
| Non-repudiation | R | A voter cannot deny voting | No vote row, no vote time, receipts deleted at final (ADR-040 decision 1) |
| Detecting | G | The page or result marks someone as a pass voter | Same page, same tally; the report never shows a count |
| Data disclosure | G | Health information typed into OSE | There is nowhere to type it |
| Unawareness | R, C | Voters do not know the rules | One line on each page: the Access Pass counts the same; the Online Pick can be gamed |
| Non-compliance | G | Special-category data (health) held by OCR | None is held. The request and the reason stay between the voter and the host |

### Score

Not a CCR. This is a first look, to support Matt's decision. A CCR (5 loops, Dr of Security first)
runs on the ADR-040 decision 13 text before any code, as ADR-040 required for decisions 6 and 12.

## 6. Questions for Matt

1. **The Access Pass cap.** Keep it at 4 per vote set, below the smallest margin? Or let it grow with
   the room size (for example, a disability organization's own event)? Recommended: 4, with a platform
   review to raise it for a named event.
2. **Who turns the Access Pass on.** Recommended: on for every event by default, so a voter never has to
   persuade a host to switch it on first. The other choice is off until the host turns it on.
3. **A bot check on the Online Pick.** Recommended: none to start, because it adds a third-party check
   on a public page, and the Online Pick is labelled as gameable anyway. Add one later if crowd floods
   are common.
4. **The names.** Decided by Matt, 2026-11-26: "Room Pick", "Online Pick" and "Access Pass".

## 7. What happens after a yes

1. OSE ADR-040 gains decision 13 with these rules, and decision 12's "remote or link voting is out" is
   amended to say: still out for the Room Pick, except the capped Access Pass.
2. A CCR (5 loops) on that text.
3. Stories in Linear (team OSE): the channel column and the gate test; the crowd pass; the Access Pass
   give, revoke and redeem; the report lines. Each born red, at both layers, checked on staging.
4. Voting stays off everywhere (`VOTING_ENABLED = "off"`) until Matt turns it on.

## Sources

- OSE `docs/adr/ADR-040-anonymous-votable-object.md` (decisions 1, 4, 6, 7, 9, 11, 12), read at OSE `main` 2dc35c9.
- OSE PR #1562 (OSE-2234, flood detection and the vote-code work).
- Matt's messages in the Transcripts project, 2026-11-26 04:56 to 05:01 UTC.
