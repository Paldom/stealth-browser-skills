# Camoufox toolchain reference

Verified against primary sources (camoufox.com/python, github.com/daijro/camoufox,
pypi.org/project/camoufox) as of 2026-07. Re-check versions before pinning.

**Contents:** [Install matrix](#install-matrix) · [The playwright-cli boundary](#the-playwright-cli-boundary) ·
[Virtual display (Xvfb)](#virtual-display-xvfb) · [GeoIP](#geoip) ·
[Channel pinning & updates](#channel-pinning--updates) · [Cleanup](#cleanup) ·
[Project status](#project-status) · [Authorized use](#authorized-use)

## Install matrix

| Step | Command | Notes |
| --- | --- | --- |
| Python package | `pip install -U camoufox[geoip]` | Requires Python ≥ 3.10, < 4.0. The `[geoip]` extra pulls the MaxMind GeoLite2 DB used by `geoip=True`. |
| Browser binary | `camoufox fetch` (Windows) / `python3 -m camoufox fetch` (macOS, Linux) | Downloads the patched-Firefox build (large). Also pulls default add-ons and, with the extra, the GeoIP DB. |
| Verify | `python3 -m camoufox version` | Prints package + browser version, channel, install status. |
| Show install path | `python3 -m camoufox path` | Prints the browser data directory. |

The Camoufox CLI subcommands are: `active`, `fetch`, `gui`, `list`, `path`,
`remove`, `server`, `set`, `sync`, `test`, `version`.

License note: the pip package `camoufox` declares **MIT**; the browser build
(the `daijro/camoufox` Firefox fork) is **MPL-2.0**. Treat the shipped browser as
MPL-2.0.

## The playwright-cli boundary

`playwright-cli` (`@playwright/cli`, Microsoft — docs at
[playwright.dev/agent-cli](https://playwright.dev/agent-cli)) is a token-efficient
browser CLI with installable agent skills:

```bash
npm install -g @playwright/cli@latest      # verify: playwright-cli --help
playwright-cli install --skills            # install its agent skills
playwright-cli install-browser --with-deps # its own Chromium (NOT Camoufox)
```

**It can drive Camoufox — by LAUNCHING it, not attaching (all tested).**

*Attaching does not work.* `attach --cdp` is Chromium/CDP-only (can't attach a
Firefox). `attach --endpoint` connects to a Camoufox server but fails:

```
$ playwright-cli attach --endpoint=ws://localhost:PORT/PATH -s stealth
Error: unable to connect to a browser that does not have any contexts
```

A Playwright browser-server hands each connecting client its own isolated,
context-less browser, and playwright-cli's `attach` refuses one with no
pre-existing contexts (it won't call `newContext`). This held even with a context
open on another client; versions matched (both 1.60).

*Launching works.* playwright-cli's config takes Playwright `launchOptions`, and
Camoufox's `launch_options()` returns exactly those (executable path, args, env
fingerprint, Firefox prefs). Write them into `.playwright/cli.config.json` and
`playwright-cli open --browser firefox --config <f>` launches a fully stealthed
Camoufox — verified `navigator.webdriver=false` and the spoofed fingerprint intact.
The `camoufox` skill's `scripts/pwcli_config.py` generates the config:

```bash
python3 <camoufox skill>/scripts/pwcli_config.py --out .playwright/cli.config.json --os windows
playwright-cli open https://example.com --browser firefox --config .playwright/cli.config.json -s stealth
playwright-cli snapshot -s stealth
```

Trade-off vs the Python wrapper: the launch path drops `humanize` cursor motion (a
runtime feature); `--geoip`/`--proxy`/`--os` bake into the launch env and carry
over. The Playwright API path (`Camoufox(...)` in-process — the `camoufox` skill)
remains the way to get humanize/add-ons and a persistent, pinned identity.

## Virtual display (Xvfb)

`headless="virtual"` runs a *real headful* browser inside an Xvfb virtual display —
useful on headless Linux because some detectors catch true headless but miss a
virtual display. Xvfb is Linux-only and rarely preinstalled:

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y xvfb
# Fedora: sudo dnf install -y xorg-x11-server-Xvfb   |   Arch: sudo pacman -S xorg-server-xvfb
```

macOS and Windows do not use Xvfb; run truly headful there (`headless=False`).

## GeoIP

`geoip=True` derives longitude, latitude, timezone, country, and locale from the
outbound IP so those values agree with your proxy — a core coherence win (a US IP
with a non-US timezone is a classic detection seam). It needs the `[geoip]` extra
and the downloaded DB. If the DB is unavailable, either install the extra and
re-`fetch`, or set `locale=`/`timezone` explicitly to match your egress IP rather
than leaving them mismatched.

## Channel pinning & updates

Camoufox uses channels. For reproducible builds, pin one:

```bash
python3 -m camoufox set official/stable   # then: python3 -m camoufox fetch
```

Stealth behavior drifts across Camoufox and Firefox versions. After any update,
re-run the `camoufox` skill's built-in verification before trusting the browser again.

## Cleanup

```bash
python3 -m camoufox remove       # remove downloaded browser data (prompts)
python3 -m camoufox remove -y    # skip the confirmation
```

## Project status

The Camoufox README warns: "⚠️ This project is under development. It may not be
suitable for stable production use," and notes a prior maintenance gap plus known
fingerprint-consistency limitations. Plan for occasional breakage, pin versions,
and lean on the `camoufox` skill's built-in verification as your regression gate.

## Authorized use

These skills provide a real browser with human-like input — capability-neutral
technology. Use them only against properties you own or are authorized to test,
and for lawful, privacy-respecting browsing. Honor Terms of Service and
`robots.txt`, do not defeat access controls you have no right to bypass, and do
not use them for fraud, credential abuse, mass account creation, or
denial-of-service. You are responsible for how you use them.
