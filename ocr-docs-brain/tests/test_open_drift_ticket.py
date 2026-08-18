#!/usr/bin/env python3
"""
test_open_drift_ticket.py — Logic lock for open_drift_ticket.py.

Why this exists
===============
On 2026-08-17 (OCR-83 "brain-drift tickets have no triage destination")
open_drift_ticket.py was hardened so drift tickets are actionable instead
of piling up unowned in Backlog. Three defects were fixed and each is
locked here so they cannot silently return:

1. **Dedup was dead.** `search_existing_issue` declared `$teamId: String!`,
   but Linear's `team.id` filter expects `ID`. The query 400'd every run,
   the error was swallowed by a bare `except`, the function always returned
   None, and every CI re-run created a *duplicate* ticket (that's how
   OCR-78..82 accumulated). Locked: the query text must declare `ID!`, and
   a found issue must route to issueUpdate (not a second issueCreate).

2. **No owner.** Tickets filed unassigned. `resolve_assignee` now maps the
   PR author's GitHub login to a Linear user, falling back to the token
   owner. Locked: match semantics + fallback.

3. **No priority.** Filed at None → indistinguishable from unfiled. Locked:
   issueCreate payload carries priority == DRIFT_PRIORITY.

Design note: the GraphQL transport (`graphql`) is monkeypatched with a
fake dispatcher, so these tests are hermetic — no network, no Linear key,
no LLM. That matches the L0 architectural floor (runtime stays offline)
and lets the create/update payloads be asserted directly.

`test_helper_cli_contracts.py` already locks the *CLI surface* (args +
skip-path exit codes); this file locks the *behavior* underneath it.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import sys
import json
import os
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BRAIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BRAIN_ROOT / 'scripts'))

import open_drift_ticket as odt  # noqa: E402

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


class FakeLinear:
    """A stand-in for the Linear GraphQL endpoint.

    Dispatches on substrings of the query text and records every call so a
    test can assert what mutations were issued and with what variables.
    Install with `odt.graphql = fake.graphql`.
    """
    def __init__(self, users=None, existing_issue=None):
        # users: list of {id,name,displayName,email} for resolve_assignee
        self.users = users if users is not None else []
        # existing_issue: id string to return from the dedup search, or None
        self.existing_issue = existing_issue
        self.calls = []            # list of (query, variables)
        self.created = None        # variables of the issueCreate call
        self.updated = None        # variables of the issueUpdate call

    def graphql(self, query, variables, api_key):
        self.calls.append((query, dict(variables)))
        if 'viewer' in query:
            return {'data': {'viewer': {'id': 'VIEWER_ID'}}}
        if 'users(' in query:
            return {'data': {'users': {'nodes': self.users}}}
        if 'teams(' in query:
            return {'data': {'teams': {'nodes': [
                {'id': 'TEAM_ID', 'key': variables.get('key'), 'name': 'T'}]}}}
        if 'issues(' in query:
            nodes = ([{'id': self.existing_issue, 'identifier': 'X-1',
                       'title': 't'}] if self.existing_issue else [])
            return {'data': {'issues': {'nodes': nodes}}}
        if 'issueUpdate' in query:
            self.updated = dict(variables)
            return {'data': {'issueUpdate': {'issue': {
                'id': 'X', 'identifier': 'X-1', 'url': 'http://x/1'}}}}
        if 'issueCreate' in query:
            self.created = dict(variables)
            return {'data': {'issueCreate': {'issue': {
                'id': 'Y', 'identifier': 'Y-2', 'url': 'http://y/2'}}}}
        raise AssertionError(f'unexpected query: {query[:60]}')


def _run_main(fake, *, product_id='ose', pr_author='someone',
              failures=None, existing=None):
    """Invoke odt.main() end-to-end with the transport faked. Returns the
    FakeLinear so callers can assert on .created / .updated / .calls."""
    if failures is None:
        failures = [{'check': 'regulatory_pools_present', 'detail': 'x'}]
    report = {'product_id': product_id, 'failures': failures,
              'passes': [], 'summary': {'failed': len(failures)}}
    with tempfile.TemporaryDirectory() as td:
        rp = Path(td) / 'report.json'
        rp.write_text(json.dumps(report), encoding='utf-8')
        argv = ['open_drift_ticket.py', '--report', str(rp), '--repo', 'r',
                '--pr-number', '7', '--pr-url', 'http://pr/7',
                '--pr-author', pr_author, '--commit', 'deadbeef1234']
        old_argv, old_key = sys.argv, os.environ.get('LINEAR_API_KEY')
        old_graphql = odt.graphql
        sys.argv = argv
        os.environ['LINEAR_API_KEY'] = 'fake-key'
        odt.graphql = fake.graphql
        try:
            odt.main()
        finally:
            sys.argv = old_argv
            odt.graphql = old_graphql
            if old_key is None:
                os.environ.pop('LINEAR_API_KEY', None)
            else:
                os.environ['LINEAR_API_KEY'] = old_key
    return fake


# ─── 1. Dedup / GraphQL type-correctness (the OCR-86 regression) ─────────────

def test_search_query_declares_teamid_as_ID():
    """Hard lock on the exact bug: the dedup query MUST declare `$teamId: ID!`.
    `String!` reintroduces the HTTP 400 that silently disabled dedup."""
    import inspect
    src = inspect.getsource(odt.search_existing_issue)
    assert '$teamId: ID!' in src, 'dedup query must declare $teamId as ID!'
    assert '$teamId: String!' not in src, 'the String! form is the OCR-86 bug'
    return '$teamId declared ID! in search_existing_issue'


def test_search_returns_existing_id_and_none():
    old = odt.graphql
    try:
        odt.graphql = FakeLinear(existing_issue='EXIST_ID').graphql
        got = odt.search_existing_issue('TEAM_ID', 'drift:ose:pr-7:deadbeef', 'k')
        assert got == 'EXIST_ID', got
        odt.graphql = FakeLinear(existing_issue=None).graphql
        got2 = odt.search_existing_issue('TEAM_ID', 'tag', 'k')
        assert got2 is None, got2
    finally:
        odt.graphql = old
    return 'search returns id when present, None when absent'


def test_search_swallows_error_but_does_not_raise():
    """A dedup-search failure must degrade to None (still file), never crash."""
    def boom(*a, **k):
        raise RuntimeError('linear down')
    old = odt.graphql
    odt.graphql = boom
    try:
        got = odt.search_existing_issue('T', 'tag', 'k')
    finally:
        odt.graphql = old
    assert got is None, got
    return 'search failure → None (files anyway, no crash)'


# ─── 2. resolve_assignee ─────────────────────────────────────────────────────

def test_resolve_assignee_matches_display_name():
    fake = FakeLinear(users=[{'id': 'U1', 'displayName': 'BeReasonable13',
                              'name': 'Matt', 'email': 'm@x.com'}])
    old = odt.graphql
    odt.graphql = fake.graphql
    try:
        got = odt.resolve_assignee('bereasonable13', 'k', 'FALLBACK')
    finally:
        odt.graphql = old
    assert got == 'U1', got
    return 'matches displayName case-insensitively'


def test_resolve_assignee_matches_email_localpart():
    fake = FakeLinear(users=[{'id': 'U2', 'displayName': 'x', 'name': 'y',
                              'email': 'octocat@example.com'}])
    old = odt.graphql
    odt.graphql = fake.graphql
    try:
        got = odt.resolve_assignee('octocat', 'k', 'FALLBACK')
    finally:
        odt.graphql = old
    assert got == 'U2', got
    return 'matches email local part'


def test_resolve_assignee_falls_back_when_no_match():
    fake = FakeLinear(users=[{'id': 'U3', 'displayName': 'someone-else',
                              'name': 'n', 'email': 'e@x.com'}])
    old = odt.graphql
    odt.graphql = fake.graphql
    try:
        got = odt.resolve_assignee('ghost', 'k', 'FALLBACK')
    finally:
        odt.graphql = old
    assert got == 'FALLBACK', got
    return 'no user match → fallback (token owner)'


def test_resolve_assignee_empty_author_falls_back():
    got = odt.resolve_assignee('', 'k', 'FALLBACK')
    assert got == 'FALLBACK', got
    return 'empty author → fallback without querying'


# ─── 3. main(): priority + owner on create, dedup routes to update ───────────

def test_create_payload_has_priority_and_assignee():
    """The core OCR-83 fix: a NEW ticket is created with a priority and an
    owner (not Backlog/None/unassigned)."""
    fake = FakeLinear(
        users=[{'id': 'AUTHOR_ID', 'displayName': 'dev', 'name': 'Dev',
                'email': 'dev@x.com'}],
        existing_issue=None)
    _run_main(fake, pr_author='dev')
    assert fake.created is not None, 'expected an issueCreate'
    assert fake.updated is None, 'must not update when no existing ticket'
    assert fake.created.get('priority') == odt.DRIFT_PRIORITY, fake.created
    assert fake.created.get('assigneeId') == 'AUTHOR_ID', fake.created
    return f'create carries priority={odt.DRIFT_PRIORITY}, assignee=PR author'


def test_create_assignee_falls_back_to_viewer():
    """When the PR author maps to no Linear user, the ticket is still owned —
    by the token owner (viewer) — never left unassigned."""
    fake = FakeLinear(users=[], existing_issue=None)
    _run_main(fake, pr_author='nobody-here')
    assert fake.created is not None
    assert fake.created.get('assigneeId') == 'VIEWER_ID', fake.created
    return 'unmapped author → assigned to viewer (never unassigned)'


def test_existing_ticket_updates_and_preserves_triage():
    """Dedup working: when a ticket already exists for this (product,PR,commit),
    update it — and do NOT re-stamp priority/assignee (preserve human triage)."""
    fake = FakeLinear(users=[], existing_issue='EXISTING')
    _run_main(fake)
    assert fake.updated is not None, 'expected issueUpdate on dedup hit'
    assert fake.created is None, 'must not create a duplicate'
    assert 'priority' not in fake.updated, 'update must not clobber priority'
    assert 'assigneeId' not in fake.updated, 'update must not clobber assignee'
    return 'existing ticket → update, triage preserved'


# ─── 4. Team routing ─────────────────────────────────────────────────────────

def test_routing_product_team_vs_brain_level():
    """A product-level failure routes to the product's team; a brain-level
    failure (e.g. faith_commitment) routes to OCR-doc regardless of product."""
    # product failure → OSE team queried
    fake = FakeLinear(existing_issue=None)
    _run_main(fake, product_id='ose',
              failures=[{'check': 'required_tags_used', 'detail': 'x'}])
    team_keys = [v.get('key') for q, v in fake.calls if 'teams(' in q]
    assert team_keys == ['OSE'], team_keys

    # brain-level failure → OCR-doc team queried even for an OSE product
    fake2 = FakeLinear(existing_issue=None)
    _run_main(fake2, product_id='ose',
              failures=[{'check': 'faith_commitment', 'detail': 'x'}])
    team_keys2 = [v.get('key') for q, v in fake2.calls if 'teams(' in q]
    assert team_keys2 == ['OCR-doc'], team_keys2
    return 'product failure → product team; brain failure → OCR-doc'


CONTRACTS = [
    ('dedup.query_declares_ID', test_search_query_declares_teamid_as_ID),
    ('dedup.search_returns_id_or_none', test_search_returns_existing_id_and_none),
    ('dedup.search_error_degrades_to_none', test_search_swallows_error_but_does_not_raise),
    ('assignee.match_display_name', test_resolve_assignee_matches_display_name),
    ('assignee.match_email_localpart', test_resolve_assignee_matches_email_localpart),
    ('assignee.fallback_on_no_match', test_resolve_assignee_falls_back_when_no_match),
    ('assignee.empty_author_fallback', test_resolve_assignee_empty_author_falls_back),
    ('create.has_priority_and_assignee', test_create_payload_has_priority_and_assignee),
    ('create.assignee_fallback_to_viewer', test_create_assignee_falls_back_to_viewer),
    ('dedup.existing_updates_preserving_triage', test_existing_ticket_updates_and_preserves_triage),
    ('routing.product_vs_brain_level', test_routing_product_team_vs_brain_level),
]

for name, fn in CONTRACTS:
    check(name, fn)

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  OPEN_DRIFT_TICKET — DEDUP / OWNER / PRIORITY / ROUTING')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:44} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: OCR-83 (drift tickets had no triage destination) +')
print('OCR-86 ($teamId String!/ID! dedup bug), hardened 2026-08-17.')

sys.exit(0 if failed == 0 else 1)
