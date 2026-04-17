"""
OSE Deployment Truth Dashboard — v1

Single-file Python tool. Probes live staging + reads git + reads a local test
cache, then writes a self-contained dashboard.html.

Usage:
  py dashboard.py                    # fast: probe endpoints + git, reuse cached test results
  py dashboard.py --run-tests t0     # run T0 Gate suite and update cache
  py dashboard.py --run-tests brain  # run OCR-docs brain pyramid and update cache
  py dashboard.py --run-tests all    # run everything (slow — 3-5 min)
  py dashboard.py --open             # also open the html in default browser

Paths are hardcoded for Matt's machine. Pure stdlib.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ────────────────────────────────────────────────────────────────────

OSE_REPO = Path("C:/Users/mzdan/dev/ourCommunityRituals/ourSharedEvents")
BRAIN_REPO = Path("C:/Users/mzdan/dev/ourCommunityRituals/OCR-docs")
DASHBOARD_DIR = BRAIN_REPO / "dashboard"
STATE_FILE = DASHBOARD_DIR / ".state.json"
OUT_HTML = DASHBOARD_DIR / "dashboard.html"

STAGING_BASE = "https://stg.oursharedevents.com"
PROD_BASE = "https://oursharedevents.com"

# Canonical routes grouped by handler. Each entry: (path, label, expected_status, aliases)
# expected_status: int | tuple of ints | "auth" (401/403 is healthy) | "any" (any 2xx/3xx)
# Expected-status notes:
# - 200 = publicly visible
# - 302 = Cloudflare Access-protected (unauth users redirect to mzdano.cloudflareaccess.com login)
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

# Test Pyramid — features with known file dirs + run commands + test-count hints.
# run_cmd is relative to OSE_REPO unless noted.
TEST_FEATURES = [
    {
        "tier": "T0",
        "name": "Gate — Unit (Vitest)",
        "dir": "tests/unit",
        "run_cmd": "npm test",
        "key": "t0-unit",
    },
    {
        "tier": "T0",
        "name": "Gate — Contract",
        "dir": "tests/contract",
        "run_cmd": "npx vitest run tests/contract",
        "key": "t0-contract",
    },
    {
        "tier": "T0",
        "name": "Gate — Worker Schema (D1)",
        "dir": "workers/oursharedevents/tests",
        "run_cmd": "npm test",
        "cwd": "workers/oursharedevents",
        "key": "t0-d1-schema",
    },
    {
        "tier": "T0",
        "name": "Gate — TypeScript + Lint",
        "dir": "workers/oursharedevents/src",
        "run_cmd": "npx tsc --noEmit && npx eslint config/ scripts/ tests/unit/ tests/contract/",
        "key": "t0-typelint",
    },
    {
        "tier": "T2",
        "name": "Smoke — Security XSS + Auth",
        "dir": "tests/e2e/1-smoke",
        "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/1-smoke/security-smoke.spec.js",
        "key": "t2-security-smoke",
    },
    {
        "tier": "T2",
        "name": "Smoke — IAC Health + Fail-Fast",
        "dir": "tests/api/smoke",
        "run_cmd": "npx playwright test --config=playwright.smoke.config.ts tests/api/smoke/api-health.spec.ts tests/api/smoke/fail-fast-gates.spec.ts",
        "key": "t2-iac-smoke",
    },
    {
        "tier": "T3",
        "name": "Contract — Newman API",
        "dir": "postman/collections",
        "run_cmd": "npx newman run postman/collections/ose-api.json -e postman/environments/ose-staging.json --reporters cli",
        "key": "t3-newman-api",
    },
    {
        "tier": "T3",
        "name": "Contract — Newman Pages",
        "dir": "postman/collections",
        "run_cmd": "npx newman run postman/collections/ose-pages.json -e postman/environments/ose-staging.json --reporters cli",
        "key": "t3-newman-pages",
    },
    {
        "tier": "T4",
        "name": "Functional — Architecture Invariants",
        "dir": "tests/e2e/0-architecture",
        "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/0-architecture/",
        "key": "t4-arch",
    },
    {
        "tier": "T4",
        "name": "Functional — Core Journeys",
        "dir": "tests/e2e/3-flows",
        "run_cmd": "npx playwright test --config=playwright.e2e-smoke.config.ts tests/e2e/3-flows/sponsor-journey.spec.ts",
        "key": "t4-journey",
    },
    {
        "tier": "T4",
        "name": "Functional — UI Smoke",
        "dir": "tests/ui/smoke",
        "run_cmd": "npm run test:ui:smoke",
        "key": "t4-ui",
    },
    {
        "tier": "Brain",
        "name": "Brain Test Pyramid (OCR-docs)",
        "dir": "ocr-docs-brain/tests",
        "run_cmd": "py ocr-docs-brain/tests/run_all.py",
        "cwd": str(BRAIN_REPO),
        "key": "brain",
    },
]


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
    """Probe one URL. Does NOT follow redirects — surfaces the server's actual response code.
    Returns bytes=body length, body_head=first 400 chars, redirect=location if 3xx."""
    url = base + path
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "ocr-dashboard/1.0"})
        with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as resp:
            body = resp.read()
            elapsed_ms = int((time.time() - t0) * 1000)
            text = body[:400].decode("utf-8", errors="replace")
            return {
                "url": url,
                "status": resp.status,
                "bytes": len(body),
                "ms": elapsed_ms,
                "body_head": text,
                "redirect": resp.headers.get("Location"),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        body = e.read() if hasattr(e, "read") else b""
        return {"url": url, "status": e.code, "bytes": len(body), "ms": elapsed_ms,
                "body_head": body[:400].decode("utf-8", errors="replace"),
                "redirect": e.headers.get("Location") if e.headers else None,
                "error": None}
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
    # stable order by ROUTES declaration
    order = {r[0]: i for i, r in enumerate(ROUTES)}
    out.sort(key=lambda d: order[d["path"]])
    return out


def status_class(probe: dict) -> tuple[str, str]:
    """Return (css_class, text_summary) from an endpoint probe."""
    if probe.get("error") or probe.get("status") is None:
        return "fail", f"ERR {probe.get('error','?')[:40]}"
    expected = probe.get("expected")
    status = probe["status"]
    redirect_to = probe.get("redirect")
    redirect_hint = f" → {redirect_to}" if redirect_to and 300 <= status < 400 else ""
    if isinstance(expected, int):
        ok = (status == expected)
    elif isinstance(expected, tuple):
        ok = status in expected
    else:
        ok = 200 <= status < 400
    if ok:
        return "pass", f"{status} · {probe['bytes']:,}b · {probe['ms']}ms{redirect_hint}"
    return "fail", f"{status} (expected {expected}) · {probe['bytes']:,}b{redirect_hint}"


# ─── Git / deployment state ───────────────────────────────────────────────────

def parse_deployed_version(health_probe: dict) -> dict:
    """From /health body extract {version, commit, deployed_at_hint}."""
    try:
        data = json.loads(health_probe.get("body_head", "") or "{}")
    except Exception:
        return {}
    version = data.get("version", "")
    # Pattern: stg-<shortsha>-<YYYYMMDD> or prod-<shortsha>-<YYYYMMDD>
    m = re.match(r"(?:stg|prod)-([0-9a-f]+)-(\d{8})", version)
    if not m:
        return {"version": version}
    return {"version": version, "commit": m.group(1), "date": m.group(2)}


def deployment_state() -> dict:
    """Live probe /health, compare to origin/main."""
    health = probe_one(STAGING_BASE, "/health", timeout=10)
    dep = parse_deployed_version(health)
    git("fetch", "origin", "--quiet")
    origin_main = git("rev-parse", "--short", "origin/main")
    origin_main_long = git("rev-parse", "origin/main")
    origin_main_msg = git("log", "-1", "--format=%s", "origin/main")
    origin_main_date = git("log", "-1", "--format=%ci", "origin/main")

    commits_since: list[dict] = []
    drift_worker = 0
    drift_ci = 0
    if dep.get("commit"):
        log_lines = git("log", "--oneline", f"{dep['commit']}..origin/main").splitlines()
        for line in log_lines[:50]:
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            sha, msg = parts
            # classify worker vs CI/tests/docs
            files = git("show", "--name-only", "--format=", sha).splitlines()
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
        "health": health,
        "deployed": dep,
        "origin_main": {
            "short": origin_main,
            "sha": origin_main_long,
            "msg": origin_main_msg,
            "date": origin_main_date,
        },
        "commits_since_deploy": commits_since,
        "drift_worker": drift_worker,
        "drift_ci": drift_ci,
    }


# ─── Test feature inventory ───────────────────────────────────────────────────

TEST_FUNC_RE = re.compile(r"(?m)^\s*(?:it|test|describe)\s*\(")
PLAYWRIGHT_RE = re.compile(r"(?m)^\s*test\s*\(")


def count_tests_in_dir(dir_path: Path) -> dict:
    """Count test files and approximate test() / it() calls."""
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
        # skip node_modules, .archive
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
    """Count requests + test assertions in a Postman collection."""
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
            # count Postman collection requests
            coll = OSE_REPO / feat["dir"] / (
                "ose-api.json" if feat["key"] == "t3-newman-api" else "ose-pages.json"
            )
            inv = count_newman_tests(coll)
        else:
            inv = count_tests_in_dir(OSE_REPO / feat["dir"] if Path(feat["dir"]).parts[0] != "ocr-docs-brain" else cwd / feat["dir"])
        run = cached.get(feat["key"], {})
        rows.append({
            **feat,
            "files": inv.get("files", 0),
            "test_calls": inv.get("test_calls", 0),
            "requests": inv.get("requests"),
            "exists": inv.get("exists", False),
            "last_run": run.get("when"),
            "result": run.get("result"),  # "pass" | "fail" | "partial"
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


# ─── Test runners ─────────────────────────────────────────────────────────────

def run_cmd(cmd: str, cwd: Path, timeout: int = 600) -> dict:
    """Run a shell command, capture output + exit code."""
    t0 = time.time()
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return {
            "rc": r.returncode,
            "stdout": r.stdout[-8000:],
            "stderr": r.stderr[-2000:],
            "elapsed_s": int(time.time() - t0),
        }
    except subprocess.TimeoutExpired:
        return {"rc": 124, "stdout": "", "stderr": f"Timed out after {timeout}s",
                "elapsed_s": timeout}
    except Exception as e:
        return {"rc": -1, "stdout": "", "stderr": str(e), "elapsed_s": int(time.time() - t0)}


VITEST_SUMMARY = re.compile(r"Tests\s+(?:(\d+)\s+passed(?:\s*\|\s*(\d+)\s+failed)?(?:\s*\|\s*(\d+)\s+skipped)?|(\d+)\s+failed.*?(\d+)\s+passed)")
PLAYWRIGHT_SUMMARY = re.compile(r"(\d+)\s+passed.*?(\d+)\s+failed|(\d+)\s+failed.*?(\d+)\s+passed|(\d+)\s+passed")
BRAIN_SUMMARY = re.compile(r"(\d+)\s+PASSED|(\d+)\s+FAILED|Total:\s+(\d+)")


def parse_test_output(output: str) -> dict:
    """Heuristic parse of test runner output — works for vitest, playwright, newman, brain pyramid."""
    out = {"pass": None, "fail": None, "skip": None, "total": None, "detail": None}

    # Brain pyramid: look for the "PYRAMID SUMMARY: 7 pass / 2 fail / 0 skip" line first —
    # those are LEVEL counts. Also sum per-level test counts for detail.
    ps = re.search(r"PYRAMID SUMMARY:\s*(\d+)\s+pass\s*/\s*(\d+)\s+fail\s*/\s*(\d+)\s+skip", output)
    if ps:
        out["pass"] = int(ps.group(1))
        out["fail"] = int(ps.group(2))
        out["skip"] = int(ps.group(3))
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        # roll up per-level tests as the "detail" number
        level_tests = re.findall(r"(\d+)\s+pass\s*/\s*(\d+)\s+fail\s*\(total\s+(\d+)\)", output)
        if level_tests:
            tests_pass = sum(int(p) for p, _, _ in level_tests)
            tests_fail = sum(int(f) for _, f, _ in level_tests)
            tests_total = sum(int(t) for _, _, t in level_tests)
            out["detail"] = f"{tests_pass} tests pass, {tests_fail} fail across {len(level_tests)} passing level(s) (of {out['total']})"
        return out

    # vitest format: "Tests  42 passed | 3 failed | 1 skipped (46)" or similar
    m = re.search(r"Tests\s+(\d+)\s+passed(?:\s*\|\s*(\d+)\s+failed)?(?:\s*\|\s*(\d+)\s+skipped)?", output)
    if m:
        out["pass"] = int(m.group(1))
        out["fail"] = int(m.group(2) or 0)
        out["skip"] = int(m.group(3) or 0)
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        return out
    # playwright: "  42 passed (30.2s)" or "  3 failed"
    p = re.search(r"(\d+)\s+passed(?:[\s(])", output)
    f = re.search(r"(\d+)\s+failed(?:[\s(])", output)
    s = re.search(r"(\d+)\s+skipped(?:[\s(])", output)
    if p or f:
        out["pass"] = int(p.group(1)) if p else 0
        out["fail"] = int(f.group(1)) if f else 0
        out["skip"] = int(s.group(1)) if s else 0
        out["total"] = out["pass"] + out["fail"] + out["skip"]
        return out
    # newman: "│ assertions │ 42 │ 0 │" kinda tables — just look for PASS/FAIL
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
    # Verdict: 0 fails parsed => pass. Otherwise fail. rc alone isn't enough
    # (some suites exit 0 even with recoverable fails).
    pf = parsed.get("fail")
    if result["rc"] == 0 and (pf is None or pf == 0):
        verdict = "pass"
    elif pf is not None and pf > 0:
        verdict = "fail"
    else:
        verdict = "fail" if result["rc"] != 0 else "pass"
    return {
        "when": now_iso(),
        "result": verdict,
        "rc": result["rc"],
        "elapsed_s": result["elapsed_s"],
        "pass": parsed.get("pass"),
        "fail": parsed.get("fail"),
        "skip": parsed.get("skip"),
        "total": parsed.get("total"),
        "detail": parsed.get("detail"),
        "output_tail": combined[-1500:],
    }


# ─── Renderer ─────────────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, Segoe UI, system-ui, sans-serif; margin: 0; padding: 20px; background: #0a0a0f; color: #e5e7eb; line-height: 1.45; }
h1 { margin: 0 0 4px; font-size: 20px; letter-spacing: -0.01em; }
h2 { margin: 20px 0 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #9ca3af; font-weight: 600; }
.subtitle { color: #6b7280; font-size: 12px; margin-bottom: 20px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 1000px) { .grid { grid-template-columns: 1fr; } }
.card { background: #14141c; border: 1px solid #1f2028; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 6px 8px; font-weight: 600; color: #9ca3af; border-bottom: 1px solid #1f2028; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: 8px; border-bottom: 1px solid #191922; vertical-align: top; }
tr:last-child td { border-bottom: none; }
.pass { color: #34d399; }
.fail { color: #f87171; }
.warn { color: #fbbf24; }
.dim { color: #6b7280; }
.pill { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.pill.pass { background: rgba(52,211,153,.14); color: #34d399; }
.pill.fail { background: rgba(248,113,113,.14); color: #f87171; }
.pill.warn { background: rgba(251,191,36,.14); color: #fbbf24; }
.pill.dim { background: rgba(107,114,128,.14); color: #9ca3af; }
.mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; }
.bar { display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: #1f2028; min-width: 80px; }
.bar .seg { height: 100%; }
.bar .seg.pass { background: #34d399; }
.bar .seg.fail { background: #f87171; }
.bar .seg.skip { background: #6b7280; }
.row-label { font-weight: 600; color: #e5e7eb; }
.tier-badge { display: inline-block; padding: 1px 6px; border-radius: 4px; background: #1f2028; font-size: 10px; font-weight: 700; margin-right: 6px; }
.tier-T0 { color: #60a5fa; }
.tier-T2 { color: #fbbf24; }
.tier-T3 { color: #a78bfa; }
.tier-T4 { color: #fb7185; }
.tier-Brain { color: #34d399; }
.deploy-panel { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
@media (max-width: 900px) { .deploy-panel { grid-template-columns: repeat(2, 1fr); } }
.deploy-kpi { background: #14141c; border: 1px solid #1f2028; border-radius: 8px; padding: 14px; }
.deploy-kpi .k { font-size: 10px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.08em; margin-bottom: 6px; }
.deploy-kpi .v { font-size: 18px; font-weight: 700; }
.cmd { background: #0f0f16; border: 1px solid #1f2028; padding: 4px 6px; border-radius: 4px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; color: #c4b5fd; display: inline-block; max-width: 100%; overflow-x: auto; }
details summary { cursor: pointer; color: #9ca3af; font-size: 11px; }
details[open] summary { color: #e5e7eb; }
.body-head { background: #0a0a10; padding: 6px 8px; border-radius: 4px; max-height: 120px; overflow-y: auto; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 10px; color: #9ca3af; white-space: pre-wrap; word-break: break-all; margin-top: 4px; }
footer { margin-top: 32px; color: #6b7280; font-size: 11px; text-align: center; }
.fresh-now { color: #34d399; }
.fresh-ok { color: #9ca3af; }
.fresh-stale { color: #fbbf24; }
.fresh-unknown { color: #6b7280; }
"""

def render_html(deploy: dict, probes: list[dict], features: list[dict], args_note: str) -> str:
    e = html.escape
    probed_at = deploy.get("probed_at", now_iso())

    # Deployment KPIs
    dep = deploy.get("deployed", {}) or {}
    om = deploy.get("origin_main", {}) or {}
    drift_worker = deploy.get("drift_worker", 0)
    drift_ci = deploy.get("drift_ci", 0)
    total_drift = drift_worker + drift_ci
    health = deploy.get("health", {})
    health_cls, health_txt = status_class({
        "status": health.get("status"), "bytes": health.get("bytes", 0),
        "ms": health.get("ms", 0), "error": health.get("error"), "expected": 200,
    })

    # Page rollup
    pages_total = len(probes)
    pages_pass = sum(1 for p in probes if status_class(p)[0] == "pass")
    pages_cls = "pass" if pages_pass == pages_total else ("warn" if pages_pass >= pages_total - 2 else "fail")

    # Suite rollup
    suites_with_runs = [f for f in features if f.get("total") is not None]
    suites_pass = sum(1 for f in suites_with_runs if f.get("result") == "pass")
    suites_fail = sum(1 for f in suites_with_runs if f.get("result") == "fail")
    tests_pass = sum(f.get("pass") or 0 for f in suites_with_runs)
    tests_fail = sum(f.get("fail") or 0 for f in suites_with_runs)
    if not suites_with_runs:
        suites_summary = f'<span class="dim">0 of {len(features)} run</span>'
        suites_detail = '<span class="dim">Run <span class="mono">py dashboard.py --run-tests all</span></span>'
        suites_cls = "dim"
    else:
        suites_summary = f'{suites_pass} ✓ · {suites_fail} ✗'
        suites_detail = f'<span class="pass">{tests_pass} tests pass</span> · <span class="fail">{tests_fail} fail</span>'
        suites_cls = "pass" if suites_fail == 0 else "warn"

    deploy_html = f"""
    <div class="deploy-panel">
      <div class="deploy-kpi">
        <div class="k">Staging /health</div>
        <div class="v {health_cls}">{'🟢' if health_cls == 'pass' else '🔴'} {e(health_txt)}</div>
        <div class="dim mono" style="margin-top:6px;font-size:11px;">{e(dep.get('version','(unknown)'))}</div>
      </div>
      <div class="deploy-kpi">
        <div class="k">Pages green</div>
        <div class="v {pages_cls}">{pages_pass} <span class="dim" style="font-size:14px;">/ {pages_total}</span></div>
        <div class="dim mono" style="margin-top:6px;font-size:11px;">
          {pages_total - pages_pass} need attention
        </div>
      </div>
      <div class="deploy-kpi">
        <div class="k">Test suites</div>
        <div class="v {suites_cls}">{suites_summary}</div>
        <div class="dim mono" style="margin-top:6px;font-size:11px;">
          {suites_detail}
        </div>
      </div>
      <div class="deploy-kpi">
        <div class="k">Drift (deploy → origin/main)</div>
        <div class="v {'warn' if drift_worker else 'pass' if total_drift == 0 else 'dim'}">
          {total_drift} <span class="dim" style="font-size:14px;">commits</span>
        </div>
        <div class="dim mono" style="margin-top:6px;font-size:11px;">
          worker: <span class="{'warn' if drift_worker else 'pass'}">{drift_worker}</span>
          &nbsp;·&nbsp;
          ci/test: <span class="dim">{drift_ci}</span>
        </div>
      </div>
    </div>
    """

    # Endpoints table
    rows_ep = []
    for p in probes:
        cls, txt = status_class(p)
        aliases_note = f"<span class='dim'>(+ {len(p['aliases'])} aliases)</span>" if p["aliases"] else ""
        rows_ep.append(f"""
          <tr>
            <td><span class="row-label">{e(p['label'])}</span><br><span class="mono dim">{e(p['path'])}</span> {aliases_note}</td>
            <td><span class="pill {cls}">{e(txt)}</span></td>
          </tr>
        """)

    endpoints_html = f"""
      <h2>Pages — live staging probes</h2>
      <div class="card">
        <table>
          <thead><tr><th>Page</th><th>Live status</th></tr></thead>
          <tbody>{''.join(rows_ep)}</tbody>
        </table>
      </div>
    """

    # Test features table
    rows_feat = []
    total_pass = 0
    total_fail = 0
    total_skip = 0
    total_total = 0
    known_any = False

    for f in features:
        p, fa, sk, tot = f.get("pass"), f.get("fail"), f.get("skip"), f.get("total")
        if tot is not None:
            known_any = True
            total_pass += p or 0
            total_fail += fa or 0
            total_skip += sk or 0
            total_total += tot

        # result badge
        if f.get("result") == "pass":
            status_cell = f'<span class="pill pass">PASS</span>'
        elif f.get("result") == "fail":
            status_cell = f'<span class="pill fail">FAIL</span>'
        else:
            status_cell = f'<span class="pill dim">NEVER RUN</span>'

        # pass/fail bar
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
              <div class="dim mono" style="font-size:10px;margin-top:3px;">
                {p or 0}✓ / {fa or 0}✗ / {sk or 0}⊘ of {tot}
              </div>
              {detail_html}
            """
        else:
            bar = f'<span class="dim mono">{f["files"]} files · ~{f["test_calls"]} calls</span>'
            if f["key"].startswith("t3-newman") and f.get("requests"):
                bar = f'<span class="dim mono">{f["requests"]} requests</span>'

        last_run_cell = (
            f'<span class="mono dim">{e(f["last_run"] or "—")}</span>'
            + (f'<br><span class="dim" style="font-size:10px;">rc: {f.get("rc",0) if "rc" in f else "?"} · {f.get("elapsed_s",0) if "elapsed_s" in f else 0}s</span>'
                if f.get("last_run") else "")
        )

        rows_feat.append(f"""
          <tr>
            <td>
              <span class="tier-badge tier-{f['tier']}">{f['tier']}</span>
              <span class="row-label">{e(f['name'])}</span>
              <div class="dim mono" style="font-size:10px;margin-top:3px;">{e(f['dir'])}</div>
            </td>
            <td>{bar}</td>
            <td>{status_cell}<br>{last_run_cell}</td>
            <td><span class="cmd">{e(f['run_cmd'])}</span></td>
          </tr>
        """)

    features_html = f"""
      <h2>Test Features — pyramid breakdown</h2>
      <div class="card">
        <table>
          <thead><tr><th>Feature</th><th>Pass / Fail / Skip</th><th>Status &amp; last run</th><th>Refresh command</th></tr></thead>
          <tbody>{''.join(rows_feat)}</tbody>
        </table>
        <div class="dim" style="margin-top:10px;font-size:11px;">
          Rollup across features with run data: <span class="pass">{total_pass}✓</span> / <span class="fail">{total_fail}✗</span> / <span class="dim">{total_skip}⊘</span> of {total_total}.
          {"" if known_any else "<em>No suites have been run in-dashboard yet. Use <code>py dashboard.py --run-tests &lt;key|all&gt;</code>.</em>"}
        </div>
      </div>
    """

    # Drift detail
    drift_rows = []
    for c in deploy.get("commits_since_deploy", [])[:30]:
        tag_cls = "warn" if c["tag"] == "worker" else "dim"
        drift_rows.append(f"""
          <tr>
            <td class="mono">{e(c['sha'])}</td>
            <td><span class="pill {tag_cls}">{e(c['tag'])}</span></td>
            <td>{e(c['msg'][:110])}</td>
          </tr>
        """)
    drift_html = f"""
      <h2>Drift — commits since deployed ({e((dep.get('commit') or '?')[:7])} → {e(om.get('short','?'))})</h2>
      <div class="card">
        <table>
          <thead><tr><th>SHA</th><th>Tag</th><th>Message</th></tr></thead>
          <tbody>{''.join(drift_rows) if drift_rows else '<tr><td colspan="3" class="dim">No commits — staging is at origin/main.</td></tr>'}</tbody>
        </table>
        <div class="dim" style="margin-top:10px;font-size:11px;">
          {"⚠️ Worker code changed since last deploy — staging may be behind." if drift_worker else "✓ No worker code has changed since last deploy. Staging is functionally current."}
        </div>
      </div>
    """

    # Staging body head preview
    health_body = (health.get("body_head") or "")[:400]
    health_preview = f'<details><summary>Show /health response body</summary><div class="body-head">{e(health_body)}</div></details>' if health_body else ""

    html_doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>OSE — Deployment Truth · {e(probed_at)}</title>
<style>{CSS}</style>
</head><body>
  <h1>OSE — Deployment Truth Dashboard</h1>
  <div class="subtitle">
    Probed at <span class="mono">{e(probed_at)}</span>.
    Base: <span class="mono">{e(STAGING_BASE)}</span>.
    Regenerate: <span class="cmd">py C:\\Users\\mzdan\\dev\\ourCommunityRituals\\OCR-docs\\dashboard\\dashboard.py</span>
    {args_note}
  </div>

  {deploy_html}
  {health_preview}

  <div class="grid">
    <div>{endpoints_html}</div>
    <div>{features_html}</div>
  </div>

  {drift_html}

  <footer>
    ocr-dashboard v1 · self-contained · reads live <span class="mono">stg.oursharedevents.com</span> + <span class="mono">origin/main</span><br>
    Test suite data cached at <span class="mono">OCR-docs/dashboard/.state.json</span> — re-runs update it.
  </footer>
</body></html>
"""
    return html_doc


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    # Force UTF-8 stdout so Unicode check/cross marks render on Windows cp1252 consoles
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--run-tests", help="Suite key to run (t0-unit, t2-security-smoke, brain, all)")
    ap.add_argument("--open", action="store_true", help="Open dashboard.html in default browser")
    args = ap.parse_args()

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    # Probe live endpoints (always)
    print(f"[{now_iso()}] Probing {STAGING_BASE} …")
    probes = probe_all_endpoints(STAGING_BASE)
    for p in probes:
        cls, txt = status_class(p)
        print(f"  {'✓' if cls == 'pass' else '✗'} {p['path']:<28} {txt}")

    # Git + deployment state
    print(f"[{now_iso()}] Reading git + deployment state …")
    deploy = deployment_state()

    # Test feature inventory (static file counts + cached last-run)
    print(f"[{now_iso()}] Inventorying test features …")
    features = inventory_features()

    # Optional: run a suite and update the cache
    note = ""
    if args.run_tests:
        targets = [f for f in features if args.run_tests == "all" or f["key"] == args.run_tests]
        if not targets:
            print(f"Unknown suite key: {args.run_tests}. Available: {[f['key'] for f in features]}")
            return 2
        state = load_state()
        for feat in targets:
            print(f"[{now_iso()}] Running {feat['key']} — {feat['name']} …")
            result = run_feature(feat)
            state.setdefault("suites", {})[feat["key"]] = result
            print(f"  → {result['result'].upper()}  pass={result['pass']} fail={result['fail']} "
                  f"skip={result['skip']} total={result['total']} rc={result['rc']} "
                  f"in {result['elapsed_s']}s")
        save_state(state)
        features = inventory_features()  # refresh with new cache
        note = f' · <span class="pass">Ran {len(targets)} suite(s) just now.</span>'

    # Render HTML
    html_doc = render_html(deploy, probes, features, note)
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    print(f"[{now_iso()}] Wrote {OUT_HTML}")

    if args.open:
        try:
            os.startfile(str(OUT_HTML))  # Windows
        except Exception as e:
            print(f"Could not auto-open: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
