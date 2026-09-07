#!/usr/bin/env python3
"""
fetch_active_stories.py — export active Linear stories into the JSON shape that
check_story_classification.py consumes.

Live half of the OCR-145 mislabel tripwire. Kept separate from the checker so the
checker stays pure/offline-testable (born-red self-test needs no token) and only
this thin fetch layer touches the network.

Auth: reads LINEAR_API_KEY from the environment (a Linear personal/API key).
The agent never handles this secret — the owner wires it as a CI secret; this
script only *reads* the env var at runtime. No key is stored here.

Emits, to stdout, a JSON array of::

    {"id","priority","statusType","labels":[...],"has_linked_action":bool}

`has_linked_action` is true when any blocking/related issue carries the `action`
label (a spike/field that feeds real work is not a mis-lane). Conservative: if
relations can't be resolved, it defaults false (the tripwire prefers to flag).
"""
import json
import os
import sys
import urllib.request

API = "https://api.linear.app/graphql"
ACTIVE_TYPES = {"backlog", "unstarted", "started"}

QUERY = """
query ActiveStories($after: String) {
  issues(
    first: 100
    after: $after
    filter: { state: { type: { in: ["backlog", "unstarted", "started"] } } }
  ) {
    pageInfo { hasNextPage endCursor }
    nodes {
      identifier
      priority
      state { type }
      labels { nodes { name } }
      relations { nodes { relatedIssue { labels { nodes { name } } } } }
      inverseRelations { nodes { issue { labels { nodes { name } } } } }
    }
  }
}
"""


def _post(api_key, after):
    body = json.dumps({"query": QUERY, "variables": {"after": after}}).encode()
    req = urllib.request.Request(API, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", api_key)
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"Linear API error: {payload['errors']}")
    return payload["data"]["issues"]


def _related_labels(node):
    names = set()
    for rel in node.get("relations", {}).get("nodes", []):
        ri = rel.get("relatedIssue") or {}
        for l in ri.get("labels", {}).get("nodes", []):
            names.add(l["name"].lower())
    for rel in node.get("inverseRelations", {}).get("nodes", []):
        ri = rel.get("issue") or {}
        for l in ri.get("labels", {}).get("nodes", []):
            names.add(l["name"].lower())
    return names


def main():
    api_key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not api_key:
        print("LINEAR_API_KEY not set", file=sys.stderr)
        return 2

    stories, after = [], None
    while True:
        page = _post(api_key, after)
        for n in page["nodes"]:
            stype = (n.get("state") or {}).get("type", "")
            if stype not in ACTIVE_TYPES:
                continue
            labels = [l["name"] for l in n.get("labels", {}).get("nodes", [])]
            stories.append({
                "id": n["identifier"],
                "priority": n.get("priority", 0),
                "statusType": stype,
                "labels": labels,
                "has_linked_action": "action" in _related_labels(n),
            })
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]

    json.dump(stories, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
