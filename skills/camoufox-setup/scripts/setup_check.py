#!/usr/bin/env python3
"""Check (and optionally install) the Camoufox stealth-browser toolchain.

Idempotent: probes what is present, and with --install adds only what is missing.
Prints machine-readable STATUS lines and a final RESULT so an agent can self-correct.

Components
  REQUIRED  camoufox[geoip] pip package  +  the Camoufox Firefox binary (camoufox fetch)
  OPTIONAL  playwright-cli + its agent skills  (a SEPARATE general browser-automation
            layer for coding agents; it does NOT drive Camoufox — see references/toolchain.md)
  OPTIONAL  Xvfb on Linux  (only needed if you launch with headless="virtual")

Exit codes: 0 = all REQUIRED present, 1 = a required component missing, 2 = usage error.
Optional components missing never fail the run; they are reported as WARN.

Usage:
  python3 setup_check.py                 # check only, no changes
  python3 setup_check.py --install       # install missing required + optional
  python3 setup_check.py --install --required-only   # skip playwright-cli/Xvfb
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from importlib import metadata

PY = sys.executable


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - env dependent
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def browser_status() -> tuple[bool, str | None]:
    """(present, path) — the Camoufox Firefox binary is considered fetched when
    `python -m camoufox path` resolves to a non-empty directory."""
    r = run([PY, "-m", "camoufox", "path"])
    if r.returncode != 0:
        return False, None
    path = (r.stdout or "").strip()
    try:
        if path and os.path.isdir(path) and os.listdir(path):
            return True, path
    except OSError:
        return False, path or None
    return False, path or None


def emit(component: str, state: str, detail: str = "") -> None:
    print(f"STATUS {component}: {state}{(' ' + detail) if detail else ''}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", action="store_true", help="install missing components")
    ap.add_argument("--required-only", action="store_true", help="ignore playwright-cli and Xvfb")
    args = ap.parse_args()

    required_ok = True

    # 1) camoufox pip package (required) --------------------------------------
    ver = pkg_version("camoufox")
    if ver:
        emit("camoufox_pkg", "OK", ver)
    elif args.install:
        emit("camoufox_pkg", "INSTALLING")
        r = run([PY, "-m", "pip", "install", "-U", "camoufox[geoip]"])
        ver = pkg_version("camoufox")
        if ver:
            emit("camoufox_pkg", "OK", ver)
        else:
            errln = (r.stderr or "").strip().splitlines()
            emit("camoufox_pkg", "FAIL", errln[-1] if errln else "pip install failed")
            required_ok = False
    else:
        emit("camoufox_pkg", "MISSING", "run with --install, or: pip install -U camoufox[geoip]")
        required_ok = False

    # 2) camoufox browser binary (required) -----------------------------------
    if ver:
        present, path = browser_status()
        if present:
            emit("camoufox_browser", "OK", path or "")
        elif args.install:
            emit("camoufox_browser", "FETCHING")
            r = run([PY, "-m", "camoufox", "fetch"])
            present, path = browser_status()
            if present:
                emit("camoufox_browser", "OK", path or "")
            else:
                tail = (r.stderr or r.stdout or "camoufox fetch failed").strip().splitlines()
                emit("camoufox_browser", "FAIL", tail[-1] if tail else "camoufox fetch failed")
                required_ok = False
        else:
            emit("camoufox_browser", "MISSING", "run with --install, or: python3 -m camoufox fetch")
            required_ok = False
    else:
        emit("camoufox_browser", "SKIP", "camoufox package not installed yet")
        required_ok = False

    # 3) playwright-cli + skills (optional) -----------------------------------
    if not args.required_only:
        if shutil.which("playwright-cli"):
            emit("playwright_cli", "OK")
            if args.install:
                r = run(["playwright-cli", "install", "--skills"])
                emit("playwright_cli_skills", "OK" if r.returncode == 0 else "WARN",
                     "" if r.returncode == 0 else "run: playwright-cli install --skills")
        elif args.install and shutil.which("npm"):
            emit("playwright_cli", "INSTALLING")
            r = run(["npm", "install", "-g", "@playwright/cli@latest"])
            if shutil.which("playwright-cli"):
                run(["playwright-cli", "install", "--skills"])
                emit("playwright_cli", "OK")
            else:
                emit("playwright_cli", "WARN", "global npm install failed; try with sudo or a Node version manager")
        elif args.install:
            emit("playwright_cli", "WARN", "npm/Node not found — install Node.js, then: npm i -g @playwright/cli@latest && playwright-cli install --skills")
        else:
            emit("playwright_cli", "MISSING", "optional; --install needs npm. It does NOT drive Camoufox (see references/toolchain.md)")

    # 4) Xvfb on Linux (optional; only for headless="virtual") ----------------
    if not args.required_only and platform.system() == "Linux":
        if shutil.which("Xvfb"):
            emit("xvfb", "OK")
        else:
            emit("xvfb", "WARN", "needed only for headless='virtual'; install via your package manager (e.g. apt-get install -y xvfb)")

    print(f"RESULT: {'ok' if required_ok else 'fail'}")
    return 0 if required_ok else 1


if __name__ == "__main__":
    sys.exit(main())
