#!/usr/bin/env python3
"""Generate a playwright-cli config that LAUNCHES Camoufox with stealth intact.

playwright-cli cannot *attach* to a Camoufox server (a Playwright server hands each
client a context-less browser and `attach` refuses to create a context). But it CAN
*launch* the Camoufox binary directly: Camoufox's `launch_options()` returns exactly
Playwright Firefox launch options — executable path, args, env (the fingerprint), and
Firefox prefs — which go straight into playwright-cli's `browser.launchOptions`.

Then:  playwright-cli open <url> --browser firefox --config <this file>

Verified live: `navigator.webdriver` is false and Camoufox's spoofed fingerprint
(e.g. a Windows UA on a Mac) survives. Baked in (carry over): `--os`, `--geoip`,
`--proxy` — they land in the launch env. LOST vs the Python wrapper: the runtime
cursor-humanization (`page.mouse` interpolation is applied by the wrapper, not by
playwright-cli) and `persistent_context` (launchOptions can't express a
user-data-dir, so every run is a fresh profile — use playwright-cli's
`--profile`/`--persistent`, or the Python wrapper, for durable logins).

IMPORTANT: the generated config pins ONE fingerprint. Regenerate it every run and
gitignore it — a frozen, reused fingerprint is *more* detectable than baseline.

Usage:
  python3 pwcli_config.py --out .playwright/cli.config.json [--os windows] [--geoip] [--proxy http://host:port] [--headless]
  playwright-cli open https://example.com --browser firefox --config .playwright/cli.config.json
  python3 pwcli_config.py --self-test        # conversion logic only, no Camoufox

Exit codes: 0 ok, 1 could not build the config, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Camoufox returns snake_case; Playwright launchOptions are camelCase.
SNAKE2CAMEL = {
    "executable_path": "executablePath",
    "firefox_user_prefs": "firefoxUserPrefs",
    "ignore_default_args": "ignoreDefaultArgs",
    "handle_sigint": "handleSIGINT",
    "handle_sigterm": "handleSIGTERM",
    "handle_sighup": "handleSIGHUP",
}
# Valid Playwright firefox.launch options we forward (drop anything Camoufox-internal).
ALLOW = {"executablePath", "args", "env", "firefoxUserPrefs", "ignoreDefaultArgs",
         "headless", "proxy", "timeout", "downloadsPath"}


def to_launch_options(raw: dict) -> tuple[dict, list[str]]:
    """Convert Camoufox launch_options() to a playwright-cli launchOptions dict.

    Returns (launchOptions, dropped_keys)."""
    camel = {SNAKE2CAMEL.get(k, k): v for k, v in raw.items()}
    kept = {k: v for k, v in camel.items() if k in ALLOW}
    dropped = sorted(set(camel) - set(kept))
    return kept, dropped


def camoufox_launch_options(**kw) -> dict:
    try:
        from camoufox import launch_options
    except Exception:  # noqa: BLE001 - older/newer layout
        from camoufox.utils import launch_options
    return launch_options(**kw)


def self_test() -> int:
    raw = {"executable_path": "/x/camoufox", "args": ["-foo"], "env": {"CAMOU_CONFIG": "{}"},
           "firefox_user_prefs": {"a": 1}, "headless": True, "some_internal_only": 42}
    lo, dropped = to_launch_options(raw)
    assert lo["executablePath"] == "/x/camoufox"
    assert lo["firefoxUserPrefs"] == {"a": 1}
    assert "env" in lo and "args" in lo and lo["headless"] is True
    assert "some_internal_only" not in lo and "some_internal_only" in dropped
    assert "executable_path" not in lo  # snake dropped in favour of camel
    print("self-test: ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=".playwright/cli.config.json",
                    help="config path (default: .playwright/cli.config.json)")
    ap.add_argument("--os", dest="os_name", help="fingerprint OS (match the real host)")
    ap.add_argument("--geoip", action="store_true", help="bake geoip locale/timezone into the launch env")
    ap.add_argument("--proxy", help="proxy server url, e.g. http://host:port")
    ap.add_argument("--headless", action="store_true", help="headless (more detectable; default headful)")
    ap.add_argument("--humanize", type=float, metavar="SECONDS",
                    help="bake the humanize value into the launch env (note: the wrapper's runtime cursor interpolation is NOT applied under playwright-cli)")
    ap.add_argument("--self-test", action="store_true", help="test conversion logic, no Camoufox")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    kw: dict = {"headless": args.headless}
    if args.os_name:
        kw["os"] = args.os_name
    if args.geoip:
        kw["geoip"] = True
    if args.humanize is not None:
        kw["humanize"] = args.humanize
    if args.proxy:
        kw["proxy"] = {"server": args.proxy}

    try:
        raw = camoufox_launch_options(**kw)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: could not compute Camoufox launch options ({exc}) — run camoufox-setup",
              file=sys.stderr)
        print("RESULT: fail")
        return 1

    lo, dropped = to_launch_options(raw)
    if not lo.get("executablePath"):
        print("ERROR: no executablePath from Camoufox — is the browser fetched? (camoufox fetch)",
              file=sys.stderr)
        print("RESULT: fail")
        return 1

    cfg = {"browser": {"browserName": "firefox", "launchOptions": lo}}
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, default=str)

    print(f"STATUS config: {out}")
    print(f"STATUS executablePath: {lo['executablePath']}")
    if dropped:
        print(f"STATUS dropped (Camoufox-only, already baked into env): {dropped}")
    print("NOTE: this config PINS ONE fingerprint — regenerate it every run and gitignore "
          "it, or sessions become correlatable (a frozen fingerprint is MORE detectable).")
    print(f"STATUS next: playwright-cli open <url> --browser firefox --config {out}   "
          "(Linux: prefix with `xvfb-run -a` and keep headless off)")
    print("RESULT: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
