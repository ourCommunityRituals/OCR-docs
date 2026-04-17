"""
OCR Deployment Truth Dashboard — v2

Multi-app roster + per-app detail view.

Structure:
  - index.html              — roster of all apps: totals, pass%, 30-day sparkline,
                              plus day/week/month trend chart at the top.
  - app-<key>.html          — per-app detail: live probes, test pyramid, drift,
                              every URL clickable.
  - .state.json             — last-run cache per suite (keyed by suite key).
  - .history.json           — append-only snapshot log for trend charts.

Apps (in roster order):
  1. ocr-brain   — first, because it validates cross-app sync (governance pyramid).
  2. ose-staging — OSE Cloudflare Worker on stg.oursharedevents.com + test pyramid.
  3. ose-prod    — OSE Cloudflare Worker on oursharedevents.com (probes only).

Usage:
  py dashboard.py                         # probe every app, regenerate index + detail pages
  py dashboard.py --open                  # ...also open index.html in default browser
  py dashboard.py --app ose-staging       # regenerate only one app's detail page
  py dashboard.py --run-tests t0-unit     # run one suite, update state + history
  py dashboard.py --run-tests all         # run every suite in every app
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────

OSE_REPO = Path("C:/Users/mzdan/dev/ourCommunityRituals/ourSharedEvents")
BRAIN_REPO = Path("C:/Users/mzdan/dev/ourCommunityRituals/OCR-docs")
DASHBOARD_DIR = BRAIN_REPO / "dashboard"
STATE_FILE = DASHBOARD_DIR / ".state.json"
HISTORY_FILE = DASHBOARD_DIR / ".history.json"
INDEX_HTML = DASHBOARD_DIR / "index.html"

STAGING_BASE = "https://stg.oursharedevents.com"
PROD_BASE = "https://oursharedevents.com"

SIBLING_DIR = Path("C:/Users/mzdan/dev/ourCommunityRituals")
STORIES_FILE = DASHBOARD_DIR / ".stories.json"

GH_ORG = "https://github.com/ourCommunityRituals"
OSE_GITHUB   = f"{GH_ORG}/ourSharedEvents"
BRAIN_GITHUB = f"{GH_ORG}/OCR-docs"
WKRP_GITHUB  = f"{GH_ORG}/ourWKRP"
OSG_GITHUB   = f"{GH_ORG}/ourSharedGames"
OSM_GITHUB   = f"{GH_ORG}/ourSharedMagnets"
OSP_GITHUB   = f"{GH_ORG}/ourSharedPulse"
OSR_GITHUB   = f"{GH_ORG}/ourSharedRecords"
OA_GITHUB    = f"{GH_ORG}/ourAirwaves"

# Canonical routes probed for any app with a live base URL.
# (path, label, expected_status, aliases)
# expected_status: int | tuple of ints
# - 200 = publicly visible
# - 302 = Cloudflare Access-protected (redirects to cloudflareaccess.com login)
# - 403 = feature-flag gated (tier-locked)
# - 405 = method not allowed (e.g. POST-only endpoint probed with GET)
ROUTES = [
    ("/health",              "Health",                  200,       []),
    ("/api/status",          "API Status",              200,       []),
    ("/",                    "Landing",                 200,       ["/home", "/welcome", "/landing", "/about", "/info"]),
    ("/events",              "Public Events",           200,       ["/public", "/schedule", "/calendar", "/agenda", "/lineup"]),
    ("/briefing",            "CEO Briefing",            200,       ["/overview", "/summary"]),
    ("/display",             "Display / TV",            200,       ["/tv", "/kiosk", "/screen"]),
    ("/poster",              "Poster / Signage",        200,       ["/posters", "/flyers", "/tabletop", "/tent", "/signage"]),
    ("/sharedReport",        "Shared Report (tier-gated)", (200, 403), ["/report", "/analytics", "/reports", "/insights", "/stats"]),
    ("/api/v2/events",       "Public Events API",       200,       []),
    ("/subscribe",           "Newsletter Subscribe",    (200, 405),["/signup", "/newsletter"]),
    ("/manage",              "Admin Gateway (CF Access)",       302, ["/dashboard", "/create"]),
    ("/admin",               "Admin UI (CF Access)",            302, []),
    ("/api/v2/admin/events", "Admin: Events API (CF Access)",   302, []),
    ("/api/v2/admin/sponsors","Admin: Sponsors API (CF Access)",302, []),
    ("/api/v2/admin/flags",  "Admin: Flags API (CF Access)",    302, []),
]

# Test pyramid — every suite known to any app.
TEST_FEATURES = [
    {"tier": "Brain", "name": "Brain Test Pyramid (OCR-docs)",
     "dir": "ocr-docs-brain/tests", "run_cmd": "py ocr-docs-brain/tests/run_all.py",
     "cwd": str(BRAIN_REPO), "key": "brain"},
    {"tier": "T0", "name": "Gate — Unit (Vitest)",
     "dir": "tests/unit", "run_cmd": "npm test", "key": "t0-unit"},
    {"tier": "T0", "name": "Gate — Contract",
     "dir": "tests/contract", "run_cmd": "npx vitest run tests/contract", "key": "t0-contract"},
    {"tier": "T0", "name": "Gate — Worker Schema (D1)",
     "dir": "workers/oursharedevents/tests", "run_cmd": "npm test",
     "cwd": "workers/oursharedevents", "key": "t0-d1-schema"},
    {"tier": "T0", "name": "Gate — TypeScript + Lint",
     "dir": "workers/oursharedevents/src",
     "run_cmd": "npx tsc --noEmit && npx eslint config/ scripts/ tests/unit/ tests/contract/",
     "key": "t0-typelint"},
    {"tier": "T2", "name": "Smoke — Security XSS + Auth",
     "dir": "tests/e2e/1-smoke",
     "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/1-smoke/security-smoke.spec.js",
     "key": "t2-security-smoke"},
    {"tier": "T2", "name": "Smoke — IAC Health + Fail-Fast",
     "dir": "tests/api/smoke",
     "run_cmd": "npx playwright test --config=playwright.smoke.config.ts tests/api/smoke/api-health.spec.ts tests/api/smoke/fail-fast-gates.spec.ts",
     "key": "t2-iac-smoke"},
    {"tier": "T3", "name": "Contract — Newman API",
     "dir": "postman/collections",
     "run_cmd": "npx newman run postman/collections/ose-api.json -e postman/environments/ose-staging.json --reporters cli",
     "key": "t3-newman-api"},
    {"tier": "T3", "name": "Contract — Newman Pages",
     "dir": "postman/collections",
     "run_cmd": "npx newman run postman/collections/ose-pages.json -e postman/environments/ose-staging.json --reporters cli",
     "key": "t3-newman-pages"},
    {"tier": "T4", "name": "Functional — Architecture Invariants",
     "dir": "tests/e2e/0-architecture",
     "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/0-architecture/",
     "key": "t4-arch"},
    {"tier": "T4", "name": "Functional — Core Journeys",
     "dir": "tests/e2e/3-flows",
     "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/3-flows/sponsor-journey.spec.ts",
     "key": "t4-journey"},
    {"tier": "T4", "name": "Functional — UI Smoke",
     "dir": "tests/ui/smoke", "run_cmd": "npm run test:ui:smoke", "key": "t4-ui"},
]

FEATURE_BY_KEY = {f["key"]: f for f in TEST_FEATURES}

# App definitions — order controls roster order.
#   `lane` groups multiple app rows into one Story-Flow column
#     (e.g. ose-staging + ose-prod both map to lane "ose").
#   `role` = "orchestrator" | "downstream" | "stub"
#   Brain is first because it validates cross-app sync (governance pyramid)
#   and, going forward, is the orchestrator that kicks Linear stories which
#   fan out to the downstream apps.
APPS = [
    # ── Orchestrator ─────────────────────────────────────────────────────────
    {
        "key": "ocr-brain", "name": "OCR-docs Brain", "abbr": "Brain",
        "subtitle": "Orchestrator · 511-check governance pyramid · kicks Linear stories",
        "role": "orchestrator", "lane": "ocr-brain",
        "base": None, "probes": False,
        "repo": BRAIN_REPO, "github": BRAIN_GITHUB,
        "suite_keys": ["brain"], "drift": False,
    },
    # ── Live downstream (OSE: two environments, so two rows) ─────────────────
    {
        "key": "ose-staging", "name": "OSE — Staging", "abbr": "OSE stg",
        "subtitle": "ourSharedEvents · Cloudflare Worker · stg.oursharedevents.com",
        "role": "downstream", "lane": "ose",
        "base": STAGING_BASE, "probes": True,
        "repo": OSE_REPO, "github": OSE_GITHUB,
        "suite_keys": [
            "t0-unit", "t0-contract", "t0-d1-schema", "t0-typelint",
            "t2-security-smoke", "t2-iac-smoke",
            "t3-newman-api", "t3-newman-pages",
            "t4-arch", "t4-journey", "t4-ui",
        ],
        "drift": True,
    },
    {
        "key": "ose-prod", "name": "OSE — Production", "abbr": "OSE prod",
        "subtitle": "ourSharedEvents · Cloudflare Worker · oursharedevents.com",
        "role": "downstream", "lane": "ose",
        "base": PROD_BASE, "probes": True,
        "repo": OSE_REPO, "github": OSE_GITHUB,
        "suite_keys": [], "drift": True,
    },
    # ── Other downstream apps (repos active; deployment URLs pending) ────────
    {
        "key": "wkrp", "name": "WKRP · ourWKRP", "abbr": "WKRP",
        "subtitle": "Cloudflare Worker · stg.ourwkrp.com + ourwkrp.com (reserved, not deployed)",
        "role": "downstream", "lane": "wkrp",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourWKRP", "github": WKRP_GITHUB,
        "suite_keys": [], "drift": False,
    },
    # ── Stubs: repos initialized, awaiting first build ───────────────────────
    {
        "key": "osg", "name": "OSG · ourSharedGames", "abbr": "OSG",
        "subtitle": "Games · repo ready, no deployment yet",
        "role": "stub", "lane": "osg",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourSharedGames", "github": OSG_GITHUB,
        "suite_keys": [], "drift": False,
    },
    {
        "key": "osm", "name": "OSM · ourSharedMagnets", "abbr": "OSM",
        "subtitle": "Magnets · repo ready, no deployment yet",
        "role": "stub", "lane": "osm",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourSharedMagnets", "github": OSM_GITHUB,
        "suite_keys": [], "drift": False,
    },
    {
        "key": "osp", "name": "OSP · ourSharedPulse", "abbr": "OSP",
        "subtitle": "Pulse · repo ready, no deployment yet",
        "role": "stub", "lane": "osp",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourSharedPulse", "github": OSP_GITHUB,
        "suite_keys": [], "drift": False,
    },
    {
        "key": "osr", "name": "OSR · ourSharedRecords", "abbr": "OSR",
        "subtitle": "Records · repo ready, no deployment yet",
        "role": "stub", "lane": "osr",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourSharedRecords", "github": OSR_GITHUB,
        "suite_keys": [], "drift": False,
    },
    {
        "key": "oa", "name": "OA · OurAirwaves", "abbr": "OA",
        "subtitle": "OurAirwaves · repo ready, no deployment yet",
        "role": "stub", "lane": "oa",
        "base": None, "probes": False,
        "repo": SIBLING_DIR / "ourAirwaves", "github": OA_GITHUB,
        "suite_keys": [], "drift": False,
    },
]

APP_BY_KEY = {a["key"]: a for a in APPS}
SUITE_TO_APP = {k: a["key"] for a in APPS for k in a["suite_keys"]}

# Lane columns for the Story-Flow view — one column per unique lane,
# preserving APPS order. Brain is always the leftmost (orchestrator).
def _lane_columns() -> list[tuple[str, str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []
    for a in APPS:
        if a["lane"] in seen:
            continue
        seen.add(a["lane"])
        out.append((a["lane"], a["abbr"].split(" ")[0], a["name"].split(" ·")[0]))
    return out

LANES = _lane_columns()


# ─── Utilities ─────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args: str, cwd: Path = OSE_REPO) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace",
        )
        return r.stdout.strip()
    except Exception as e:
        return f"(git error: {e})"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "suites": {}}


def save_state(state: dict) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "snapshots": []}


def save_history(h: dict) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(h, indent=2), encoding="utf-8")


def append_snapshot(history: dict, suite_key: str, result: dict) -> None:
    """Append a trend row for one suite's run result."""
    app_key = SUITE_TO_APP.get(suite_key)
    if not app_key:
        return
    history.setdefault("snapshots", []).append({
        "ts": result.get("when", now_iso()),
        "app": app_key,
        "suite": suite_key,
        "pass": result.get("pass") or 0,
        "fail": result.get("fail") or 0,
        "skip": result.get("skip") or 0,
        "total": result.get("total") or 0,
        "result": result.get("result"),
        "rc": result.get("rc"),
    })


# ─── Probes ────────────────────────────────────────────────────────────────────

class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent urllib from silently following 3xx — we want the server's actual response."""
    def http_error_301(self, req, fp, code, msg, headers): return None
    def http_error_302(self, req, fp, code, msg, headers): return None
    def http_error_303(self, req, fp, code, msg, headers): return None
    def http_error_307(self, req, fp, code, msg, headers): return None
    def http_error_308(self, req, fp, code, msg, headers): return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def probe_one(base: str, path: str, timeout: float = 10.0) -> dict:
    """Probe one URL. Does NOT follow redirects — surfaces the server's actual response."""
    url = base + path
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "ocr-dashboard/2.0"})
        with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as resp:
            body = resp.read()
            elapsed_ms = int((time.time() - t0) * 1000)
            text = body[:400].decode("utf-8", errors="replace")
            return {
                "url": url, "status": resp.status, "bytes": len(body), "ms": elapsed_ms,
                "body_head": text, "redirect": resp.headers.get("Location"), "error": None,
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        body = e.read() if hasattr(e, "read") else b""
        return {"url": url, "status": e.code, "bytes": len(body), "ms": elapsed_ms,
                "body_head": body[:400].decode("utf-8", errors="replace"),
                "redirect": e.headers.get("Location") if e.headers else None, "error": None}
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return {"url": url, "status": None, "bytes": 0, "ms": elapsed_ms,
                "body_head": "", "redirect": None, "error": str(e)}


def probe_all_endpoints(base: str) -> list[dict]:
    out: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(probe_one, base, r[0]): r for r in ROUTES}
        for fut in concurrent.futures.as_completed(futures):
            route = futures[fut]
            probe = fut.result()
            probe["label"] = route[1]
            probe["expected"] = route[2]
            probe["aliases"] = route[3]
            probe["path"] = route[0]
            out.append(probe)
    order = {r[0]: i for i, r in enumerate(ROUTES)}
    out.sort(key=lambda d: order[d["path"]])
    return out


def status_class(probe: dict) -> tuple[str, str]:
    """Return (css_class, text_summary) for an endpoint probe."""
    if probe.get("error") or probe.get("status") is None:
        return "fail", f"ERR {probe.get('error','?')[:40]}"
    expected = probe.get("expected")
    status = probe["status"]
    if isinstance(expected, int):
        ok = (status == expected)
    elif isinstance(expected, tuple):
        ok = status in expected
    else:
        ok = 200 <= status < 400
    if ok:
        return "pass", f"{status} · {probe['bytes']:,}b · {probe['ms']}ms"
    return "fail", f"{status} (expected {expected}) · {probe['bytes']:,}b"


# ─── Git / deployment state ───────────────────────────────────────────────────

def parse_deployed_version(health_probe: dict) -> dict:
    try:
        data = json.loads(health_probe.get("body_head", "") or "{}")
    except Exception:
        return {}
    version = data.get("version", "")
    m = re.match(r"(?:stg|prod)-([0-9a-f]+)-(\d{8})", version)
    if not m:
        return {"version": version}
    return {"version": version, "commit": m.group(1), "date": m.group(2)}


def deployment_state(base: str, repo: Path) -> dict:
    """Probe /health for `base`, compare deployed SHA to origin/main of `repo`."""
    health = probe_one(base, "/health", timeout=10)
    dep = parse_deployed_version(health)
    git("fetch", "origin", "--quiet", cwd=repo)
    origin_main = git("rev-parse", "--short", "origin/main", cwd=repo)
    origin_main_long = git("rev-parse", "origin/main", cwd=repo)
    origin_main_msg = git("log", "-1", "--format=%s", "origin/main", cwd=repo)
    origin_main_date = git("log", "-1", "--format=%ci", "origin/main", cwd=repo)

    commits_since: list[dict] = []
    drift_worker = 0
    drift_ci = 0
    if dep.get("commit"):
        log_lines = git("log", "--oneline", f"{dep['commit']}..origin/main", cwd=repo).splitlines()
        for line in log_lines[:50]:
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            sha, msg = parts
            files = git("show", "--name-only", "--format=", sha, cwd=repo).splitlines()
            worker_touched = any(
                f.startswith("workers/oursharedevents/src/")
                or f.startswith("workers/oursharedevents/wrangler")
                for f in files if f
            )
            ci_touched = any(
                f.startswith(".github/workflows/")
                or f.startswith("tests/")
                or f.startswith("postman/")
                or f.startswith("scripts/")
                for f in files if f
            )
            tag = "worker" if worker_touched else ("ci/test" if ci_touched else "other")
            if worker_touched:
                drift_worker += 1
            else:
                drift_ci += 1
            commits_since.append({"sha": sha, "msg": msg, "tag": tag})

    return {
        "probed_at": now_iso(),
        "base": base,
        "health": health,
        "deployed": dep,
        "origin_main": {"short": origin_main, "sha": origin_main_long,
                        "msg": origin_main_msg, "date": origin_main_date},
        "commits_since_deploy": commits_since,
        "drift_worker": drift_worker,
        "drift_ci": drift_ci,
    }


# ─── Test feature inventory ───────────────────────────────────────────────────

TEST_FUNC_RE = re.compile(r"(?m)^\s*(?:it|test|describe)\s*\(")


def count_tests_in_dir(dir_path: Path) -> dict:
    if not dir_path.exists():
        return {"files": 0, "test_calls": 0, "exists": False}
    files = 0
    calls = 0
    for p in dir_path.rglob("*"):
        if not p.is_file():
            continue
        name = p.name.lower()
        if not (name.endswith(".test.js") or name.endswith(".test.ts")
                or name.endswith(".spec.js") or name.endswith(".spec.ts")):
            continue
        if "node_modules" in p.parts or "archive" in p.parts:
            continue
        files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            calls += len(TEST_FUNC_RE.findall(text))
        except Exception:
            pass
    return {"files": files, "test_calls": calls, "exists": True}


def count_newman_tests(collection_path: Path) -> dict:
    if not collection_path.exists():
        return {"files": 0, "test_calls": 0, "exists": False}
    try:
        doc = json.loads(collection_path.read_text(encoding="utf-8"))
    except Exception:
        return {"files": 0, "test_calls": 0, "exists": True, "error": "parse"}
    requests = 0
    tests = 0

    def walk(items):
        nonlocal requests, tests
        for it in items or []:
            if "item" in it:
                walk(it["item"])
                continue
            if "request" in it:
                requests += 1
                for ev in it.get("event", []) or []:
                    if ev.get("listen") == "test":
                        script = (ev.get("script") or {}).get("exec") or []
                        if isinstance(script, list):
                            script = "\n".join(script)
                        tests += len(re.findall(r"\bpm\.test\s*\(", script or ""))
    walk(doc.get("item", []))
    return {"files": 1, "test_calls": tests, "requests": requests, "exists": True}


def inventory_features() -> list[dict]:
    """Build rows for every feature with static counts + cached last-run."""
    state = load_state()
    cached = state.get("suites", {})
    rows: list[dict] = []
    for feat in TEST_FEATURES:
        cwd = Path(feat.get("cwd", OSE_REPO))
        if feat["key"].startswith("t3-newman"):
            coll = OSE_REPO / feat["dir"] / (
                "ose-api.json" if feat["key"] == "t3-newman-api" else "ose-pages.json"
            )
            inv = count_newman_tests(coll)
        else:
            if Path(feat["dir"]).parts and Path(feat["dir"]).parts[0] == "ocr-docs-brain":
                inv = count_tests_in_dir(cwd / feat["dir"])
            else:
                inv = count_tests_in_dir(OSE_REPO / feat["dir"])
        run = cached.get(feat["key"], {})
        rows.append({
            **feat,
            "files": inv.get("files", 0),
            "test_calls": inv.get("test_calls", 0),
            "requests": inv.get("requests"),
            "exists": inv.get("exists", False),
            "last_run": run.get("when"),
            "result": run.get("result"),
            "pass": run.get("pass"),
            "fail": run.get("fail"),
            "skip": run.get("skip"),
            "total": run.get("total"),
            "detail": run.get("detail"),
            "rc": run.get("rc"),
            "elapsed_s": run.get("elapsed_s"),
            "output_tail": run.get("output_tail"),
        })
    return rows


# ─── Per-app aggregation ──────────────────────────────────────────────────────

def features_for_app(app: dict, all_features: list[dict]) -> list[dict]:
    keys = set(app["suite_keys"])
    return [f for f in all_features if f["key"] in keys]


def summarize_app(app: dict, all_features: list[dict], probes: list[dict] | None) -> dict:
    feats = features_for_app(app, all_features)
    suite_pass = sum(1 for f in feats if f.get("result") == "pass")
    suite_fail = sum(1 for f in feats if f.get("result") == "fail")
    suite_never = len(feats) - suite_pass - suite_fail

    t_pass = sum(f.get("pass") or 0 for f in feats if f.get("total") is not None)
    t_fail = sum(f.get("fail") or 0 for f in feats if f.get("total") is not None)
    t_skip = sum(f.get("skip") or 0 for f in feats if f.get("total") is not None)
    t_total = t_pass + t_fail + t_skip

    last_run = None
    for f in feats:
        ts = f.get("last_run")
        if ts and (not last_run or ts > last_run):
            last_run = ts

    pages_pass = pages_total = 0
    if probes is not None:
        pages_total = len(probes)
        pages_pass = sum(1 for p in probes if status_class(p)[0] == "pass")

    # Overall verdict
    if suite_fail > 0 or (pages_total and pages_pass < pages_total):
        verdict = "fail"
    elif t_total > 0 or (pages_total and pages_pass == pages_total):
        verdict = "pass"
    else:
        verdict = "never"

    return {
        "suites": {"pass": suite_pass, "fail": suite_fail, "never": suite_never,
                   "total": len(feats)},
        "tests": {"pass": t_pass, "fail": t_fail, "skip": t_skip, "total": t_total,
                  "pct": (100.0 * t_pass / t_total) if t_total else None},
        "pages": {"pass": pages_pass, "total": pages_total} if probes is not None else None,
        "last_run": last_run,
        "verdict": verdict,
    }


# ─── History aggregation for trend charts ─────────────────────────────────────

def history_points_by_bucket(history: dict, app_key: str, bucket: str, n: int) -> list[tuple[str, float | None]]:
    """Return n buckets of pass% for the given app.
    bucket: 'day' | 'week' | 'month'
    """
    snaps = [s for s in history.get("snapshots", []) if s.get("app") == app_key]
    if not snaps:
        return []

    def bucket_key(ts: str) -> str:
        d = datetime.strptime(ts[:10], "%Y-%m-%d").date()
        if bucket == "day":
            return d.isoformat()
        if bucket == "week":
            monday = d - timedelta(days=d.weekday())
            return monday.isoformat()
        return f"{d.year:04d}-{d.month:02d}"

    today = datetime.now(timezone.utc).date()
    if bucket == "day":
        keys = [(today - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]
    elif bucket == "week":
        monday = today - timedelta(days=today.weekday())
        keys = [(monday - timedelta(weeks=i)).isoformat() for i in range(n - 1, -1, -1)]
    else:
        keys = []
        y, m = today.year, today.month
        for i in range(n - 1, -1, -1):
            mm = m - i
            yy = y
            while mm <= 0:
                mm += 12
                yy -= 1
            keys.append(f"{yy:04d}-{mm:02d}")

    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for s in snaps:
        by_bucket[bucket_key(s["ts"])].append(s)

    # For each bucket, use the latest per-suite snapshot (last one wins).
    results: list[tuple[str, float | None]] = []
    for k in keys:
        in_bucket = by_bucket.get(k, [])
        if not in_bucket:
            results.append((k, None))
            continue
        latest_per_suite: dict[str, dict] = {}
        for s in in_bucket:
            existing = latest_per_suite.get(s["suite"])
            if existing is None or s["ts"] > existing["ts"]:
                latest_per_suite[s["suite"]] = s
        p = sum(s.get("pass") or 0 for s in latest_per_suite.values())
        t = sum(s.get("total") or 0 for s in latest_per_suite.values())
        pct = (100.0 * p / t) if t else None
        results.append((k, pct))
    return results


# ─── Test runners ─────────────────────────────────────────────────────────────

def run_cmd(cmd: str, cwd: Path, timeout: int = 900) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return {"rc": r.returncode, "stdout": r.stdout[-8000:],
                "stderr": r.stderr[-2000:], "elapsed_s": int(time.time() - t0)}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "stdout": "", "stderr": f"Timed out after {timeout}s",
                "elapsed_s": timeout}
    except Exception as e:
        return {"rc": -1, "stdout": "", "stderr": str(e), "elapsed_s": int(time.time() - t0)}


def parse_test_output(output: str) -> dict:
    out = {"pass": None, "fail": None, "skip": None, "total": None, "detail": None}

    # Brain pyramid
    ps = re.search(r"PYRAMID SUMMARY:\s*(\d+)\s+pass\s*/\s*(\d+)\s+fail\s*/\s*(\d+)\s+skip", output)
    if ps:
        out["pass"] = int(ps.group(1))
        out["fail"] = int(ps.group(2))
        out["skip"] = int(ps.group(3))
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        level_tests = re.findall(r"(\d+)\s+pass\s*/\s*(\d+)\s+fail\s*\(total\s+(\d+)\)", output)
        if level_tests:
            tests_pass = sum(int(p) for p, _, _ in level_tests)
            tests_fail = sum(int(f) for _, f, _ in level_tests)
            out["detail"] = f"{tests_pass} tests pass, {tests_fail} fail across {len(level_tests)} passing level(s) (of {out['total']})"
        return out

    m = re.search(r"Tests\s+(\d+)\s+passed(?:\s*\|\s*(\d+)\s+failed)?(?:\s*\|\s*(\d+)\s+skipped)?", output)
    if m:
        out["pass"] = int(m.group(1))
        out["fail"] = int(m.group(2) or 0)
        out["skip"] = int(m.group(3) or 0)
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        return out
    p = re.search(r"(\d+)\s+passed(?:[\s(])", output)
    f = re.search(r"(\d+)\s+failed(?:[\s(])", output)
    s = re.search(r"(\d+)\s+skipped(?:[\s(])", output)
    if p or f:
        out["pass"] = int(p.group(1)) if p else 0
        out["fail"] = int(f.group(1)) if f else 0
        out["skip"] = int(s.group(1)) if s else 0
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        return out
    na = re.search(r"assertions[^\d]+(\d+)[^\d]+(\d+)", output)
    if na:
        out["pass"] = int(na.group(1))
        out["fail"] = int(na.group(2))
        out["total"] = out["pass"] + out["fail"]
        out["skip"] = 0
        return out
    return out


def run_feature(feat: dict) -> dict:
    cwd = Path(feat.get("cwd", OSE_REPO))
    result = run_cmd(feat["run_cmd"], cwd=cwd, timeout=900)
    combined = (result["stdout"] + "\n" + result["stderr"]).strip()
    parsed = parse_test_output(combined)
    pf = parsed.get("fail")
    if result["rc"] == 0 and (pf is None or pf == 0):
        verdict = "pass"
    elif pf is not None and pf > 0:
        verdict = "fail"
    else:
        verdict = "fail" if result["rc"] != 0 else "pass"
    return {
        "when": now_iso(), "result": verdict, "rc": result["rc"],
        "elapsed_s": result["elapsed_s"],
        "pass": parsed.get("pass"), "fail": parsed.get("fail"),
        "skip": parsed.get("skip"), "total": parsed.get("total"),
        "detail": parsed.get("detail"),
        "output_tail": combined[-1500:],
    }


# ─── SVG helpers ──────────────────────────────────────────────────────────────

def donut_svg(segments: list[tuple[str, float, str]], size: int = 96, stroke: int = 16) -> str:
    """Draw a donut chart. segments: list of (label, value, color)."""
    total = sum(max(0.0, v) for _, v, _ in segments)
    r = (size - stroke) / 2
    cx = cy = size / 2
    circumference = 2 * math.pi * r
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1f2028" stroke-width="{stroke}" />']
    if total > 0:
        offset = 0.0
        for _label, value, color in segments:
            if value <= 0:
                continue
            length = (value / total) * circumference
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
                f'stroke-width="{stroke}" stroke-dasharray="{length:.3f} {circumference:.3f}" '
                f'stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 {cx} {cy})" />'
            )
            offset += length
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true">{"".join(parts)}</svg>'


def sparkline_svg(values: list[float | None], width: int = 120, height: int = 28) -> str:
    """Draw a sparkline 0-100 from the first non-None value onward.
    None values are drawn as gaps (path breaks)."""
    if not values:
        return ""
    # Forward-fill None at start; keep internal None as gap
    pad = 2
    n = len(values)
    xs = [(i / max(n - 1, 1)) * (width - 2 * pad) + pad for i in range(n)]
    ys = []
    for v in values:
        if v is None:
            ys.append(None)
        else:
            ys.append((1 - max(0.0, min(100.0, v)) / 100.0) * (height - 2 * pad) + pad)

    # Build polyline segments (break on None)
    segments = []
    cur: list[str] = []
    for x, y in zip(xs, ys):
        if y is None:
            if cur:
                segments.append(cur)
                cur = []
        else:
            cur.append(f"{x:.1f},{y:.1f}")
    if cur:
        segments.append(cur)

    polylines = "".join(
        f'<polyline points="{" ".join(seg)}" fill="none" stroke="#a78bfa" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />'
        for seg in segments if len(seg) >= 1
    )

    # Last known dot
    dot = ""
    last_y = None
    last_x = None
    last_v = None
    for x, y, v in zip(xs, ys, values):
        if y is not None:
            last_y = y
            last_x = x
            last_v = v
    if last_y is not None:
        color = "#34d399" if (last_v or 0) >= 99.9 else ("#fbbf24" if (last_v or 0) >= 70 else "#f87171")
        dot = f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2.5" fill="{color}" />'

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" aria-hidden="true">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="transparent" />'
        f'{polylines}{dot}'
        f'</svg>'
    )


def trend_chart_svg(series: list[tuple[str, list[tuple[str, float | None]]]],
                    width: int = 820, height: int = 180) -> str:
    """Draw a multi-series line chart. Each series: (name, color, [(bucket_key, value)])."""
    pad_l, pad_r, pad_t, pad_b = 36, 12, 14, 22
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    # Flatten all values for axis
    has_data = any(v is not None for _n, _c, pts in series for _k, v in pts)
    if not has_data or not series:
        return (
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<rect width="{width}" height="{height}" fill="#14141c" stroke="#1f2028" rx="8" />'
            f'<text x="{width/2}" y="{height/2}" text-anchor="middle" fill="#6b7280" font-size="12" font-family="system-ui">No history yet — run a suite (<tspan fill="#c4b5fd" font-family="monospace">py dashboard.py --run-tests &lt;key&gt;</tspan>) to start plotting.</text>'
            f'</svg>'
        )

    n_points = len(series[0][2]) if series else 0
    xs = [pad_l + (i / max(n_points - 1, 1)) * plot_w for i in range(n_points)]

    # y-axis: 0 → 100
    def y_at(v: float) -> float:
        return pad_t + (1 - max(0.0, min(100.0, v)) / 100.0) * plot_h

    # gridlines at 0/50/100
    grid_parts = []
    for tick in (0, 50, 100):
        y = y_at(tick)
        grid_parts.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
            f'stroke="#1f2028" stroke-width="1" stroke-dasharray="2 3" />'
        )
        grid_parts.append(
            f'<text x="{pad_l - 6}" y="{y + 3:.1f}" text-anchor="end" fill="#6b7280" '
            f'font-size="10" font-family="system-ui">{tick}%</text>'
        )

    # x-axis labels at first, middle, last
    x_labels = []
    if n_points > 0 and series:
        keys = [k for k, _ in series[0][2]]
        for i in (0, n_points // 2, n_points - 1):
            if 0 <= i < len(keys):
                x_labels.append(
                    f'<text x="{xs[i]:.1f}" y="{height - 6}" text-anchor="middle" '
                    f'fill="#6b7280" font-size="10" font-family="system-ui">{html.escape(keys[i])}</text>'
                )

    # series lines + dots
    series_svg = []
    legend_parts = []
    for idx, (name, color, pts) in enumerate(series):
        pieces: list[list[str]] = []
        cur: list[str] = []
        for i, (_k, v) in enumerate(pts):
            if v is None:
                if cur:
                    pieces.append(cur)
                    cur = []
            else:
                cur.append(f"{xs[i]:.1f},{y_at(v):.1f}")
        if cur:
            pieces.append(cur)
        for seg in pieces:
            if len(seg) >= 1:
                series_svg.append(
                    f'<polyline points="{" ".join(seg)}" fill="none" stroke="{color}" '
                    f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />'
                )
                if len(seg) == 1:
                    x, y = seg[0].split(",")
                    series_svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" />')
        # dot the final value
        last_v = next((v for _, v in reversed(pts) if v is not None), None)
        last_i = next((i for i in range(len(pts) - 1, -1, -1) if pts[i][1] is not None), None)
        if last_v is not None and last_i is not None:
            series_svg.append(
                f'<circle cx="{xs[last_i]:.1f}" cy="{y_at(last_v):.1f}" r="3" fill="{color}" />'
            )
        legend_parts.append(
            f'<g transform="translate({pad_l + idx * 170},{pad_t - 2})">'
            f'<rect width="10" height="10" fill="{color}" rx="2" />'
            f'<text x="14" y="9" fill="#9ca3af" font-size="11" font-family="system-ui">{html.escape(name)}</text>'
            f'</g>'
        )

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="max-width:100%;height:auto;background:#14141c;border:1px solid #1f2028;border-radius:8px;">'
        f'{"".join(grid_parts)}{"".join(x_labels)}{"".join(series_svg)}{"".join(legend_parts)}'
        f'</svg>'
    )


# ─── URL / link helpers ───────────────────────────────────────────────────────

def short_redirect_label(url: str) -> str:
    if not url:
        return ""
    if "cloudflareaccess.com/cdn-cgi/access/login" in url:
        return "CF Access login →"
    m = re.match(r"^(https?://[^/]+)(/[^?#]*)", url)
    if m:
        short = m.group(1) + m.group(2)
        if len(short) > 60:
            short = short[:57] + "…"
        return short
    return url[:60] + ("…" if len(url) > 60 else "")


def link(href: str, text: str, *, plain: bool = False, new_tab: bool = True, title: str = "") -> str:
    cls = ' class="plain"' if plain else ""
    tgt = ' target="_blank" rel="noopener"' if new_tab else ""
    ttl = f' title="{html.escape(title)}"' if title else ""
    return f'<a href="{html.escape(href)}"{cls}{tgt}{ttl}>{html.escape(text)}</a>'


# ─── CSS / JS ─────────────────────────────────────────────────────────────────

CSS = """
:root { --bg:#0a0a0f; --surface:#14141c; --border:#1f2028; --text:#e5e7eb; --muted:#9ca3af; --dim:#6b7280;
  --pass:#34d399; --fail:#f87171; --warn:#fbbf24; --accent:#a78bfa; --accent-hi:#c4b5fd; }
html { scroll-behavior: smooth; }
* { box-sizing: border-box; }
body { font-family: -apple-system, Segoe UI, system-ui, sans-serif; margin: 0; padding: 0 20px 20px;
  background: var(--bg); color: var(--text); line-height: 1.45; }
h1 { margin: 0 0 4px; font-size: 20px; letter-spacing: -0.01em; }
h2 { margin: 22px 0 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--muted); font-weight: 600; scroll-margin-top: 130px; }
h3 { margin: 0 0 6px; font-size: 13px; font-weight: 600; }
.subtitle { color: var(--dim); font-size: 12px; margin-bottom: 20px; }
a { color: var(--accent-hi); text-decoration: none; border-bottom: 1px dotted rgba(196,181,253,.3); }
a:hover { color: #ddd6fe; border-bottom-color: #ddd6fe; }
a.plain { border-bottom: none; }

/* Sticky topbar */
.topbar { position: sticky; top: 0; z-index: 50;
  background: linear-gradient(180deg, rgba(10,10,15,.98) 0%, rgba(10,10,15,.94) 75%, rgba(10,10,15,0) 100%);
  padding: 14px 0 10px; margin-bottom: 12px; }
.topbar-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.topbar-row .brand { font-weight: 700; font-size: 16px; letter-spacing: -0.01em; }
.topbar-row .brand .dim { font-weight: 400; color: var(--dim); font-size: 13px; margin-left: 6px; }

.nav { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; margin-top: 10px; }
.nav a { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 6px;
  background: var(--surface); color: var(--muted); font-size: 12px; font-weight: 600;
  border: 1px solid var(--border); }
.nav a:hover, .nav a.active { color: var(--text); border-color: #2a2a36; }
.nav a kbd { background: #0a0a10; border: 1px solid var(--border); border-radius: 3px;
  padding: 0 4px; font-size: 10px; color: var(--dim); }
.nav .spacer { flex: 1; }
.nav .hint { font-size: 11px; color: var(--dim); }

/* Cards + grid */
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }

/* Roster */
.roster { display: grid; gap: 12px; }
.app-row { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 16px; display: grid; grid-template-columns: auto 1fr auto auto; gap: 18px; align-items: center; }
@media (max-width: 900px) { .app-row { grid-template-columns: auto 1fr; } .app-row .cell-spark { grid-column: 1 / -1; } }
.app-row .donut-wrap { position: relative; width: 96px; height: 96px; flex-shrink: 0; }
.app-row .donut-center { position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; pointer-events: none; }
.app-row .donut-center .num { font-size: 20px; font-weight: 700; line-height: 1; }
.app-row .donut-center .den { font-size: 9px; color: var(--dim); letter-spacing: 0.08em;
  text-transform: uppercase; margin-top: 2px; }
.app-row .meta h3 { margin-bottom: 4px; font-size: 15px; }
.app-row .meta h3 a { color: var(--text); border-bottom: none; }
.app-row .meta h3 a:hover { color: var(--accent-hi); }
.app-row .meta .sub { color: var(--dim); font-size: 11px; }
.app-row .stats { font-size: 12px; text-align: right; min-width: 180px; }
.app-row .stats .line { color: var(--muted); margin-bottom: 2px; }
.app-row .stats strong { color: var(--text); }
.app-row .cell-spark { min-width: 140px; text-align: right; }
.app-row .cell-spark .label { font-size: 10px; color: var(--dim); letter-spacing: 0.05em; margin-bottom: 2px; }

/* Detail: overview donuts */
.overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
@media (max-width: 1100px) { .overview { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .overview { grid-template-columns: 1fr; } }
.donut-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px; display: flex; gap: 14px; align-items: center; }
.donut-card .donut-wrap { position: relative; width: 96px; height: 96px; flex-shrink: 0; }
.donut-card .donut-center { position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; pointer-events: none; }
.donut-card .donut-center .num { font-size: 20px; font-weight: 700; line-height: 1; }
.donut-card .donut-center .den { font-size: 9px; color: var(--dim); letter-spacing: 0.08em;
  text-transform: uppercase; margin-top: 2px; }
.donut-card .donut-meta { flex: 1; min-width: 0; }
.donut-card h3 { font-size: 11px; text-transform: uppercase; color: var(--dim);
  letter-spacing: 0.08em; font-weight: 600; margin: 0 0 8px; }
.legend { display: flex; flex-direction: column; gap: 3px; font-size: 11px; }
.legend .row { display: flex; justify-content: space-between; gap: 8px; }
.legend .k { color: var(--muted); }
.legend .v { color: var(--text); font-variant-numeric: tabular-nums; font-weight: 600; }
.legend .dot { display: inline-block; width: 8px; height: 8px; border-radius: 2px;
  margin-right: 6px; vertical-align: middle; }

/* Trend chart */
.trend-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px; margin-bottom: 16px; }
.trend-tabs { display: inline-flex; border: 1px solid var(--border); border-radius: 6px;
  overflow: hidden; margin-bottom: 10px; }
.trend-tabs button { background: transparent; color: var(--muted); border: none; padding: 5px 12px;
  font-size: 12px; cursor: pointer; font-family: inherit; font-weight: 600; }
.trend-tabs button.active { background: var(--border); color: var(--text); }
.trend-panel[hidden] { display: none; }
.trend-panel svg { display: block; width: 100%; }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 6px 8px; font-weight: 600; color: var(--muted);
  border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 8px; border-bottom: 1px solid #191922; vertical-align: top; }
tr:last-child td { border-bottom: none; }
.hidden { display: none !important; }
.pass { color: var(--pass); } .fail { color: var(--fail); } .warn { color: var(--warn); } .dim { color: var(--dim); }
.pill { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.pill.pass { background: rgba(52,211,153,.14); color: var(--pass); }
.pill.fail { background: rgba(248,113,113,.14); color: var(--fail); }
.pill.warn { background: rgba(251,191,36,.14); color: var(--warn); }
.pill.dim  { background: rgba(107,114,128,.14); color: var(--muted); }
.mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; }
.bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: var(--border); min-width: 80px; }
.bar .seg { height: 100%; }
.bar .seg.pass { background: var(--pass); }
.bar .seg.fail { background: var(--fail); }
.bar .seg.skip { background: var(--dim); }
.row-label { font-weight: 600; color: var(--text); }
.tier-badge { display: inline-block; padding: 1px 6px; border-radius: 4px; background: var(--border);
  font-size: 10px; font-weight: 700; margin-right: 6px; }
.tier-T0 { color: #60a5fa; } .tier-T2 { color: #fbbf24; } .tier-T3 { color: #a78bfa; }
.tier-T4 { color: #fb7185; } .tier-Brain { color: #34d399; }

/* Redirect link in endpoint cell */
.redir { display: inline-block; max-width: 320px; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; vertical-align: bottom; font-size: 11px; }

/* Toolbar */
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
.toolbar input[type="search"] { flex: 1; min-width: 180px; background: #0f0f16;
  border: 1px solid var(--border); color: var(--text); padding: 6px 10px; border-radius: 6px;
  font-size: 12px; font-family: inherit; }
.toolbar input[type="search"]:focus { outline: none; border-color: var(--accent); }
.toolbar label.toggle { display: inline-flex; align-items: center; gap: 6px; font-size: 11px;
  color: var(--muted); cursor: pointer; user-select: none; padding: 6px 10px;
  border: 1px solid var(--border); border-radius: 6px; }

/* Commands / copy */
.cmd { background: #0f0f16; border: 1px solid var(--border); padding: 4px 6px; border-radius: 4px;
  font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; color: var(--accent-hi);
  display: inline-block; max-width: 100%; overflow-x: auto; }
.cmd-wrap { display: inline-flex; align-items: center; gap: 4px; max-width: 100%; }
.copy-btn { background: var(--border); color: var(--muted); border: none; font-size: 10px;
  padding: 2px 6px; border-radius: 3px; cursor: pointer; font-family: inherit; }
.copy-btn:hover { background: #2a2a36; color: var(--text); }
.copy-btn.copied { background: rgba(52,211,153,.2); color: var(--pass); }

details summary { cursor: pointer; color: var(--muted); font-size: 11px; }
details[open] summary { color: var(--text); }
.body-head { background: #0a0a10; padding: 6px 8px; border-radius: 4px; max-height: 140px;
  overflow-y: auto; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 10px;
  color: var(--muted); white-space: pre-wrap; word-break: break-all; margin-top: 4px; }
footer { margin-top: 32px; color: var(--dim); font-size: 11px; text-align: center; }
.fresh { font-variant-numeric: tabular-nums; }

/* Story Flow lanes */
table.lanes th { border-right: 1px solid var(--border); }
table.lanes th.lane-col { text-align: center; padding: 8px 4px; color: var(--muted); }
table.lanes td { border-right: 1px solid #191922; }
table.lanes td.lane-cell { text-align: center; padding: 8px 4px; cursor: help; min-width: 54px; }
.lane-dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%;
  box-shadow: 0 0 0 2px var(--surface), 0 0 0 3px rgba(255,255,255,0.03); vertical-align: middle; }
.legend-chip { display: inline-flex; align-items: center; gap: 4px; margin-right: 10px; color: var(--muted); }
.legend-chip .dot { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
"""

JS = r"""
(function(){
  // Copy buttons
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.target);
      if (!target) return;
      const text = target.textContent.trim();
      const finish = () => {
        btn.classList.add('copied');
        const orig = btn.textContent;
        btn.textContent = 'OK';
        setTimeout(() => { btn.classList.remove('copied'); btn.textContent = orig; }, 900);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(finish, finish);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch(e) {}
        document.body.removeChild(ta); finish();
      }
    });
  });

  // Filter + failing-only
  function wireFilter(ctrlId, onlyId, tableSelector, dataAttr) {
    const ctrl = document.getElementById(ctrlId);
    const only = document.getElementById(onlyId);
    const tbody = document.querySelector(tableSelector);
    if (!ctrl || !tbody) return;
    function apply() {
      const q = ctrl.value.trim().toLowerCase();
      const failingOnly = only && only.checked;
      tbody.querySelectorAll('tr').forEach(tr => {
        const txt = tr.textContent.toLowerCase();
        const state = tr.getAttribute(dataAttr) || '';
        const matchQ = !q || txt.includes(q);
        const matchOnly = !failingOnly || state === 'fail';
        tr.classList.toggle('hidden', !(matchQ && matchOnly));
      });
    }
    ctrl.addEventListener('input', apply);
    if (only) only.addEventListener('change', apply);
  }
  wireFilter('filter-pages', 'only-failing-pages', '#pages-tbody', 'data-state');
  wireFilter('filter-tests', 'only-failing-tests', '#tests-tbody', 'data-state');
  wireFilter('filter-apps', 'only-failing-apps', '#apps-tbody', 'data-state');

  // Keyboard nav: 1..9 jumps to nav item
  document.addEventListener('keydown', e => {
    if (e.target.matches('input,textarea,select')) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const n = parseInt(e.key, 10);
    if (!n) return;
    const targets = document.querySelectorAll('[data-jump]');
    const t = targets[n - 1];
    if (t) {
      e.preventDefault();
      const sel = t.getAttribute('data-jump');
      const el = document.querySelector(sel);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  // Trend tabs
  document.querySelectorAll('.trend-tabs').forEach(tabs => {
    const group = tabs.getAttribute('data-group');
    const buttons = tabs.querySelectorAll('button');
    buttons.forEach(btn => btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.toggle('active', b === btn));
      const key = btn.dataset.panel;
      document.querySelectorAll(`[data-group="${group}"][data-panel]`).forEach(p => {
        p.hidden = (p.dataset.panel !== key);
      });
    }));
  });

  // Live "freshness" indicator
  const probedAt = document.body.dataset.probedAt;
  if (probedAt) {
    const t0 = Date.parse(probedAt);
    const elems = document.querySelectorAll('[data-fresh]');
    function tick() {
      const secs = Math.max(0, Math.floor((Date.now() - t0) / 1000));
      const label = secs < 5 ? 'just now'
        : secs < 60 ? `${secs}s ago`
        : secs < 3600 ? `${Math.floor(secs/60)}m ago`
        : secs < 86400 ? `${Math.floor(secs/3600)}h ago`
        : `${Math.floor(secs/86400)}d ago`;
      elems.forEach(e => { e.textContent = label; });
    }
    tick();
    setInterval(tick, 1000);
  }
})();
"""


# ─── Renderers ─────────────────────────────────────────────────────────────────

def donut_card_html(title: str, center_num: str, center_label: str,
                    segments: list[tuple[str, float, str]],
                    center_class: str = "") -> str:
    size = 96
    svg = donut_svg(segments, size=size)
    legend_rows = "".join(
        f'<div class="row"><span class="k"><span class="dot" style="background:{color}"></span>{html.escape(label)}</span>'
        f'<span class="v">{value}</span></div>'
        for label, value, color in segments
    )
    return (
        f'<div class="donut-card">'
        f'<div class="donut-wrap">{svg}'
        f'<div class="donut-center"><div class="num {center_class}">{html.escape(center_num)}</div>'
        f'<div class="den">{html.escape(center_label)}</div></div>'
        f'</div>'
        f'<div class="donut-meta"><h3>{html.escape(title)}</h3>'
        f'<div class="legend">{legend_rows}</div></div>'
        f'</div>'
    )


def detail_filename(app_key: str) -> str:
    return f"app-{app_key}.html"


def nav_html(sections: list[tuple[str, str, str | None]], active_id: str | None = None) -> str:
    """sections: list of (anchor, label, pill_html)"""
    links = []
    for idx, (anchor, label, pill) in enumerate(sections, start=1):
        active = " active" if active_id == anchor.lstrip("#") else ""
        pill_html = f' {pill}' if pill else ""
        links.append(
            f'<a href="{html.escape(anchor)}" class="{active.strip()}" data-jump="{html.escape(anchor)}">'
            f'<kbd>{idx}</kbd> {html.escape(label)}{pill_html}</a>'
        )
    return (
        f'<nav class="nav" aria-label="Sections">{"".join(links)}'
        f'<span class="spacer"></span><span class="hint">press <kbd>1</kbd>–<kbd>{len(sections)}</kbd> to jump</span>'
        f'</nav>'
    )


# ─── Story lanes (Brain → downstream-app fan-out) ─────────────────────────────

STORY_STATUS_META = {
    "pass":    {"color": "#34d399", "label": "Pass",    "cls": "pass"},
    "fail":    {"color": "#f87171", "label": "Fail",    "cls": "fail"},
    "running": {"color": "#60a5fa", "label": "Running", "cls": "warn"},
    "pending": {"color": "#a78bfa", "label": "Pending", "cls": "dim"},
    "skipped": {"color": "#fbbf24", "label": "Skipped", "cls": "warn"},
    "na":      {"color": "#1f2028", "label": "Not affected", "cls": "dim"},
}


def load_stories() -> dict:
    if STORIES_FILE.exists():
        try:
            return json.loads(STORIES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "source": "none", "stories": []}


def render_lanes(stories_doc: dict) -> str:
    """Render the Story-Flow lane view: one row per in-flight Linear story, one column per lane."""
    e = html.escape
    stories = stories_doc.get("stories", []) or []
    source = stories_doc.get("source", "none")

    # Column header
    header_cells = "".join(
        f'<th class="lane-col" data-lane="{e(key)}" title="{e(full)}">'
        f'<span class="mono" style="font-size:11px;">{e(abbr)}</span>'
        f'</th>'
        for key, abbr, full in LANES
    )

    legend_html = " ".join(
        f'<span class="legend-chip"><span class="dot" style="background:{m["color"]}"></span>{e(m["label"])}</span>'
        for k, m in STORY_STATUS_META.items()
    )

    if not stories:
        example_path = STORIES_FILE.with_suffix(".json.example")
        example_link = link(f"file:///{example_path.as_posix()}", ".stories.json.example", plain=True)
        empty_state = f"""
          <div class="card" style="text-align:center;padding:28px;">
            <div style="font-size:13px;color:var(--muted);margin-bottom:8px;">No in-flight stories</div>
            <div class="dim" style="font-size:12px;max-width:640px;margin:0 auto;">
              Drop a <span class="mono">.stories.json</span> in the dashboard folder and re-run, or wire up the Linear API.
              See {example_link} for the expected schema — each story groups by an <span class="mono">umbrella</span> label
              (so issues in different app backlogs with different numbers roll up to one row).
            </div>
          </div>
        """
        return f"""
        <section id="stories">
          <h2>Story Flow — Brain → downstream apps</h2>
          <div class="dim" style="font-size:11px;margin:-4px 0 10px;">Source: <span class="mono">{e(source)}</span> · {legend_html}</div>
          {empty_state}
        </section>
        """

    rows = []
    for story in stories:
        umbrella = story.get("umbrella", "")
        title = story.get("title", "(no title)")
        linear_url = story.get("linear_url")
        created = (story.get("created_at") or "")[:10]
        title_html = link(linear_url, title, plain=False) if linear_url else e(title)

        # Count statuses to pick a row-level badge
        statuses = [(story.get("apps") or {}).get(lane_key, {}).get("status", "na") for lane_key, *_ in LANES]
        any_fail = any(s == "fail" for s in statuses)
        any_running = any(s == "running" for s in statuses)
        all_done = all(s in ("pass", "na", "skipped") for s in statuses)
        row_state = "fail" if any_fail else ("running" if any_running else ("pass" if all_done else "pending"))
        row_pill_cls = {"fail": "fail", "running": "warn", "pass": "pass", "pending": "dim"}[row_state]

        cells = []
        for lane_key, abbr, full in LANES:
            app_data = (story.get("apps") or {}).get(lane_key, {}) or {}
            status = app_data.get("status", "na")
            meta = STORY_STATUS_META.get(status, STORY_STATUS_META["na"])
            note = app_data.get("note") or meta["label"]
            pr = app_data.get("pr_url")
            ci = app_data.get("ci_url")

            dot = f'<span class="lane-dot" style="background:{meta["color"]};" title="{e(abbr)}: {e(note)}"></span>'
            extras = []
            if pr:
                extras.append(link(pr, "PR", plain=True))
            if ci:
                extras.append(link(ci, "CI", plain=True))
            extras_html = f' <span class="dim" style="font-size:10px;">{" · ".join(extras)}</span>' if extras else ""

            cell_title = f"{abbr}: {note}" + (f" ({status})" if status not in ("na",) else "")
            cells.append(
                f'<td class="lane-cell" title="{e(cell_title)}" data-status="{e(status)}">'
                f'{dot}{extras_html}'
                f'</td>'
            )

        umbrella_html = (
            f'<div class="dim mono" style="font-size:10px;margin-top:2px;">'
            f'{e(umbrella)}</div>'
        ) if umbrella else ""

        rows.append(f"""
          <tr data-state="{e(row_state)}">
            <td>
              <div class="row-label">{title_html}</div>
              {umbrella_html}
              <div class="dim" style="font-size:10px;">{e(created)}</div>
            </td>
            <td><span class="pill {row_pill_cls}">{e(row_state.upper())}</span></td>
            {''.join(cells)}
          </tr>
        """)

    return f"""
    <section id="stories">
      <h2>Story Flow — Brain → downstream apps</h2>
      <div class="dim" style="font-size:11px;margin:-4px 0 10px;">
        Source: <span class="mono">{e(source)}</span> · {len(stories)} in flight · {legend_html}
      </div>
      <div class="card" style="padding:8px;overflow-x:auto;">
        <table class="lanes">
          <thead>
            <tr>
              <th style="min-width:280px;">Story</th>
              <th style="min-width:90px;">Overall</th>
              {header_cells}
            </tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>
    """


def render_index(all_features: list[dict], per_app: dict[str, dict], history: dict,
                 probed_at: str, args_note: str, stories_doc: dict) -> str:
    """Top-level roster page."""
    e = html.escape

    # Global totals (across all apps, suites only)
    g_pass = sum(p["tests"]["pass"] for p in per_app.values())
    g_fail = sum(p["tests"]["fail"] for p in per_app.values())
    g_skip = sum(p["tests"]["skip"] for p in per_app.values())
    g_total = g_pass + g_fail + g_skip
    g_pct = (100.0 * g_pass / g_total) if g_total else None

    g_suite_pass = sum(p["suites"]["pass"] for p in per_app.values())
    g_suite_fail = sum(p["suites"]["fail"] for p in per_app.values())
    g_suite_never = sum(p["suites"]["never"] for p in per_app.values())
    g_suite_total = g_suite_pass + g_suite_fail + g_suite_never

    g_pages_pass = sum(p["pages"]["pass"] for p in per_app.values() if p.get("pages"))
    g_pages_total = sum(p["pages"]["total"] for p in per_app.values() if p.get("pages"))

    # Donuts at top
    tests_donut = donut_card_html(
        "Tests across all apps",
        f"{g_pct:.0f}%" if g_pct is not None else "—",
        f"of {g_total} tests" if g_total else "no runs yet",
        [("Pass", g_pass, "#34d399"), ("Fail", g_fail, "#f87171"), ("Skip", g_skip, "#6b7280")],
        center_class=("pass" if g_fail == 0 and g_pass > 0 else "fail" if g_fail else "dim"),
    )
    suites_donut = donut_card_html(
        "Suites",
        f"{g_suite_pass}/{g_suite_total}" if g_suite_total else "0",
        "passing",
        [("Pass", g_suite_pass, "#34d399"), ("Fail", g_suite_fail, "#f87171"),
         ("Never run", g_suite_never, "#6b7280")],
        center_class=("pass" if g_suite_fail == 0 and g_suite_pass > 0 else "fail" if g_suite_fail else "dim"),
    )
    pages_donut = donut_card_html(
        "Pages live",
        f"{g_pages_pass}/{g_pages_total}" if g_pages_total else "—",
        "green",
        [("Pass", g_pages_pass, "#34d399"),
         ("Fail", g_pages_total - g_pages_pass, "#f87171")],
        center_class=("pass" if g_pages_total and g_pages_pass == g_pages_total else "fail" if g_pages_total else "dim"),
    )
    apps_pass = sum(1 for p in per_app.values() if p["verdict"] == "pass")
    apps_fail = sum(1 for p in per_app.values() if p["verdict"] == "fail")
    apps_never = sum(1 for p in per_app.values() if p["verdict"] == "never")
    apps_donut = donut_card_html(
        "Apps",
        f"{apps_pass}/{len(APPS)}",
        "green",
        [("Pass", apps_pass, "#34d399"), ("Fail", apps_fail, "#f87171"),
         ("Never run", apps_never, "#6b7280")],
        center_class=("pass" if apps_fail == 0 and apps_pass > 0 else "fail" if apps_fail else "dim"),
    )
    overview_html = f'<div class="overview">{tests_donut}{suites_donut}{pages_donut}{apps_donut}</div>'

    # Trend chart: one line per app, three tabs (day/week/month)
    colors_by_app = {"ocr-brain": "#34d399", "ose-staging": "#60a5fa", "ose-prod": "#fb7185"}
    def chart_for(bucket: str, n: int) -> str:
        series = [
            (a["name"], colors_by_app.get(a["key"], "#a78bfa"),
             history_points_by_bucket(history, a["key"], bucket, n))
            for a in APPS
        ]
        return trend_chart_svg(series, width=820, height=190)

    trend_html = f"""
    <section id="trend" class="trend-card">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;">
        <h3 style="margin:0;font-size:12px;text-transform:uppercase;color:var(--muted);letter-spacing:0.08em;">
          Pass-rate trend (per app)
        </h3>
        <div class="trend-tabs" data-group="trend">
          <button class="active" data-panel="day">30 days</button>
          <button data-panel="week">12 weeks</button>
          <button data-panel="month">12 months</button>
        </div>
      </div>
      <div data-group="trend" data-panel="day" class="trend-panel">{chart_for("day", 30)}</div>
      <div data-group="trend" data-panel="week" class="trend-panel" hidden>{chart_for("week", 12)}</div>
      <div data-group="trend" data-panel="month" class="trend-panel" hidden>{chart_for("month", 12)}</div>
    </section>
    """

    # Roster — one row per app, linked to detail page
    rows: list[str] = []
    for app in APPS:
        s = per_app.get(app["key"])
        if not s:
            continue
        verdict = s["verdict"]
        verdict_cls = {"pass": "pass", "fail": "fail"}.get(verdict, "dim")
        pct = s["tests"]["pct"]
        pct_str = f"{pct:.0f}%" if pct is not None else "—"
        center_num = pct_str
        center_lbl = f"{s['tests']['pass']}/{s['tests']['total']}" if s["tests"]["total"] else "no runs"
        segments = [
            ("Pass", s["tests"]["pass"], "#34d399"),
            ("Fail", s["tests"]["fail"], "#f87171"),
            ("Skip", s["tests"]["skip"], "#6b7280"),
        ]
        donut = donut_svg(segments, size=96)

        pages_line = ""
        if s.get("pages"):
            pg = s["pages"]
            cls = "pass" if pg["total"] and pg["pass"] == pg["total"] else "warn"
            pages_line = f'<div class="line">Pages: <strong class="{cls}">{pg["pass"]}/{pg["total"]}</strong> green</div>'

        suite_pill_cls = "pass" if s["suites"]["fail"] == 0 and s["suites"]["pass"] > 0 else ("fail" if s["suites"]["fail"] else "dim")
        never_frag = f' · <span class="dim">{s["suites"]["never"]} never</span>' if s["suites"]["never"] else ""
        suites_line = (
            f'<div class="line">Suites: '
            f'<strong class="{suite_pill_cls}">{s["suites"]["pass"]}✓ / {s["suites"]["fail"]}✗</strong>'
            f'{never_frag}'
            f'</div>'
        )
        tests_line = (
            f'<div class="line">Tests: <strong class="pass">{s["tests"]["pass"]}</strong> / '
            f'<strong class="fail">{s["tests"]["fail"]}</strong> of '
            f'<strong>{s["tests"]["total"]}</strong></div>'
            if s["tests"]["total"] else
            '<div class="line dim">No runs yet</div>'
        )
        last_line = (
            f'<div class="line dim">Last run: <span class="mono">{e(s["last_run"])}</span></div>'
            if s.get("last_run") else '<div class="line dim">Last run: —</div>'
        )

        # 30-day sparkline using forward-fill
        sp_pairs = history_points_by_bucket(history, app["key"], "day", 30)
        sp_vals = [v for _, v in sp_pairs]
        sp = sparkline_svg(sp_vals, width=150, height=32)

        detail_url = detail_filename(app["key"])
        rows.append(f"""
          <div class="app-row" data-state="{e(verdict)}">
            <div class="donut-wrap">{donut}
              <div class="donut-center">
                <div class="num {verdict_cls}">{e(center_num)}</div>
                <div class="den">{e(center_lbl)}</div>
              </div>
            </div>
            <div class="meta">
              <h3><a href="{e(detail_url)}" class="plain">{e(app["name"])} →</a></h3>
              <div class="sub">{e(app["subtitle"])}</div>
              <div style="margin-top:6px;"><span class="pill {verdict_cls}">{e(verdict.upper())}</span></div>
            </div>
            <div class="stats">
              {suites_line}
              {tests_line}
              {pages_line}
              {last_line}
            </div>
            <div class="cell-spark">
              <div class="label">30-day pass%</div>
              {sp}
            </div>
          </div>
        """)

    roster_html = f"""
    <section id="apps">
      <h2>Apps</h2>
      <div class="toolbar">
        <input type="search" id="filter-apps" placeholder="Filter apps…" autocomplete="off">
        <label class="toggle"><input type="checkbox" id="only-failing-apps"> Only failing</label>
        <span class="dim" style="font-size:11px;">{apps_pass}/{len(APPS)} green · click an app to drill in</span>
      </div>
      <div id="apps-tbody" class="roster">{''.join(rows)}</div>
    </section>
    """

    lanes_html = render_lanes(stories_doc)
    stories_count = len(stories_doc.get("stories") or [])
    stories_pill = f'<span class="pill dim" style="margin-left:4px;">{stories_count}</span>'

    # Navigation
    nav_sections = [
        ("#overview", "Overview", None),
        ("#trend", "Trend", None),
        ("#stories", "Stories", stories_pill),
        ("#apps", "Apps", f'<span class="pill {"pass" if apps_fail==0 else "fail"}" style="margin-left:4px;">{apps_pass}/{len(APPS)}</span>'),
    ]

    top = f"""
    <div class="topbar">
      <div class="topbar-row">
        <div class="brand">OCR — Multi-App Dashboard
          <span class="dim">probed <span class="fresh" data-fresh>just now</span></span>
        </div>
      </div>
      {nav_html(nav_sections, active_id="apps")}
    </div>
    """

    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>OCR — Multi-App Dashboard · {e(probed_at)}</title>
<style>{CSS}</style>
</head><body data-probed-at="{e(probed_at)}">
{top}
<section id="overview"><h2>Overview</h2>{overview_html}</section>
{trend_html}
{lanes_html}
{roster_html}
<footer>
  ocr-dashboard v2 · click an app to drill into its live probes + test pyramid + drift<br>
  State: <span class="mono">OCR-docs/dashboard/.state.json</span> · History: <span class="mono">OCR-docs/dashboard/.history.json</span><br>
  Regenerate: <span class="cmd" id="cmd-regen">py C:\\Users\\mzdan\\dev\\ourCommunityRituals\\OCR-docs\\dashboard\\dashboard.py</span>
  <button class="copy-btn" data-target="cmd-regen">copy</button>
  {args_note}
</footer>
<script>{JS}</script>
</body></html>
"""
    return doc


def render_app_detail(app: dict, features_for_this_app: list[dict],
                     probes: list[dict] | None, deploy: dict | None,
                     history: dict, probed_at: str, args_note: str) -> str:
    """Per-app detail page with live probes, test pyramid, drift — URLs clickable."""
    e = html.escape

    # Summary stats for this app
    summary = summarize_app(app, features_for_this_app, probes)

    # Overview donuts
    donuts: list[str] = []

    # Always show: health (if probes), pages (if probes), suites, tests
    if probes is not None and deploy is not None:
        health = deploy.get("health", {})
        health_cls, health_txt = status_class({
            "status": health.get("status"), "bytes": health.get("bytes", 0),
            "ms": health.get("ms", 0), "error": health.get("error"), "expected": 200,
        })
        dep = deploy.get("deployed") or {}
        donuts.append(donut_card_html(
            "Health",
            "OK" if health_cls == "pass" else "DOWN",
            e(dep.get("version") or "unknown")[:20],
            [("Healthy", 1 if health_cls == "pass" else 0, "#34d399"),
             ("Down", 0 if health_cls == "pass" else 1, "#f87171")],
            center_class=health_cls,
        ))
        pp = summary["pages"] or {"pass": 0, "total": 0}
        pages_cls = "pass" if pp["total"] and pp["pass"] == pp["total"] else "warn"
        donuts.append(donut_card_html(
            "Pages live",
            f"{pp['pass']}/{pp['total']}" if pp["total"] else "—",
            "green",
            [("Pass", pp["pass"], "#34d399"),
             ("Fail", pp["total"] - pp["pass"], "#f87171")],
            center_class=pages_cls,
        ))

    s = summary["suites"]
    suite_cls = "pass" if s["fail"] == 0 and s["pass"] > 0 else ("fail" if s["fail"] else "dim")
    donuts.append(donut_card_html(
        "Test suites",
        f"{s['pass']}/{s['total']}" if s["total"] else "0",
        "passing",
        [("Pass", s["pass"], "#34d399"), ("Fail", s["fail"], "#f87171"),
         ("Never run", s["never"], "#6b7280")],
        center_class=suite_cls,
    ))
    t = summary["tests"]
    tests_pct = t["pct"]
    tests_cls = "pass" if t["fail"] == 0 and t["pass"] > 0 else ("fail" if t["fail"] else "dim")
    donuts.append(donut_card_html(
        "Tests",
        f"{tests_pct:.0f}%" if tests_pct is not None else "—",
        f"of {t['total']} tests" if t["total"] else "no runs",
        [("Pass", t["pass"], "#34d399"), ("Fail", t["fail"], "#f87171"), ("Skip", t["skip"], "#6b7280")],
        center_class=tests_cls,
    ))
    if deploy is not None and app["drift"]:
        dw = deploy.get("drift_worker", 0)
        dc = deploy.get("drift_ci", 0)
        total_drift = dw + dc
        drift_cls = "warn" if dw else ("pass" if total_drift == 0 else "dim")
        donuts.append(donut_card_html(
            "Drift → origin/main",
            str(total_drift),
            "commits",
            [("Worker", dw, "#fbbf24"), ("CI / tests / docs", dc, "#6b7280")],
            center_class=drift_cls,
        ))

    overview_html = f'<div class="overview">{"".join(donuts)}</div>'

    # Trend for this app only
    def chart_for(bucket: str, n: int) -> str:
        color = {"ocr-brain": "#34d399", "ose-staging": "#60a5fa", "ose-prod": "#fb7185"}.get(app["key"], "#a78bfa")
        series = [(app["name"], color, history_points_by_bucket(history, app["key"], bucket, n))]
        return trend_chart_svg(series, width=820, height=180)

    trend_html = f"""
    <section id="trend" class="trend-card">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;">
        <h3 style="margin:0;font-size:12px;text-transform:uppercase;color:var(--muted);letter-spacing:0.08em;">
          Pass-rate trend
        </h3>
        <div class="trend-tabs" data-group="trend">
          <button class="active" data-panel="day">30 days</button>
          <button data-panel="week">12 weeks</button>
          <button data-panel="month">12 months</button>
        </div>
      </div>
      <div data-group="trend" data-panel="day" class="trend-panel">{chart_for("day", 30)}</div>
      <div data-group="trend" data-panel="week" class="trend-panel" hidden>{chart_for("week", 12)}</div>
      <div data-group="trend" data-panel="month" class="trend-panel" hidden>{chart_for("month", 12)}</div>
    </section>
    """

    # Endpoint table (only if probes)
    endpoints_html = ""
    if probes is not None:
        rows_ep: list[str] = []
        for p in probes:
            cls, txt = status_class(p)
            path = p["path"]
            url = (app["base"] or "") + path
            aliases_html = ""
            if p["aliases"]:
                alias_links = " · ".join(
                    link((app["base"] or "") + a, a, plain=True)
                    for a in p["aliases"][:8]
                )
                aliases_html = f"<div class='dim mono' style='font-size:10px;margin-top:2px;'>aliases: {alias_links}</div>"

            redir_html = ""
            redirect = p.get("redirect")
            if redirect and p.get("status") and 300 <= p["status"] < 400:
                short = short_redirect_label(redirect)
                redir_html = (
                    f" <span class='dim'>→</span> "
                    f'<a href="{e(redirect)}" target="_blank" rel="noopener" class="redir plain" title="{e(redirect)}">{e(short)}</a>'
                )

            rows_ep.append(f"""
              <tr data-state="{cls}">
                <td>
                  <a href="{e(url)}" target="_blank" rel="noopener" class="row-label plain">{e(p['label'])}</a>
                  <div>{link(url, path, plain=True)}</div>
                  {aliases_html}
                </td>
                <td><span class="pill {cls}">{e(txt)}</span>{redir_html}</td>
              </tr>
            """)

        endpoints_html = f"""
          <section id="pages">
            <h2>Pages — live probes against {link(app["base"], app["base"].replace("https://",""), plain=True)}</h2>
            <div class="card">
              <div class="toolbar">
                <input type="search" id="filter-pages" placeholder="Filter pages…" autocomplete="off">
                <label class="toggle"><input type="checkbox" id="only-failing-pages"> Only failing</label>
                <span class="dim" style="font-size:11px;">{summary["pages"]["pass"]}/{summary["pages"]["total"]} green</span>
              </div>
              <table>
                <thead><tr><th>Page</th><th>Live status</th></tr></thead>
                <tbody id="pages-tbody">{''.join(rows_ep)}</tbody>
              </table>
            </div>
          </section>
        """

    # Test feature table
    tests_html = ""
    if features_for_this_app:
        rows_feat: list[str] = []
        for idx, f in enumerate(features_for_this_app):
            p, fa, sk, tot = f.get("pass"), f.get("fail"), f.get("skip"), f.get("total")
            if f.get("result") == "pass":
                status_cell, state = '<span class="pill pass">PASS</span>', "pass"
            elif f.get("result") == "fail":
                status_cell, state = '<span class="pill fail">FAIL</span>', "fail"
            else:
                status_cell, state = '<span class="pill dim">NEVER RUN</span>', "never"

            if tot and tot > 0:
                pass_pct = (p or 0) / tot * 100
                fail_pct = (fa or 0) / tot * 100
                skip_pct = (sk or 0) / tot * 100
                detail = f.get("detail") or ""
                detail_html = f'<div class="dim" style="font-size:10px;margin-top:2px;">{e(detail)}</div>' if detail else ""
                bar = f"""
                  <div class="bar">
                    <div class="seg pass" style="width:{pass_pct:.1f}%"></div>
                    <div class="seg fail" style="width:{fail_pct:.1f}%"></div>
                    <div class="seg skip" style="width:{skip_pct:.1f}%"></div>
                  </div>
                  <div class="dim mono" style="font-size:10px;margin-top:3px;">{p or 0}✓ / {fa or 0}✗ / {sk or 0}⊘ of {tot}</div>
                  {detail_html}
                """
            else:
                bar = f'<span class="dim mono">{f["files"]} files · ~{f["test_calls"]} calls</span>'
                if f["key"].startswith("t3-newman") and f.get("requests"):
                    bar = f'<span class="dim mono">{f["requests"]} requests</span>'

            last_run_cell = (
                f'<span class="mono dim">{e(f["last_run"] or "—")}</span>'
                + (f'<br><span class="dim" style="font-size:10px;">rc: {f.get("rc",0)} · {f.get("elapsed_s",0)}s</span>'
                    if f.get("last_run") else "")
            )

            cmd_id = f"cmd-{app['key']}-{idx}"
            refresh_cmd = f"py C:\\Users\\mzdan\\dev\\ourCommunityRituals\\OCR-docs\\dashboard\\dashboard.py --run-tests {f['key']}"
            cmd_html = (
                f'<div class="cmd-wrap"><span class="cmd" id="{cmd_id}">{e(f["run_cmd"])}</span>'
                f'<button class="copy-btn" data-target="{cmd_id}" title="Copy">copy</button></div>'
                f'<div class="dim mono" style="font-size:10px;margin-top:4px;">refresh: </div>'
                f'<div class="cmd-wrap"><span class="cmd" id="{cmd_id}-r">{e(refresh_cmd)}</span>'
                f'<button class="copy-btn" data-target="{cmd_id}-r" title="Copy">copy</button></div>'
            )

            rows_feat.append(f"""
              <tr data-state="{state}">
                <td>
                  <span class="tier-badge tier-{f['tier']}">{f['tier']}</span>
                  <span class="row-label">{e(f['name'])}</span>
                  <div class="dim mono" style="font-size:10px;margin-top:3px;">{e(f['dir'])}</div>
                </td>
                <td>{bar}</td>
                <td>{status_cell}<br>{last_run_cell}</td>
                <td>{cmd_html}</td>
              </tr>
            """)

        sm_s = summary["suites"]
        sm_t = summary["tests"]
        tests_html = f"""
          <section id="tests">
            <h2>Test pyramid ({len(features_for_this_app)} suite{'s' if len(features_for_this_app) != 1 else ''})</h2>
            <div class="card">
              <div class="toolbar">
                <input type="search" id="filter-tests" placeholder="Filter tests…" autocomplete="off">
                <label class="toggle"><input type="checkbox" id="only-failing-tests"> Only failing</label>
                <span class="dim" style="font-size:11px;">
                  {sm_s["pass"]}/{sm_s["total"]} suites passing · {sm_t["pass"]}✓ / {sm_t["fail"]}✗ of {sm_t["total"]} tests
                </span>
              </div>
              <table>
                <thead><tr><th>Feature</th><th>Pass / Fail / Skip</th><th>Status &amp; last run</th><th>Commands</th></tr></thead>
                <tbody id="tests-tbody">{''.join(rows_feat)}</tbody>
              </table>
            </div>
          </section>
        """

    # Drift
    drift_html = ""
    if deploy is not None and app["drift"]:
        dep = deploy.get("deployed") or {}
        om = deploy.get("origin_main") or {}
        drift_rows: list[str] = []
        for c in deploy.get("commits_since_deploy", [])[:40]:
            tag_cls = "warn" if c["tag"] == "worker" else "dim"
            commit_url = f"{app['github']}/commit/{c['sha']}"
            drift_rows.append(f"""
              <tr>
                <td class="mono">{link(commit_url, c['sha'])}</td>
                <td><span class="pill {tag_cls}">{e(c['tag'])}</span></td>
                <td>{e(c['msg'][:110])}</td>
              </tr>
            """)
        dep_short = (dep.get('commit') or '?')[:7]
        origin_short = om.get('short', '?')
        compare_html = ""
        if dep.get('commit') and om.get('sha'):
            compare_url = f"{app['github']}/compare/{dep['commit']}...{om['sha']}"
            compare_html = f' · {link(compare_url, "compare on GitHub")}'
        body_empty = '<tr><td colspan="3" class="dim">No commits — deployment is at origin/main.</td></tr>'
        drift_note = ("⚠️ Worker code changed since last deploy — runtime may be behind."
                      if deploy.get("drift_worker") else
                      "✓ No worker code has changed since last deploy. Runtime is functionally current.")
        drift_html = f"""
          <section id="drift">
            <h2>Drift — commits since deployed ({e(dep_short)} → {e(origin_short)}){compare_html}</h2>
            <div class="card">
              <table>
                <thead><tr><th>SHA</th><th>Tag</th><th>Message</th></tr></thead>
                <tbody>{''.join(drift_rows) if drift_rows else body_empty}</tbody>
              </table>
              <div class="dim" style="margin-top:10px;font-size:11px;">{drift_note}</div>
            </div>
          </section>
        """

    # /health body preview
    health_preview = ""
    if deploy is not None:
        hb = (deploy.get("health", {}).get("body_head") or "")[:400]
        if hb:
            health_preview = (
                f'<details><summary>Show /health response body</summary>'
                f'<div class="body-head">{e(hb)}</div></details>'
            )

    # Navigation
    nav_sections: list[tuple[str, str, str | None]] = [("#overview", "Overview", None),
                                                        ("#trend", "Trend", None)]
    if endpoints_html:
        pg = summary["pages"]
        pages_pill = f'<span class="pill {"pass" if pg and pg["total"] and pg["pass"] == pg["total"] else "warn"}" style="margin-left:4px;">{pg["pass"]}/{pg["total"]}</span>' if pg else ""
        nav_sections.append(("#pages", "Pages", pages_pill))
    if tests_html:
        sm = summary["suites"]
        tests_pill = f'<span class="pill {"pass" if sm["fail"]==0 and sm["pass"]>0 else "fail" if sm["fail"] else "dim"}" style="margin-left:4px;">{sm["pass"]}✓ / {sm["fail"]}✗</span>'
        nav_sections.append(("#tests", "Tests", tests_pill))
    if drift_html:
        dw = deploy.get("drift_worker", 0) if deploy else 0
        dc = deploy.get("drift_ci", 0) if deploy else 0
        tot = dw + dc
        drift_pill = f'<span class="pill {"warn" if dw else "pass" if tot == 0 else "dim"}" style="margin-left:4px;">{tot}</span>'
        nav_sections.append(("#drift", "Drift", drift_pill))

    top = f"""
    <div class="topbar">
      <div class="topbar-row">
        <div class="brand">
          <a href="index.html" class="plain" style="color:var(--muted);">← All apps</a>
          &nbsp;·&nbsp;{e(app["name"])}
          <span class="dim">probed <span class="fresh" data-fresh>just now</span></span>
        </div>
      </div>
      {nav_html(nav_sections)}
    </div>
    """

    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{e(app["name"])} · {e(probed_at)}</title>
<style>{CSS}</style>
</head><body data-probed-at="{e(probed_at)}">
{top}
<section id="overview"><h2>Overview — {e(app["name"])}</h2>
  <div class="subtitle">{e(app["subtitle"])} · {link(app["github"], "GitHub")}
    {f' · {link(app["base"], app["base"].replace("https://",""))}' if app.get("base") else ""}
    {args_note}
  </div>
  {overview_html}
  {health_preview}
</section>
{trend_html}
{endpoints_html}
{tests_html}
{drift_html}
<footer>
  ocr-dashboard v2 · <a href="index.html">← back to all apps</a> · self-contained · no CDN<br>
  State: <span class="mono">.state.json</span> · History: <span class="mono">.history.json</span>
</footer>
<script>{JS}</script>
</body></html>
"""
    return doc


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--run-tests", help="Suite key to run (e.g. t0-unit, brain) or 'all'")
    ap.add_argument("--app", help="Regenerate only one app's detail page (ocr-brain, ose-staging, ose-prod)")
    ap.add_argument("--open", action="store_true", help="Open index.html in default browser when done")
    args = ap.parse_args()

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    # If --run-tests: run first, then regenerate everything
    history = load_history()
    state = load_state()
    note = ""

    if args.run_tests:
        all_feats = inventory_features()
        targets = [f for f in all_feats if args.run_tests == "all" or f["key"] == args.run_tests]
        if not targets:
            print(f"Unknown suite key: {args.run_tests}. Available: {[f['key'] for f in all_feats]}")
            return 2
        for feat in targets:
            print(f"[{now_iso()}] Running {feat['key']} — {feat['name']} …")
            result = run_feature(feat)
            state.setdefault("suites", {})[feat["key"]] = result
            append_snapshot(history, feat["key"], result)
            print(f"  → {result['result'].upper()}  pass={result['pass']} fail={result['fail']} "
                  f"skip={result['skip']} total={result['total']} rc={result['rc']} "
                  f"in {result['elapsed_s']}s")
        save_state(state)
        save_history(history)
        note = f' · <span class="pass">Ran {len(targets)} suite(s) just now.</span>'

    # Refresh feature inventory after any runs
    all_feats = inventory_features()

    # Probe + deploy state for each app in parallel-ish (sequential is fine; probes are already parallel inside)
    probed_at = now_iso()
    per_app_probes: dict[str, list[dict]] = {}
    per_app_deploy: dict[str, dict] = {}
    for app in APPS:
        if app["probes"]:
            print(f"[{now_iso()}] Probing {app['base']} …")
            probes = probe_all_endpoints(app["base"])
            per_app_probes[app["key"]] = probes
            if app["drift"]:
                print(f"[{now_iso()}] Reading git + deployment state for {app['key']} …")
                per_app_deploy[app["key"]] = deployment_state(app["base"], app["repo"])

    # Summaries for roster
    per_app_summary: dict[str, dict] = {
        a["key"]: summarize_app(a, all_feats, per_app_probes.get(a["key"]) if a["probes"] else None)
        for a in APPS
    }

    # Render detail pages
    if args.app:
        apps_to_render = [a for a in APPS if a["key"] == args.app]
        if not apps_to_render:
            print(f"Unknown app: {args.app}. Known: {[a['key'] for a in APPS]}")
            return 2
    else:
        apps_to_render = APPS

    for app in apps_to_render:
        html_doc = render_app_detail(
            app=app,
            features_for_this_app=features_for_app(app, all_feats),
            probes=per_app_probes.get(app["key"]) if app["probes"] else None,
            deploy=per_app_deploy.get(app["key"]),
            history=history,
            probed_at=probed_at,
            args_note=note,
        )
        out = DASHBOARD_DIR / detail_filename(app["key"])
        out.write_text(html_doc, encoding="utf-8")
        print(f"[{now_iso()}] Wrote {out}")

    # Render index only if not --app-scoped (or always — index is cheap)
    stories_doc = load_stories()
    index_doc = render_index(all_feats, per_app_summary, history, probed_at, note, stories_doc)
    INDEX_HTML.write_text(index_doc, encoding="utf-8")
    print(f"[{now_iso()}] Wrote {INDEX_HTML}")

    # Back-compat: keep dashboard.html as a redirect to index.html so old bookmarks still work
    legacy = DASHBOARD_DIR / "dashboard.html"
    legacy.write_text(
        '<!doctype html><meta http-equiv="refresh" content="0;url=index.html">'
        '<title>Redirecting…</title><p>Redirecting to <a href="index.html">index.html</a>.</p>',
        encoding="utf-8",
    )

    if args.open:
        try:
            os.startfile(str(INDEX_HTML))  # Windows
        except Exception as e:
            print(f"Could not auto-open: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
