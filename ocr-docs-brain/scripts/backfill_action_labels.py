#!/usr/bin/env python3
"""
backfill_action_labels.py — OCR-145 one-time `action`-label backfill.

Purpose
=======
`OCR_STANDARD_storyClassification` requires **unlabeled = not-yet-classified**,
never silently "Action". The 2026-09-06 audit classified the whole active board
(verb-signal + DoD read) and labelled the ~46 non-Action stories (spike/field/
hybrid). The complement — every active story the audit left as Action — must
carry the explicit `action` label so the residual "unlabeled" set becomes the
honest *unreviewed* set (and the mislabel tripwire's live gate can be flipped to
blocking via STORY_GATE_ENFORCE=true).

This applies `action` to every ACTIVE story that currently has NO class label.
It is APPEND-ONLY (Linear `issueAddLabel`) — it never removes or replaces labels,
so a story already carrying spike/field/hybrid is skipped untouched.

Honesty / residual
==================
Bulk backfill records the audit's classification; it does not re-classify. The
baseline (docs/discovery/OCR-145_classification-precision-recall-baseline.md)
measured non-Action **recall = 1.00** on a 30-ticket sample, so few if any
disguised spikes are expected in the residual — but "few" is not "zero". A spike
mis-recorded as `action` is NOT caught by the tripwire (which only inspects
spike/field/hybrid), so pair this with a periodic re-classify pass that flags
`action`-labelled stories whose DoD reads like a decision. Stated, not hidden.

Auth: reads LINEAR_API_KEY from the environment. The agent never handles the
secret — the owner runs this. `issueAddLabel` requires a write-scoped key.

Usage
=====
    # SoD: always dry-run first — prints the manifest, mutates nothing.
    python backfill_action_labels.py            # dry-run (default)
    python backfill_action_labels.py --apply    # actually add the labels

The `action` label id is resolved by name at runtime (no hard-coded id).
"""
import json
import os
import sys
import urllib.request

API = "https://api.linear.app/graphql"
ACTIVE_TYPES = {"backlog", "unstarted", "started"}
CLASS_LABELS = {"action", "spike", "field", "hybrid", "vision", "ops"}
ACTION_LABEL = "action"

Q_LABEL = 'query($n:String!){ issueLabels(filter:{name:{eq:$n}}){ nodes{ id name } } }'

Q_ISSUES = """
query($after: String) {
  issues(first: 100, after: $after,
    filter: { state: { type: { in: ["backlog","unstarted","started"] } } }) {
    pageInfo { hasNextPage endCursor }
    nodes { id identifier labels { nodes { name } } }
  }
}
"""

M_ADD = 'mutation($id:String!,$label:String!){ issueAddLabel(id:$id, labelId:$label){ success } }'


def _gql(key, query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", key)
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"Linear API error: {payload['errors']}")
    return payload["data"]


def main(argv):
    apply = "--apply" in argv
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not key:
        print("LINEAR_API_KEY not set (owner runs this; agent never handles the key)", file=sys.stderr)
        return 2

    label_nodes = _gql(key, Q_LABEL, {"n": ACTION_LABEL})["issueLabels"]["nodes"]
    if not label_nodes:
        raise SystemExit(f"'{ACTION_LABEL}' label not found — create it first")
    action_id = label_nodes[0]["id"]

    targets, after = [], None
    while True:
        page = _gql(key, Q_ISSUES, {"after": after})["issues"]
        for n in page["nodes"]:
            names = {l["name"].lower() for l in n["labels"]["nodes"]}
            if not (names & CLASS_LABELS):
                targets.append((n["id"], n["identifier"]))
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]

    print(f"{len(targets)} active stories have no class label → would receive `action`.")
    for _, ident in targets[:20]:
        print(f"  {ident}")
    if len(targets) > 20:
        print(f"  … and {len(targets) - 20} more")

    if not apply:
        print("\nDRY-RUN (default) — nothing changed. Re-run with --apply to add the labels.")
        return 0

    done = 0
    for iid, ident in targets:
        res = _gql(key, M_ADD, {"id": iid, "label": action_id})
        if res["issueAddLabel"]["success"]:
            done += 1
        else:
            print(f"  WARN: {ident} add-label returned success=false", file=sys.stderr)
    print(f"\nApplied `action` to {done}/{len(targets)} stories. Unlabeled now = genuinely unreviewed.")
    print("Next: verify the live gate count is ~0, then set repo var STORY_GATE_ENFORCE=true.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
