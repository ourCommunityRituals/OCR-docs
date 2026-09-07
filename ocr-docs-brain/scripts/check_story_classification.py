#!/usr/bin/env python3
"""
check_story_classification.py — OCR-145 mislabel tripwire (the pawl).

Why this exists
===============
The Action/Spike/Field classification (`OCR_STANDARD_storyClassification`) is
only true while something keeps it true. A one-time board sweep decays the
moment the next ticket is filed ("green is rented"). This gate is the pawl: it
fails closed on the drift shapes the 2026-09-06 audit had to clean by hand, so
they cannot silently return.

It operates on a JSON snapshot of active stories (Linear export in live mode, or
a fixture in the born-red self-test), so the logic is provable offline with no
API token — exactly the OCR-130 secret-scan pattern (checker + fixtures + a
self-test that plants a violation and asserts the gate bites).

Story JSON shape (one object per active story)::

    {"id": "OSE-1", "priority": 1, "statusType": "started",
     "labels": ["spike"], "has_linked_action": false}

  priority   : 0=None 1=Urgent 2=High 3=Medium 4=Low   (Linear convention)
  statusType : backlog | unstarted | started | completed | canceled
  labels     : the story's label names
  has_linked_action : true if a blocking/related ticket is itself an Action
                      (a spike/field that FEEDS real work is fine)

Only active stories are checked (statusType in {backlog, unstarted, started});
completed/canceled are ignored.

Violations (fail closed on any)
-------------------------------
  V1 UNCLASSIFIED       — active story carries no class label. UNLABELED must
                          mean "not yet classified", never silently "Action".
  V2 SPIKE_NOW_PRIORITY — a `spike` at Urgent/High with no linked Action. A
                          spike is *future* work; carrying now-priority with
                          nothing it feeds is the "deferred investigation drawing
                          now-urgency" smell.
  V3 INFLIGHT_NO_ACTION — a `spike` or `field` In-Progress (started) with no
                          linked Action — investigation/field work occupying an
                          active engineering slot on its own.
  V4 UNSPLIT_HYBRID     — a `hybrid` that has entered a sprint (started). A
                          hybrid must be SPLIT before it is worked; the label is
                          a work-marker, not a resting class.

Design note on V2/field: `field` is deliberately NOT flagged on priority alone.
Field work runs on its own real-world/GTM calendar and is legitimately urgent
(a launch-blocking sponsor ask). It is only flagged once it is *in flight* with
no linked Action (V3). This is a considered refinement of OCR-145's DoD wording
("spike/field moved to Urgent/High or In-Progress") — spike keeps the priority
rule; field keeps only the in-flight rule. Tune the constants below to change it.

Exit non-zero if any violation is found.
"""
import json
import sys

CLASS_LABELS = {"action", "spike", "field", "hybrid", "vision", "ops"}
ACTIVE = {"backlog", "unstarted", "started"}
NOW_PRIORITIES = {1, 2}          # Urgent, High
IN_FLIGHT = {"started"}          # In-Progress / In-Review


def violations_for(story):
    """Return a list of (code, reason) violations for one story. Empty = clean."""
    status = story.get("statusType", "")
    if status not in ACTIVE:
        return []

    labels = {str(l).lower() for l in story.get("labels", [])}
    classes = labels & CLASS_LABELS
    priority = story.get("priority", 0)
    started = status in IN_FLIGHT
    has_action = bool(story.get("has_linked_action", False))

    out = []
    if not classes:
        out.append(("V1_UNCLASSIFIED",
                    "active story carries no class label (unlabeled != Action)"))
    if "spike" in labels and priority in NOW_PRIORITIES and not has_action:
        out.append(("V2_SPIKE_NOW_PRIORITY",
                    "spike at Urgent/High with no linked Action (future work drawing now-urgency)"))
    if (labels & {"spike", "field"}) and started and not has_action:
        out.append(("V3_INFLIGHT_NO_ACTION",
                    "spike/field In-Progress with no linked Action (investigation/field in an active slot)"))
    if "hybrid" in labels and started:
        out.append(("V4_UNSPLIT_HYBRID",
                    "hybrid entered a sprint unsplit (split decide->ship before working)"))
    return out


def main(argv):
    if len(argv) != 2:
        print("usage: check_story_classification.py <stories.json>", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as fh:
        stories = json.load(fh)

    findings = []
    for s in stories:
        for code, reason in violations_for(s):
            findings.append((s.get("id", "?"), code, reason))

    active = sum(1 for s in stories if s.get("statusType") in ACTIVE)
    if findings:
        print(f"FAIL: {len(findings)} classification violation(s) across {active} active stories:\n")
        for sid, code, reason in findings:
            print(f"  {sid}  {code}  — {reason}")
        print("\nSee OCR_STANDARD_storyClassification §3. Fix the class label, split the "
              "hybrid, link the Action, or re-lane — then re-run.")
        return 1

    print(f"OK: {active} active stories, every one carries a class label and no mis-lane. Gate clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
