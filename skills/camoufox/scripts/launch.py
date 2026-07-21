#!/usr/bin/env python3
"""Start or resume a headful, human-like Camoufox session on a persistent profile.

The persistent profile (user_data_dir) is what makes a session RESUMABLE: point
every run at the SAME directory and cookies/logins/localStorage survive restarts.
"Resume" is not a separate mode — it is just launching again with the same profile.

A persistent profile carries COOKIES, but by default Camoufox re-rolls the
FINGERPRINT (canvas/WebGL/screen/cores) every launch. For a durable identity — e.g.
log in to a social site by hand, then reuse the session agentically — that shift
looks like a new device and can trip re-verification. `--pin-identity` freezes the
fingerprint (stored in the profile) so the device stays constant across launches,
while keeping humanize (it reuses the saved Camoufox `config`, the author-endorsed
way to persist a fingerprint — daijro/camoufox#38).

Modes:
  --check          preflight only (prereqs + profile not locked); exit 0/1, no launch
  --smoke          launch headless, load about:blank, confirm a page, close (CI check)
  --pin-identity   stable fingerprint (stored in <profile>/.camoufox-identity.json);
                   pairs with --profile for a durable "same device + same cookies"
                   identity. Generate it behind the same proxy/region you'll reuse it
                   with (geo is frozen into the identity).
  (default)        launch and hold the browser open until Enter/Ctrl-C ("just start")

Firefox profiles are SINGLE-WRITER: opening a profile already in use by another
process corrupts it. This script refuses a locked profile unless --force.

Exit codes: 0 ok, 1 preflight/launch failure, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from importlib import metadata

# Firefox profile lock files (Linux/macOS use lock + .parentlock; Windows parent.lock).
LOCK_FILES = ("lock", ".parentlock", "parent.lock")
IDENTITY_FILE = ".camoufox-identity.json"  # pinned fingerprint, stored inside the profile


def profile_locked(profile: str) -> bool:
    return any(os.path.lexists(os.path.join(profile, n)) for n in LOCK_FILES)


def _launch_options(**kw) -> dict:
    try:
        from camoufox import launch_options
    except Exception:  # noqa: BLE001 - older/newer layout
        from camoufox.utils import launch_options
    return launch_options(**kw)


def _extract_config(env: dict) -> dict:
    """Reassemble Camoufox's fingerprint (CAMOU_CONFIG, possibly chunked _1/_2/…)."""
    keys = sorted((k for k in env if re.match(r"^CAMOU_CONFIG(_\d+)?$", k)),
                  key=lambda k: int(k.rsplit("_", 1)[-1]) if k.rsplit("_", 1)[-1].isdigit() else -1)
    return json.loads("".join(env[k] for k in keys)) if keys else {}


def _camoufox_version() -> str:
    try:
        return metadata.version("camoufox")
    except metadata.PackageNotFoundError:
        return "?"


def load_or_create_identity(profile: str, kw: dict) -> tuple[dict, str | None]:
    """Return (pinned_config, os) for a stable identity, stored in the profile.

    First call generates a fingerprint via launch_options(**kw), extracts its
    Camoufox `config` (the CAMOU_CONFIG payload) and saves it with the package
    version; later calls reuse it so the device stays identical. On a Camoufox
    version change the saved UA/config can be version-skewed — we warn rather than
    silently mix an old fingerprint with a newer binary.
    """
    ident = os.path.join(profile, IDENTITY_FILE)
    if os.path.isfile(ident):
        with open(ident, encoding="utf-8") as f:
            data = json.load(f)
        saved_ver, cur = data.get("camoufox_version"), _camoufox_version()
        if saved_ver and cur != "?" and saved_ver != cur:
            print(f"PREFLIGHT: identity pinned on camoufox {saved_ver} but {cur} is installed — "
                  f"UA/fingerprint may be version-skewed; regenerate (delete {ident}) if the site "
                  "flags it.", file=sys.stderr)
        return data.get("config") or {}, data.get("os")
    opts = _launch_options(**kw)
    config = _extract_config(opts.get("env", {}))
    os.makedirs(profile, exist_ok=True)
    with open(ident, "w", encoding="utf-8") as f:
        json.dump({"config": config, "os": kw.get("os"),
                   "camoufox_version": _camoufox_version()}, f, default=str)
    return config, kw.get("os")


def preflight(profile: str, force: bool) -> list[str]:
    problems: list[str] = []
    try:
        import camoufox  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - report any import failure
        problems.append(f"camoufox not importable ({exc}) — run camoufox-setup")
        return problems  # nothing else works without the package
    try:
        r = subprocess.run([sys.executable, "-m", "camoufox", "path"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        problems.append("could not run 'python -m camoufox path' (timeout or error) — run camoufox-setup")
        return problems
    path = (r.stdout or "").strip()
    try:
        fetched = r.returncode == 0 and path and os.path.isdir(path) and bool(os.listdir(path))
    except OSError:
        fetched = False
    if not fetched:
        problems.append("Camoufox browser binary not fetched — run camoufox-setup "
                        "(python3 -m camoufox fetch)")
    # ponytail: lock-file presence is a heuristic; stale locks exist — hence --force.
    if os.path.isdir(profile) and profile_locked(profile) and not force:
        problems.append(
            f"profile {profile!r} appears to be in use (lock file present); close the "
            "other Camoufox process, or pass --force if you are sure the lock is stale")
    return problems


def _drive(context, args, smoke: bool, profile: str) -> int:
    """Shared post-launch flow."""
    page = context.new_page()
    target = "about:blank" if smoke else args.url
    if target:
        page.goto(target)
    print(f"STATUS profile: {profile}")
    print(f"STATUS pages: {len(context.pages)}")
    print("RESULT: ok")
    if smoke:
        assert page is not None and len(context.pages) >= 1
        return 0
    print("Browser open. Press Enter (or Ctrl-C) to close.", file=sys.stderr)
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=None,
                    help="persistent user_data_dir (default: ./.camoufox-profile; a throwaway temp dir under --smoke)")
    ap.add_argument("--url", help="navigate here after launch")
    ap.add_argument("--headless", choices=["false", "true", "virtual"], default="false",
                    help="false=headful (default), virtual=Xvfb on Linux, true=headless")
    ap.add_argument("--os", dest="os_name", help="fingerprint OS; match the real host OS")
    ap.add_argument("--geoip", action="store_true",
                    help="align timezone/locale to the egress IP (needs the [geoip] extra)")
    ap.add_argument("--pin-identity", action="store_true",
                    help="freeze the fingerprint in the profile for a durable identity (keeps humanize)")
    ap.add_argument("--humanize-max", type=float, default=None,
                    help="max seconds of humanized cursor travel (default: on/True)")
    ap.add_argument("--no-humanize", action="store_true", help="disable cursor humanization")
    ap.add_argument("--force", action="store_true", help="open even if the profile looks locked")
    ap.add_argument("--check", action="store_true", help="preflight only, do not launch")
    ap.add_argument("--smoke", action="store_true", help="headless open of about:blank, then close")
    args = ap.parse_args()

    # --smoke uses a throwaway temp profile (unless one is named) so it never touches
    # a real session, and it does NOT bypass the single-writer lock check.
    smoke_tmp = None
    if args.smoke and not args.profile:
        import tempfile
        smoke_tmp = tempfile.mkdtemp(prefix="camoufox-smoke-")
        profile = smoke_tmp
    else:
        profile = os.path.abspath(args.profile or "./.camoufox-profile")
    problems = preflight(profile, args.force)
    for p in problems:
        print(f"PREFLIGHT: {p}", file=sys.stderr)
    if problems:
        print("RESULT: fail")
        return 1
    if args.check:
        print(f"STATUS profile: {profile}")
        print(f"STATUS identity: {'pinned' if args.pin_identity else 'fresh per launch'}")
        print("RESULT: ok")
        return 0

    headless = {"false": False, "true": True, "virtual": "virtual"}[args.headless]
    if args.smoke:
        headless = True
    humanize: object = True
    if args.no_humanize:
        humanize = False
    elif args.humanize_max is not None:
        humanize = args.humanize_max
    os.makedirs(profile, exist_ok=True)

    kwargs = dict(persistent_context=True, user_data_dir=profile,
                  headless=headless, humanize=humanize)
    if args.pin_identity:
        # Reuse a saved Camoufox `config` through the wrapper: pins the fingerprint AND
        # keeps humanize (geo is frozen in the config — generate behind your reuse proxy).
        lo_kw: dict = {"headless": headless if isinstance(headless, bool) else False}
        if args.os_name:
            lo_kw["os"] = args.os_name
        if args.geoip:
            lo_kw["geoip"] = True
        config, os_used = load_or_create_identity(profile, lo_kw)
        print(f"STATUS identity: pinned ({os.path.join(profile, IDENTITY_FILE)})")
        if config:
            kwargs["config"] = config
            kwargs["i_know_what_im_doing"] = True  # intentional: reusing a saved fingerprint
            if os_used:
                kwargs["os"] = os_used
        else:
            print("PREFLIGHT: could not extract a fingerprint to pin — falling back to a fresh one",
                  file=sys.stderr)
    else:
        if args.os_name:
            kwargs["os"] = args.os_name
        if args.geoip:
            kwargs["geoip"] = True

    try:
        from camoufox.sync_api import Camoufox
        with Camoufox(**kwargs) as context:
            return _drive(context, args, args.smoke, profile)
    except Exception as exc:  # noqa: BLE001 - surface launch failure to the agent
        print(f"LAUNCH-ERROR: {exc}", file=sys.stderr)
        print("RESULT: fail")
        return 1
    finally:
        if smoke_tmp:
            import shutil
            shutil.rmtree(smoke_tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
