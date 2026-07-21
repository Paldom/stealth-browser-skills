---
name: camoufox
description: Opens a headful, human-like Camoufox stealth browser on a persistent profile (logins survive restarts), drives the task, and self-verifies it isn't detected. Use whenever the user wants to browse, log in, or automate a site 'like a human', 'stealthily', or 'with camoufox' — 'open camoufox and go to X', 'resume my stealth session'. Not for installing the toolchain or running a browser server.
---

# camoufox

The main entry point: drive a task in a [Camoufox](https://github.com/daijro/camoufox)
stealth browser — **headful**, with a **persistent profile** and **humanized**
cursor motion — then verify it isn't leaking automation tells. Because the profile
lives on disk, **resuming is just launching again with the same `user_data_dir`**:
cookies, logins, and localStorage carry across restarts.

**Authorized use only.** Automate only sites you own or are authorized to test;
respect Terms of Service and `robots.txt`; no abuse, mass scraping, or bypassing
access controls you have no right to defeat. Details in
[references/config.md](references/config.md).

## When to use / when NOT to use

Use for any "do something in a stealth/human-like browser" task — open a page, log
in, fill a form, click through a flow, resume a saved session, or reuse a login you
made by hand. **Not** for installing the toolchain (that's `camoufox-setup`).

## Workflow

1. **Ensure setup.** Run the preflight; if it reports Camoufox missing or unfetched,
   run the **camoufox-setup** skill first, then retry (this skill installs nothing
   itself):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launch.py" --check --profile ./.camoufox-profile
   ```
2. **Drive the task from code.** With `persistent_context=True` the context manager
   yields a Playwright **BrowserContext**:
   ```python
   from camoufox.sync_api import Camoufox   # async: from camoufox.async_api import AsyncCamoufox

   with Camoufox(
       persistent_context=True,
       user_data_dir="./.camoufox-profile",  # SAME dir every run = resume
       headless=False,                        # headful; use "virtual" on headless Linux
       humanize=True,                          # human-like cursor motion (True or max-seconds float)
       os="windows",                           # match the REAL host OS
       # geoip=True,                           # align timezone/locale to the proxy IP
       # proxy={"server": "http://host:port", "username": "u", "password": "p"},
   ) as context:
       page = context.new_page()
       page.goto("https://example.com")
       # drive: page.click(...), page.mouse.wheel(0, 600), page.fill(...), ...
   ```
   Or just start it and hold it open (for hands-on use):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launch.py" --profile ./.camoufox-profile --url https://example.com
   ```
   Flags: `--headless virtual` (Xvfb on Linux), `--geoip`, `--os windows`,
   `--humanize-max 2.0`, `--no-humanize`, `--force` (open a stale-locked profile),
   `--smoke` (headless open/close pipeline check). Re-run with the same `--profile`
   to **resume**; use a *different* directory per identity/account (one profile
   links everything done in it).
3. **Verify (built-in).** Before trusting the session on a real target, run the
   internal detection check:
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/canary.py"                 # ephemeral check (add --headless true for CI)
   python3 "${CLAUDE_SKILL_DIR}/scripts/canary.py" --ws ws://localhost:PORT/PATH   # a running Camoufox server
   ```
   It asserts the local automation-leak canaries (`navigator.webdriver`, CDP/`cdc_`
   leaks, software WebGL, unstable canvas hash, UA seams, untrusted scroll) and
   prints a scorecard; `RESULT: ok` (exit 0) means no required tell. On any `[FAIL]`,
   see the fix table in
   [references/detection-tools.md](references/detection-tools.md), then re-run.

## Optional: drive with playwright-cli (token-efficient)

playwright-cli (Microsoft's low-token agent browser CLI) can't *attach* to a
Camoufox server — a Playwright server has no contexts to attach to — but it can
*launch* Camoufox directly and give you its snapshot/ref commands against a fully
stealthed browser. Camoufox's `launch_options()` are exactly Playwright launch
options, so we feed them into playwright-cli's config. Verified live:
`navigator.webdriver`=false and Camoufox's spoofed fingerprint survive.

```bash
# 1. Regenerate the config EVERY run (fresh fingerprint) — never a static file:
python3 "${CLAUDE_SKILL_DIR}/scripts/pwcli_config.py" --out .playwright/cli.config.json --os windows   # + --geoip / --proxy http://host:port
# 2. Launch + drive (Linux: prefix `xvfb-run -a`, keep headless off):
playwright-cli open https://example.com --browser firefox --config .playwright/cli.config.json -s stealth
# 3. Smoke-gate before trusting it — must be false:
playwright-cli eval "() => navigator.webdriver" -s stealth
playwright-cli snapshot -s stealth        # token-efficient page read (refs for click/type)
```

Endorsed as the correct path by three independent flagship models; treat it as the
supported pattern, not a hack. Non-negotiable caveats:

- **Regenerate per run and gitignore the config.** A frozen config pins one
  fingerprint — reused across sessions it is *more* detectable than baseline.
- **Version-pin both sides.** playwright-cli bundles its own Playwright; it must
  match Camoufox's (both currently 1.60). Re-run the smoke-gate after any upgrade of
  either — a mismatch breaks driving with cryptic protocol errors.
- **Lost via this path:** the runtime cursor-humanization (`humanize`) and profile
  persistence (every run is a fresh profile — no durable logins). For those, or for
  add-ons, drive via the Python API (step 2 above) instead.
- **Linux:** wrap with `xvfb-run -a … --config …` and keep `headless` off — the
  `virtual` display is a Python-wrapper feature and isn't in the config.

Requires playwright-cli (`camoufox-setup`).

## Reuse a manual login (durable identity)

To log into a site by hand and then have the agent reuse that session, you need a
stable *device*, not just stable cookies. A persistent profile carries cookies, but
Camoufox re-rolls the fingerprint each launch (verified: canvas/WebGL/screen/cores
all change) — to a site that fingerprints your session, the agent's turn looks like
a new device and can trigger re-verification. `--pin-identity` freezes the
fingerprint in the profile so the device stays constant.

Under the hood it reuses the saved Camoufox `config` through the wrapper (the
author-endorsed way to persist a fingerprint), so `humanize` and add-ons still work.

1. **Log in by hand** (headful, pinned identity + persistent profile):
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/launch.py" --pin-identity --profile ./accounts/example --os windows --url https://example.com/login
   ```
   Log in in the window, then close it. The fingerprint is saved to
   `./accounts/example/.camoufox-identity.json`; cookies live in the profile.
2. **Agent reuse** — relaunch (or drive in code) with the same `--pin-identity
   --profile ./accounts/example`: same device + same cookies → the session holds.

**For a durable *social* login, the fingerprint is only half of it** — risk engines
weight the network as heavily as the device. Keep constant across login and reuse:

- **A sticky IP (residential/mobile proxy)** — the #1 trigger. Login and every agent
  run must egress from the same IP/region; a datacenter IP or country hop forces
  re-verification. Easiest if the agent runs on the same machine as the manual login.
- **`--geoip` at generation** so timezone/locale/`Accept-Language` match that IP (the
  values are then frozen in the identity — generate behind the proxy you'll reuse).
- **No WebRTC leak** (Camoufox blocks/spoofs it; a leaked real IP defeats everything).
- **Same Camoufox version and same launch mode** (headful↔headless shifts some
  signals). The script warns if the identity was pinned on a different Camoufox
  version — regenerate if the site flags it.

One identity + profile per account (never share a fingerprint across accounts — it
links them). The profile + identity file together are full session-takeover material
— treat them as credentials (restrictive perms, gitignored, never shared). Sessions
still expire server-side; pinning cuts re-verification, it doesn't make logins
immortal.

## Advanced: share a live browser, or use an MCP host

- **One browser, many processes/languages.** To keep a Camoufox browser alive for
  several scripts (or a non-Python client) to drive concurrently, run `python3 -m
  camoufox server` and connect with `playwright.firefox.connect(ws)` (Python) or
  `firefox.connect(ws)` from `playwright-core` (Node). It binds localhost with a
  random secret path — don't expose the port. Caveat: each `connect` client gets its
  own **isolated, ephemeral context**, so this does *not* share a logged-in session
  or a persistent profile across clients (use the manual-login recipe above,
  in-process). playwright-cli can't attach to it.
- **MCP hosts (no shell, e.g. desktop apps).** If you need MCP tools instead of a
  CLI, use an existing Camoufox MCP — e.g. `camoufox-mcp` (`uvx camoufox-mcp`) or
  `mcp-camoufox` — rather than this skill. Note they *randomize* fingerprints per
  session; for a durable manual-login identity, prefer the pinning recipe above.

## What "done" looks like

- The task ran in the browser, and the same `user_data_dir` reused later loads the
  persisted cookies/logins.
- `canary.py` reported `RESULT: ok` (every required check passed) before you relied
  on the session against the target.

## Gotchas

- **Single-writer profile.** Never open the same `user_data_dir` from two processes
  at once — it corrupts the profile. The launcher refuses a locked profile unless
  `--force`; only force when no other Camoufox is running.
- **`humanize` moves the cursor only** — not typing or scrolling. Scroll with real
  wheel input (`page.mouse.wheel(...)`), never JS `scrollTo`/`scrollBy` (those emit
  untrusted `scroll` events with no `wheel` — a documented bot tell).
- **Coherence beats spoofing.** With a proxy, set `geoip=True` (or explicit
  `locale`/`timezone`) so timezone/locale match the egress IP — a US IP with a
  non-US timezone is a classic seam. `os` must match the real host OS. Don't rotate
  IP mid-session on a logged-in profile.
- **Headful vs virtual.** `headless=False` is the default and strongest; on headless
  Linux use `headless="virtual"` (needs Xvfb). Avoid true `headless=True` where
  stealth matters.
- **The profile holds real secrets.** Cookies/logins are written unencrypted to
  `user_data_dir` — keep it out of shared dirs and version control, treat it like a
  credential.
- **Camoufox is under active development**; stealth drifts across versions. Re-run
  the built-in verification after any Camoufox/Firefox update.

## References

- [references/config.md](references/config.md) — coherence rules (network → runtime
  → session), human-like interaction, per-account profile hygiene, authorized use.
- [references/detection-tools.md](references/detection-tools.md) — the verification
  canaries, the failure→fix table, and optional external detection suites.
