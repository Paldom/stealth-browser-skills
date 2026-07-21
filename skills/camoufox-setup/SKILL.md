---
name: camoufox-setup
description: Installs and verifies the Camoufox stealth-browser toolchain — the camoufox[geoip] pip package, its Firefox browser binary via `camoufox fetch`, and the playwright-cli agent skills. Use when Camoufox is missing or setup fails, e.g. 'set up camoufox', 'install the stealth browser', 'camoufox fetch failed'. Not for launching, resuming, serving, or detection-testing a browser.
---

# camoufox-setup

Get the [Camoufox](https://github.com/daijro/camoufox) stealth-browsing toolchain
installed and verified on this machine, idempotently: probe what is present, then
install only what is missing. Camoufox is an anti-detect **Firefox** fork driven
through Playwright; you install a pip package and then download its patched browser
binary separately.

**Authorized use only.** This toolchain is for automating sites you own or are
authorized to test, and for privacy-respecting browsing. Respect each site's Terms
of Service and `robots.txt`; do not use it for abuse, mass scraping, or evading
access controls you have no right to bypass. See
[references/toolchain.md](references/toolchain.md).

## When to use / when NOT to use

Use when the environment is missing or broken: Camoufox not importable, `camoufox
fetch` failing, a fresh machine, or "get the stealth env ready". **Not** for
running a browsing task or resuming a session — that is the `camoufox` skill.

## Workflow

Run everything through the bundled script — it is the deterministic gate.

1. **Probe first (no changes).** See what already exists before touching anything:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/setup_check.py"
   ```
   Read the `STATUS <component>: OK|MISSING|WARN` lines and the final `RESULT:`.
   `camoufox_pkg` and `camoufox_browser` are **required**; `playwright_cli` and
   `xvfb` are **optional** and never fail the run.

2. **Install what is missing.** Only if step 1 reported `MISSING`/`fail`:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/setup_check.py" --install
   ```
   This runs `pip install -U camoufox[geoip]`, then `python3 -m camoufox fetch`,
   and (if `npm` is present) `npm i -g @playwright/cli@latest && playwright-cli
   install --skills`. Add `--required-only` to skip playwright-cli and Xvfb.

3. **Verify.** Re-run step 1; require `RESULT: ok`. Report the resolved package
   version and the browser install path. **Do not launch a browser here.**

If a required step fails, read the `FAIL` detail and fix the root cause
(network/proxy for `fetch`, disk space, permissions) — never fake success. Full
troubleshooting and platform notes are in
[references/toolchain.md](references/toolchain.md).

## What "done" looks like

- `setup_check.py` prints `STATUS camoufox_pkg: OK <ver>`,
  `STATUS camoufox_browser: OK <path>`, and `RESULT: ok` (exit 0).
- You reported the version and browser path and made no other changes.

## Gotchas

- **`geoip` extra is not optional for locale coherence.** `geoip=True` at launch
  needs the `[geoip]` extra (a MaxMind DB, pulled by `camoufox fetch`). Installing
  plain `camoufox` and later passing `geoip=True` fails or leaks a mismatched
  locale. Always install `camoufox[geoip]`.
- **playwright-cli drives Camoufox by *launching* it, not attaching (tested).** Its
  `attach --cdp` is Chromium-only and `attach --endpoint` fails on a Camoufox server
  (`no contexts`). But feeding Camoufox's `launch_options()` into playwright-cli's
  config (`browser.launchOptions`) makes `playwright-cli open --browser firefox
  --config <f>` launch a fully stealthed Camoufox — verified `navigator.webdriver`
  false and the spoofed fingerprint intact. The `camoufox` skill's `pwcli_config.py`
  generates that config. In-process/server driving still uses the Playwright API
  (`Camoufox(...)` / `firefox.connect`). See references/toolchain.md.
- **`headless="virtual"` needs Xvfb (Linux only).** The setup script warns if
  Xvfb is absent; install it (`apt-get install -y xvfb` or your package manager)
  only if you intend to run the virtual display. macOS/Windows ignore this.
- **Camoufox self-labels "under development … may not be suitable for stable
  production use."** Pin a channel for reproducibility (`python3 -m camoufox set
  official/stable` then `fetch`) and re-run the `camoufox` skill's built-in
  verification after any Camoufox or Firefox update — stealth properties drift
  between versions.
- **Cleanup / disk:** the browser binary is large. Remove it with `python3 -m
  camoufox remove` if you need the space back.

## References

- [references/toolchain.md](references/toolchain.md) — install matrix, the
  playwright-cli boundary, Xvfb, GeoIP, channel pinning, cleanup, and the
  authorized-use policy in full.
