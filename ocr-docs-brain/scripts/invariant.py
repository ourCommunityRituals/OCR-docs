#!/usr/bin/env python3
"""
invariant.py — Lightweight invariant management CLI for the OCR-docs brain.

Wraps create / update / delete / list / validate / flip operations on
architectural-invariants.yaml so every mutation is structurally correct:
  - IDs are auto-assigned (max+1)
  - group_order is auto-assigned (max-within-group+1)
  - History entries are written automatically
  - status_summary counts are rebuilt from source, not hand-edited
  - YAML comments are preserved via ruamel.yaml round-trip

Usage:
  python3 scripts/invariant.py list [--group GROUP] [--status STATUS]
  python3 scripts/invariant.py create --name NAME --group GROUP --title TITLE --enforces TEXT --applies-to ose,wkrp [options]
  python3 scripts/invariant.py update ID_OR_NAME [--status STATUS] [--title TITLE] [--pr-ref REF] [options]
  python3 scripts/invariant.py flip ID_OR_NAME --to live|partial --pr-ref REF [--rationale TEXT]
  python3 scripts/invariant.py delete ID_OR_NAME --rationale TEXT [--pr-ref REF]
  python3 scripts/invariant.py validate [--fix]
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentToken
    from ruamel.yaml.error import CommentMark
    import ruamel.yaml.scalarstring as ss
except ImportError:
    print("ERROR: ruamel.yaml is required.")
    print("  pip install ruamel.yaml")
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
BRAIN_DIR = SCRIPT_DIR.parent
INVARIANTS_FILE = BRAIN_DIR / "architectural-invariants.yaml"

# ── Constants ──────────────────────────────────────────────────────────────────

VALID_STATUSES = {"live", "partial", "planned", "canceled"}
STATUS_ICON = {"live": "✅", "partial": "⚙️ ", "planned": "📋", "canceled": "❌"}

# Required fields per status (planned invariants defer test_file)
REQUIRED_ALWAYS = ["id", "name", "label", "group", "group_order", "title",
                   "status", "enforces", "applies_to"]
REQUIRED_NON_PLANNED = REQUIRED_ALWAYS + ["test_file"]

# ── YAML I/O ───────────────────────────────────────────────────────────────────

def _make_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 120
    y.best_sequence_indent = 2
    y.best_map_flow_style = False
    return y


def load_brain() -> CommentedMap:
    if not INVARIANTS_FILE.exists():
        print(f"ERROR: invariants file not found: {INVARIANTS_FILE}")
        sys.exit(1)
    y = _make_yaml()
    with open(INVARIANTS_FILE, encoding="utf-8") as fh:
        return y.load(fh)


def save_brain(data: CommentedMap) -> None:
    """Atomic write: dump to temp file then rename so a crash can't corrupt."""
    y = _make_yaml()
    tmp = INVARIANTS_FILE.with_suffix(".yaml.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        y.dump(data, fh)
    tmp.replace(INVARIANTS_FILE)

# ── Helpers ────────────────────────────────────────────────────────────────────

def today() -> str:
    return datetime.date.today().isoformat()


def find_invariant(data: CommentedMap, id_or_name: str) -> CommentedMap | None:
    for inv in data.get("invariants", []):
        if str(inv.get("id")) == str(id_or_name):
            return inv
        if inv.get("name") == id_or_name:
            return inv
    return None


def next_global_id(data: CommentedMap) -> int:
    ids = [i["id"] for i in data.get("invariants", [])
           if isinstance(i.get("id"), int)]
    return max(ids) + 1 if ids else 1


def next_group_order(data: CommentedMap, group: str) -> int:
    orders = [
        i.get("group_order", 0)
        for i in data.get("invariants", [])
        if i.get("group") == group and isinstance(i.get("group_order"), int)
        and i.get("status") != "canceled"
    ]
    return max(orders) + 1 if orders else 1


def valid_group_ids(data: CommentedMap) -> list[str]:
    return [g["id"] for g in data.get("invariant_groups", [])
            if isinstance(g, dict) and "id" in g]


def make_label(iid: int, title: str) -> str:
    return f"#{iid} — {title}"


def _set_eol_comment(mapping: CommentedMap, key: str, comment: str) -> None:
    """Set (or replace) the end-of-line comment on a key in a CommentedMap."""
    col = 4  # indent of status_summary keys
    tok = CommentToken(f"# {comment}\n", CommentMark(col), None)
    # ruamel stores: [before_key, before_value, eol_comment, after_value]
    existing = mapping.ca.items.get(key, [None, None, None, None])
    existing[2] = tok
    mapping.ca.items[key] = existing


def rebuild_status_summary(data: CommentedMap) -> None:
    """
    Recompute status_summary from the invariants list and write it back,
    regenerating the inline ID-list comments for live + partial.
    """
    by_status: dict[str, list[CommentedMap]] = {
        "live": [], "partial": [], "planned": [], "canceled": []
    }
    rich: list[int] = []
    lean: list[int] = []

    for inv in data.get("invariants", []):
        status = inv.get("status", "planned")
        if status in by_status:
            by_status[status].append(inv)
        if status != "canceled":
            if inv.get("enforcement_statement"):
                rich.append(inv["id"])
            else:
                lean.append(inv["id"])

    summary: CommentedMap = data.get("status_summary", CommentedMap())

    summary["live"] = len(by_status["live"])
    summary["partial"] = len(by_status["partial"])
    summary["planned"] = len(by_status["planned"])
    summary["total"] = (len(by_status["live"]) + len(by_status["partial"])
                        + len(by_status["planned"]))
    summary["rich_form"] = len(rich)
    summary["lean_form"] = len(lean)

    # Regenerate inline ID-list comments
    def _ids(invs: list[CommentedMap]) -> str:
        parts = [f"#{i['id']} {i['name']}" for i in
                 sorted(invs, key=lambda x: x.get("id", 0))]
        return ", ".join(parts) if parts else "none"

    if by_status["live"]:
        _set_eol_comment(summary, "live", _ids(by_status["live"]))
    if by_status["partial"]:
        _set_eol_comment(summary, "partial", _ids(by_status["partial"]))

    data["status_summary"] = summary

# ── Commands ───────────────────────────────────────────────────────────────────

def cmd_create(args: argparse.Namespace, data: CommentedMap) -> None:
    groups = valid_group_ids(data)
    if args.group not in groups:
        _die(f"group '{args.group}' is not valid.\nKnown groups: {groups}")

    applies = [a.strip() for a in args.applies_to.split(",") if a.strip()]
    status = args.status or "planned"
    if status not in VALID_STATUSES:
        _die(f"status must be one of {sorted(VALID_STATUSES)}")

    new_id = next_global_id(data)
    group_ord = next_group_order(data, args.group)

    inv = CommentedMap({
        "id": new_id,
        "name": args.name,
        "label": make_label(new_id, args.title),
        "group": args.group,
        "group_order": group_ord,
        "title": args.title,
        "status": status,
        "test_file": args.test_file,
        "enforces": ss.FoldedScalarString(args.enforces.strip() + "\n"),
        "applies_to": applies,
    })

    if args.protective_statement:
        inv["protective_statement"] = ss.FoldedScalarString(
            args.protective_statement.strip() + "\n")
    if args.enforcement_statement:
        inv["enforcement_statement"] = ss.FoldedScalarString(
            args.enforcement_statement.strip() + "\n")

    data["invariants"].append(inv)

    _append_history(data, CommentedMap({
        "invariant_id": new_id,
        "invariant_name": args.name,
        "from_state": "does not exist",
        "to_state": ss.FoldedScalarString(
            f"{status} ({today()} — new invariant born {status})\n"),
        "date": today(),
        "pr_refs": ([args.pr_ref] if args.pr_ref else []),
        "rationale": ss.FoldedScalarString(
            (args.rationale or f"New invariant created via invariant.py CLI ({today()})") + "\n"),
    }))

    rebuild_status_summary(data)
    save_brain(data)

    _ok(f"Created Invariant #{new_id} — {args.title}")
    _info(f"group: {args.group}  group_order: {group_ord}  status: {status}")
    _print_summary(data)


def cmd_update(args: argparse.Namespace, data: CommentedMap) -> None:
    inv = _require_invariant(data, args.id_or_name)
    old_status = inv.get("status", "?")
    changes: list[str] = []

    if args.status:
        if args.status not in VALID_STATUSES:
            _die(f"status must be one of {sorted(VALID_STATUSES)}")
        if args.status != old_status:
            inv["status"] = args.status
            changes.append(f"status {old_status} → {args.status}")

    if args.title:
        inv["title"] = args.title
        inv["label"] = make_label(inv["id"], args.title)
        changes.append("title updated")

    if args.enforces:
        inv["enforces"] = ss.FoldedScalarString(args.enforces.strip() + "\n")
        changes.append("enforces updated")

    if args.test_file:
        inv["test_file"] = args.test_file
        changes.append(f"test_file → {args.test_file}")

    if args.protective_statement:
        inv["protective_statement"] = ss.FoldedScalarString(
            args.protective_statement.strip() + "\n")
        changes.append("protective_statement updated")

    if args.enforcement_statement:
        inv["enforcement_statement"] = ss.FoldedScalarString(
            args.enforcement_statement.strip() + "\n")
        changes.append("enforcement_statement updated")

    if not changes:
        _warn("No changes specified — nothing to do.")
        return

    _append_history(data, CommentedMap({
        "invariant_id": inv["id"],
        "invariant_name": inv["name"],
        "from_state": old_status,
        "to_state": ss.FoldedScalarString(
            f"{inv.get('status')} ({today()} — {'; '.join(changes)})\n"),
        "date": today(),
        "pr_refs": ([args.pr_ref] if args.pr_ref else []),
        "rationale": ss.FoldedScalarString(
            (args.rationale or f"Updated via CLI: {'; '.join(changes)}") + "\n"),
    }))

    rebuild_status_summary(data)
    save_brain(data)

    _ok(f"Updated Invariant #{inv['id']} — {inv['title']}")
    for c in changes:
        _info(f"  {c}")
    _print_summary(data)


def cmd_flip(args: argparse.Namespace, data: CommentedMap) -> None:
    """Shortcut for the common partial → live or planned → partial transitions."""
    inv = _require_invariant(data, args.id_or_name)
    old_status = inv.get("status")
    new_status = args.to

    if new_status not in VALID_STATUSES:
        _die(f"--to must be one of {sorted(VALID_STATUSES)}")
    if old_status == new_status:
        _warn(f"Invariant #{inv['id']} is already {new_status}. Nothing to do.")
        return
    if not args.pr_ref:
        _die("--pr-ref is required for flip (records the activation PR)")

    inv["status"] = new_status
    _append_history(data, CommentedMap({
        "invariant_id": inv["id"],
        "invariant_name": inv["name"],
        "from_state": old_status,
        "to_state": ss.FoldedScalarString(
            f"{new_status} ({today()} — flipped via CLI)\n"),
        "date": today(),
        "pr_refs": [args.pr_ref],
        "rationale": ss.FoldedScalarString(
            (args.rationale or f"Status flip {old_status} → {new_status} via CLI ({today()})") + "\n"),
    }))

    rebuild_status_summary(data)
    save_brain(data)

    _ok(f"Flipped Invariant #{inv['id']} — {inv['title']}: {old_status} → {new_status}")
    _print_summary(data)


def cmd_delete(args: argparse.Namespace, data: CommentedMap) -> None:
    """Mark as canceled — never hard-delete (preserves audit trail)."""
    inv = _require_invariant(data, args.id_or_name)
    old_status = inv.get("status")

    if old_status == "canceled":
        _warn(f"Invariant #{inv['id']} is already canceled.")
        return
    if not args.rationale:
        _die("--rationale is required for delete (explain why in the audit trail)")

    inv["status"] = "canceled"
    _append_history(data, CommentedMap({
        "invariant_id": inv["id"],
        "invariant_name": inv["name"],
        "from_state": old_status,
        "to_state": ss.FoldedScalarString(
            f"canceled ({today()} — {args.rationale})\n"),
        "date": today(),
        "pr_refs": ([args.pr_ref] if args.pr_ref else []),
        "rationale": ss.FoldedScalarString(args.rationale + "\n"),
    }))

    rebuild_status_summary(data)
    save_brain(data)

    _ok(f"Canceled Invariant #{inv['id']} — {inv['title']}")
    _info("Audit trail preserved — not hard-deleted.")
    _print_summary(data)


def cmd_list(args: argparse.Namespace, data: CommentedMap) -> None:
    invs = list(data.get("invariants", []))

    if args.group:
        invs = [i for i in invs if i.get("group") == args.group]
    if args.status:
        invs = [i for i in invs if i.get("status") == args.status]

    # Sort: group canonical order, then group_order, then id
    group_order_map = {
        g["id"]: g.get("order", 99)
        for g in data.get("invariant_groups", [])
        if isinstance(g, dict) and "id" in g
    }
    invs.sort(key=lambda i: (
        group_order_map.get(i.get("group", ""), 99),
        i.get("group_order", 99),
        i.get("id", 99),
    ))

    if not invs:
        _info("No invariants match the filter.")
        return

    # Column widths
    W_ID, W_GRP, W_ORD, W_TITLE = 4, 28, 3, 42

    header = (f"{'ID':>{W_ID}}  {'St':2}  {'Group':<{W_GRP}}  "
              f"{'Ord':>{W_ORD}}  {'Title':<{W_TITLE}}")
    print(header)
    print("─" * len(header))

    last_group = None
    for inv in invs:
        iid    = inv.get("id", "?")
        status = inv.get("status", "?")
        icon   = STATUS_ICON.get(status, "? ")
        group  = inv.get("group", "?")
        order  = inv.get("group_order", "?")
        title  = (inv.get("title") or inv.get("name") or "")[:W_TITLE]

        if group != last_group:
            if last_group is not None:
                print()
            last_group = group

        print(f"{iid:>{W_ID}}  {icon}  {group:<{W_GRP}}  {order:>{W_ORD}}  {title}")

    print()
    _print_summary(data)


def cmd_validate(args: argparse.Namespace, data: CommentedMap) -> None:
    """Full structural validation — mirrors level2_schema.py checks 1.5c–1.5g."""
    errors: list[str] = []
    warnings: list[str] = []
    groups = valid_group_ids(data)

    ids_seen: set[int] = set()
    group_orders_seen: dict[str, set[int]] = {}

    for inv in data.get("invariants", []):
        iid   = inv.get("id")
        name  = inv.get("name", "?")
        label = f"#{iid} {name}"
        status = inv.get("status", "?")

        # ── Required fields ──
        required = (REQUIRED_NON_PLANNED
                    if status not in ("planned", "canceled")
                    else REQUIRED_ALWAYS)
        missing = [f for f in required if f not in inv]
        if missing:
            errors.append(f"{label}: missing required fields: {missing}")

        # ── Duplicate IDs ──
        if iid in ids_seen:
            errors.append(f"Duplicate invariant id: {iid}")
        if isinstance(iid, int):
            ids_seen.add(iid)

        # ── Group valid ──
        group = inv.get("group")
        if group not in groups:
            errors.append(f"{label}: group '{group}' not in known groups {groups}")

        # ── group_order unique within group ──
        go = inv.get("group_order")
        if group not in group_orders_seen:
            group_orders_seen[group] = set()
        if isinstance(go, int):
            if go in group_orders_seen[group]:
                errors.append(f"{label}: group_order {go} collision in group '{group}'")
            group_orders_seen[group].add(go)

        # ── Status valid ──
        if status not in VALID_STATUSES:
            errors.append(f"{label}: invalid status '{status}'")

        # ── label matches id ──
        label_field = inv.get("label", "")
        if label_field and not str(label_field).startswith(f"#{iid}"):
            warnings.append(f"{label}: label '{label_field}' doesn't start with '#{iid}'")

        # ── applies_to is a list ──
        at = inv.get("applies_to")
        if not isinstance(at, list) or len(at) == 0:
            warnings.append(f"{label}: applies_to should be a non-empty list")

    # ── status_summary accuracy ──
    declared = data.get("status_summary", {})
    # Build expected counts without mutating data
    by_status: dict[str, int] = {"live": 0, "partial": 0, "planned": 0}
    for inv in data.get("invariants", []):
        s = inv.get("status")
        if s in by_status:
            by_status[s] += 1
    expected_total = sum(by_status.values())
    for key in ["live", "partial", "planned"]:
        if declared.get(key) != by_status[key]:
            errors.append(
                f"status_summary.{key}: declared={declared.get(key)}, "
                f"computed={by_status[key]}"
            )
    if declared.get("total") != expected_total:
        errors.append(
            f"status_summary.total: declared={declared.get('total')}, "
            f"computed={expected_total}"
        )

    # ── History entries have required fields ──
    for entry in data.get("history", []):
        for field in ["invariant_id", "invariant_name", "from_state", "to_state", "date", "rationale"]:
            if field not in entry:
                warnings.append(
                    f"history entry for #{entry.get('invariant_id','?')}: missing '{field}'")

    # ── Report ──
    total_invs = len([i for i in data.get("invariants", [])
                      if i.get("status") != "canceled"])
    if errors:
        print(f"FAIL — {len(errors)} error(s), {len(warnings)} warning(s)  "
              f"({total_invs} active invariants)\n")
        for e in errors:
            print(f"  ✗ {e}")
        if warnings:
            print()
            for w in warnings:
                print(f"  ⚠ {w}")
        sys.exit(1)
    else:
        print(f"PASS — {total_invs} active invariants valid.")
        if warnings:
            print(f"  {len(warnings)} warning(s):")
            for w in warnings:
                print(f"    ⚠ {w}")

# ── Internal utilities ─────────────────────────────────────────────────────────

def _append_history(data: CommentedMap, entry: CommentedMap) -> None:
    if "history" not in data:
        data["history"] = []
    data["history"].append(entry)


def _require_invariant(data: CommentedMap, id_or_name: str) -> CommentedMap:
    inv = find_invariant(data, id_or_name)
    if inv is None:
        _die(f"Invariant '{id_or_name}' not found")
    return inv


def _print_summary(data: CommentedMap) -> None:
    s = data.get("status_summary", {})
    print(f"  summary: live={s.get('live',0)}  partial={s.get('partial',0)}  "
          f"planned={s.get('planned',0)}  total={s.get('total',0)}")


def _ok(msg: str)   -> None: print(f"✓ {msg}")
def _info(msg: str) -> None: print(f"  {msg}")
def _warn(msg: str) -> None: print(f"⚠ {msg}", file=sys.stderr)
def _die(msg: str)  -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

# ── Argument parser ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="invariant",
        description="Lightweight invariant management CLI for the OCR-docs brain.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all invariants
  python3 scripts/invariant.py list

  # List only security_isolation invariants
  python3 scripts/invariant.py list --group security_isolation

  # List only partial invariants
  python3 scripts/invariant.py list --status partial

  # Create a new planned invariant
  python3 scripts/invariant.py create \\
    --name my_new_invariant \\
    --group security_isolation \\
    --title "My New Invariant" \\
    --enforces "What it enforces." \\
    --applies-to ose,wkrp \\
    --rationale "Why this invariant exists."

  # Create a live invariant (gate already wired)
  python3 scripts/invariant.py create \\
    --name cross_repo_import_isolation \\
    --group security_isolation \\
    --title "Cross-Repo Import Isolation" \\
    --enforces "No module-level imports cross repo boundaries." \\
    --applies-to ose,wkrp,oaw \\
    --status live \\
    --pr-ref "OSE PR #291"

  # Flip an invariant from partial to live
  python3 scripts/invariant.py flip 9 --to live --pr-ref "OSE PR #255" \\
    --rationale "Gate wired to T0 invariants shard."

  # Update title and enforcement statement
  python3 scripts/invariant.py update 22 \\
    --title "Updated Title" \\
    --enforcement-statement "L0 script gate: scripts/check-cross-repo-imports.sh" \\
    --pr-ref "OSE PR #291"

  # Cancel an invariant (preserves audit trail)
  python3 scripts/invariant.py delete 5 \\
    --rationale "Superseded by Invariant #23 which enforces a stricter version."

  # Validate structural integrity
  python3 scripts/invariant.py validate
""")

    sub = p.add_subparsers(dest="cmd", required=True)

    # ── list ──
    lp = sub.add_parser("list", help="List invariants in tabular form")
    lp.add_argument("--group",  help="Filter by group ID (e.g. security_isolation)")
    lp.add_argument("--status", choices=list(VALID_STATUSES), help="Filter by status")

    # ── create ──
    cp = sub.add_parser("create", help="Create a new invariant")
    cp.add_argument("--name",     required=True, metavar="NAME",
                    help="snake_case identifier (e.g. cross_repo_import_isolation)")
    cp.add_argument("--group",    required=True, metavar="GROUP",
                    help="Group ID — must exist in invariant_groups (e.g. security_isolation)")
    cp.add_argument("--title",    required=True, metavar="TITLE",
                    help="Human-readable title")
    cp.add_argument("--enforces", required=True, metavar="TEXT",
                    help="What this invariant enforces (1–3 sentences)")
    cp.add_argument("--applies-to", required=True, dest="applies_to", metavar="LIST",
                    help="Comma-separated product codes (e.g. ose,wkrp,oaw)")
    cp.add_argument("--status",   default="planned",
                    choices=list(VALID_STATUSES), help="Initial status (default: planned)")
    cp.add_argument("--test-file", dest="test_file", metavar="PATH",
                    help="Relative path to test/spec file (omit for planned)")
    cp.add_argument("--protective-statement",  dest="protective_statement", metavar="TEXT")
    cp.add_argument("--enforcement-statement", dest="enforcement_statement", metavar="TEXT")
    cp.add_argument("--rationale",  metavar="TEXT", help="Why this invariant was created")
    cp.add_argument("--pr-ref",     dest="pr_ref", metavar="REF",
                    help="PR reference (e.g. 'OSE PR #291')")

    # ── update ──
    up = sub.add_parser("update", help="Update one or more fields on an existing invariant")
    up.add_argument("id_or_name", help="Invariant ID (integer) or snake_case name")
    up.add_argument("--status",   choices=list(VALID_STATUSES))
    up.add_argument("--title",    metavar="TEXT")
    up.add_argument("--enforces", metavar="TEXT")
    up.add_argument("--test-file", dest="test_file", metavar="PATH")
    up.add_argument("--protective-statement",  dest="protective_statement", metavar="TEXT")
    up.add_argument("--enforcement-statement", dest="enforcement_statement", metavar="TEXT")
    up.add_argument("--rationale", metavar="TEXT")
    up.add_argument("--pr-ref",    dest="pr_ref", metavar="REF")

    # ── flip ──
    fp = sub.add_parser("flip",
                        help="Flip an invariant status (shortcut for the common partial→live transition)")
    fp.add_argument("id_or_name", help="Invariant ID or name")
    fp.add_argument("--to",       required=True, metavar="STATUS",
                    choices=list(VALID_STATUSES), help="Target status")
    fp.add_argument("--pr-ref",   required=True, dest="pr_ref", metavar="REF",
                    help="Activation PR reference (required — records what shipped)")
    fp.add_argument("--rationale", metavar="TEXT")

    # ── delete ──
    dp = sub.add_parser("delete",
                        help="Mark an invariant as canceled (preserves audit trail — never hard-deletes)")
    dp.add_argument("id_or_name",  help="Invariant ID or name")
    dp.add_argument("--rationale", required=True, metavar="TEXT",
                    help="Why it was canceled (required — goes into audit history)")
    dp.add_argument("--pr-ref",    dest="pr_ref", metavar="REF")

    # ── validate ──
    sub.add_parser("validate",
                   help="Validate structural integrity of architectural-invariants.yaml")

    return p


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    data   = load_brain()

    dispatch = {
        "list":     cmd_list,
        "create":   cmd_create,
        "update":   cmd_update,
        "flip":     cmd_flip,
        "delete":   cmd_delete,
        "validate": cmd_validate,
    }
    dispatch[args.cmd](args, data)


if __name__ == "__main__":
    main()
