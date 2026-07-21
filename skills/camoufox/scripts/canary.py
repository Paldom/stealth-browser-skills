#!/usr/bin/env python3
"""Local automation-leak canary for a Camoufox (Firefox) browser session.

Runs a small set of browser-side checks and prints a machine-readable scorecard.
LOCAL canaries are the authoritative pass/fail; external suites (Sannysoft, CreepJS)
are optional, non-blocking screenshots for human review — third-party pages change
and rate-limit, so they never gate the result.

Checks are tuned for a FIREFOX-based browser (Camoufox), not Chrome — e.g. we do
NOT expect a `window.chrome` object, and we do not treat empty `navigator.plugins`
as a failure.

REQUIRED (fail the run): navigator.webdriver is false; no Selenium/CDP automation
globals; user-agent has no "Headless"; canvas hash identical across two draws;
wheel input is trusted (isTrusted).
ADVISORY (reported, WARN only unless --strict): WebGL not a software renderer;
navigator.languages non-empty; hardwareConcurrency > 0; UA/platform coherent.

Usage:
  python3 canary.py                         # launch ephemeral Camoufox, run canaries
  python3 canary.py --ws ws://localhost:PORT/PATH   # test a running Camoufox server
  python3 canary.py --headless true --json          # CI-friendly
  python3 canary.py --external --out ./eval-out      # + screenshot allowlisted suites
  python3 canary.py --self-test                      # scoring logic only, no browser

Exit codes: 0 = all REQUIRED passed (and no WARN under --strict), 1 = failed, 2 = usage/error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

SOFTWARE_GPU = re.compile(r"swiftshader|llvmpipe|software|basic render|microsoft basic", re.I)
HEADLESS_UA = re.compile(r"headless", re.I)
AUTOMATION_KEY = re.compile(r"cdc_|_selenium|__selenium|__webdriver|__driver|_phantom|callphantom|domautomation", re.I)

# Allowlisted external test pages (optional, non-blocking). Official deployments only.
EXTERNAL_SUITES = {
    "sannysoft": "https://bot.sannysoft.com",
    "creepjs": "https://abrahamjuliot.github.io/creepjs",   # ONLY official GitHub Pages
    "browserscan": "https://www.browserscan.net/bot-detection",
}

# JS run in the page's isolated content world (no main_world_eval needed).
CANARY_JS = r"""
() => {
  const out = {};
  out.webdriver = navigator.webdriver;
  out.automationGlobals = Object.getOwnPropertyNames(window).filter(k =>
    /cdc_|_selenium|__selenium|__webdriver|__driver|_phantom|callPhantom|domAutomation/i.test(k));
  out.userAgent = navigator.userAgent;
  out.platform = navigator.platform || "";
  out.oscpu = navigator.oscpu || null;
  out.languages = navigator.languages || [];
  out.hardwareConcurrency = navigator.hardwareConcurrency || 0;
  try {
    const gl = document.createElement('canvas').getContext('webgl');
    const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
    out.webglRenderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null;
    out.webglVendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : null;
  } catch (e) { out.webglRenderer = null; out.webglVendor = null; }
  const draw = () => {
    const c = document.createElement('canvas'); c.width = 220; c.height = 40;
    const ctx = c.getContext('2d');
    ctx.textBaseline = 'top'; ctx.font = "14px 'Arial'";
    ctx.fillStyle = '#f60'; ctx.fillRect(8, 8, 120, 20);
    ctx.fillStyle = '#069'; ctx.fillText('stealth-canary-✓', 10, 10);
    return c.toDataURL();
  };
  const a = draw(), b = draw();
  out.canvasStable = a === b;
  out.canvasLen = a.length;
  window.__wheelTrusted = null;
  window.addEventListener('wheel', e => { window.__wheelTrusted = e.isTrusted; },
                          { once: true, passive: true });
  return out;
}
"""


def score(checks: dict, strict: bool = False) -> tuple[list[dict], bool]:
    """Pure scoring: map raw browser readings to (results, ok). No I/O."""
    results: list[dict] = []

    def add(name, level, ok, detail=""):
        results.append({"check": name, "level": level,
                        "status": "PASS" if ok else ("FAIL" if level == "required" else "WARN"),
                        "detail": detail})

    # REQUIRED
    add("navigator.webdriver==false", "required", checks.get("webdriver") is False,
        f"value={checks.get('webdriver')!r}")
    globs = checks.get("automationGlobals") or []
    add("no automation globals", "required", not globs, f"found={globs}")
    ua = checks.get("userAgent") or ""
    add("UA has no Headless", "required", not HEADLESS_UA.search(ua), ua[:80])
    add("canvas hash stable", "required", checks.get("canvasStable") is True,
        "identical across two draws" if checks.get("canvasStable") else "differs → per-call noise injector")
    wt = checks.get("wheelTrusted")
    if wt is True or wt is False:
        add("wheel input trusted", "required", wt is True, f"isTrusted={wt}")
    else:
        # Never silently drop it: if it couldn't be measured, surface it visibly
        # (advisory WARN — a measurement hiccup shouldn't hard-fail, but --strict catches it).
        add("wheel input measured", "advisory", False, f"could not measure wheel isTrusted (value={wt!r})")

    # ADVISORY
    gpu = checks.get("webglRenderer")
    if gpu:
        add("WebGL not software", "advisory", not SOFTWARE_GPU.search(gpu), gpu)
    else:
        add("WebGL renderer readable", "advisory", False, "renderer unknown/null")
    langs = checks.get("languages") or []
    add("languages present", "advisory", bool(langs), str(langs))
    add("hardwareConcurrency>0", "advisory", (checks.get("hardwareConcurrency") or 0) > 0,
        str(checks.get("hardwareConcurrency")))
    ua_l, plat = ua.lower(), (checks.get("platform") or "").lower()
    seam = ("windows" in ua_l and plat.startswith("linux")) or \
           ("linux" in ua_l and plat.startswith("win")) or \
           ("mac" in ua_l and plat.startswith("linux"))
    add("UA/platform coherent", "advisory", not seam, f"ua~{ua_l[:30]} platform={plat}")

    required_fail = any(r["status"] == "FAIL" for r in results)
    warn = any(r["status"] == "WARN" for r in results)
    ok = not required_fail and (not warn if strict else True)
    return results, ok


def run_browser(args) -> dict:
    from playwright.sync_api import sync_playwright

    checks: dict = {}
    if args.ws:
        with sync_playwright() as p:
            browser = p.firefox.connect(args.ws)
            page = browser.new_page()          # throwaway page — never touch the server's existing tabs
            try:
                checks = _probe(page, args)
            finally:
                page.close()                    # leave the server and its sessions intact
    else:
        from camoufox.sync_api import Camoufox
        headless = {"false": False, "true": True, "virtual": "virtual"}[args.headless]
        with Camoufox(headless=headless, humanize=True) as browser:
            page = browser.new_page()
            checks = _probe(page, args)
    return checks


def _probe(page, args) -> dict:
    page.goto("about:blank")
    checks = page.evaluate(CANARY_JS)
    try:
        page.mouse.move(200, 200)          # position over the viewport so the wheel dispatches
        page.mouse.wheel(0, 120)
        page.wait_for_function("() => window.__wheelTrusted !== null", timeout=3000)
        checks["wheelTrusted"] = page.evaluate(
            "() => { const v = window.__wheelTrusted; delete window.__wheelTrusted; return v; }")
    except Exception:  # noqa: BLE001 - if unmeasurable, score() surfaces it visibly (never silently dropped)
        checks["wheelTrusted"] = "unmeasured"
    if args.external:
        import os
        out = os.path.abspath(args.out or "./eval-out")
        os.makedirs(out, exist_ok=True)
        for name, url in EXTERNAL_SUITES.items():
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.screenshot(path=os.path.join(out, f"{name}.png"), full_page=True)
                print(f"EXTERNAL {name}: screenshot saved (review manually)")
            except Exception as exc:  # noqa: BLE001 - never gate on external sites
                print(f"EXTERNAL {name}: skipped ({exc})", file=sys.stderr)
    return checks


def self_test() -> int:
    clean = {"webdriver": False, "automationGlobals": [], "userAgent": "Mozilla/5.0 ... Firefox/152.0",
             "platform": "Win32", "canvasStable": True, "wheelTrusted": True,
             "webglRenderer": "NVIDIA GeForce RTX 4070", "languages": ["en-US", "en"],
             "hardwareConcurrency": 8}
    res, ok = score(clean)
    assert ok, res
    assert all(r["status"] != "FAIL" for r in res)

    dirty = {"webdriver": True, "automationGlobals": ["cdc_asdjflasutopfhvcZLmcfl_"],
             "userAgent": "Mozilla/5.0 HeadlessChrome/999", "platform": "Linux x86_64",
             "canvasStable": False, "wheelTrusted": False,
             "webglRenderer": "Google SwiftShader", "languages": [], "hardwareConcurrency": 0}
    res2, ok2 = score(dirty)
    assert not ok2
    fails = {r["check"] for r in res2 if r["status"] == "FAIL"}
    assert "navigator.webdriver==false" in fails and "no automation globals" in fails
    assert "canvas hash stable" in fails and "wheel input trusted" in fails

    # advisory-only issues should not fail non-strict, but should under --strict
    warnish = dict(clean, webglRenderer="llvmpipe (LLVM 15)")
    _, ok3 = score(warnish, strict=False)
    _, ok4 = score(warnish, strict=True)
    assert ok3 and not ok4

    # an UNMEASURED wheel must be surfaced (advisory WARN), never silently dropped
    unmeasured = dict(clean, wheelTrusted="unmeasured")
    res5, ok5 = score(unmeasured, strict=False)
    assert ok5, res5
    assert any(r["check"] == "wheel input measured" and r["status"] == "WARN" for r in res5)
    assert not any(r["check"] == "wheel input trusted" for r in res5)
    _, ok6 = score(unmeasured, strict=True)
    assert not ok6

    print("self-test: ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ws", help="connect to a running Camoufox server ws endpoint instead of launching")
    ap.add_argument("--headless", choices=["false", "true", "virtual"], default="false")
    ap.add_argument("--strict", action="store_true", help="advisory WARNs also fail the run")
    ap.add_argument("--external", action="store_true", help="also screenshot allowlisted external suites")
    ap.add_argument("--out", help="screenshot output dir (default ./eval-out)")
    ap.add_argument("--json", action="store_true", help="emit the scorecard as JSON")
    ap.add_argument("--self-test", action="store_true", help="run scoring logic only, no browser")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    try:
        checks = run_browser(args)
    except Exception as exc:  # noqa: BLE001
        print(f"EVAL-ERROR: {exc}", file=sys.stderr)
        print("RESULT: error")
        return 2

    results, ok = score(checks, strict=args.strict)
    if args.json:
        print(json.dumps({"results": results, "ok": ok, "raw": checks}, indent=2, default=str))
    else:
        for r in results:
            print(f"[{r['status']:4}] {r['level']:8} {r['check']} — {r['detail']}")
    print(f"RESULT: {'ok' if ok else 'fail'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
