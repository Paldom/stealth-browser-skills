# Changelog

All notable changes to this repository's skills are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning: [SemVer](https://semver.org) on the plugin manifest
(breaking skill-interface change → major, new skill → minor, fix → patch).

## [Unreleased]

### Added
- Repository scaffolded from the skills template.
- **camoufox** — the main entry point: open or resume a headful, human-like Camoufox
  session on a persistent `user_data_dir` (resume = relaunch same profile), drive the
  task, and self-verify it isn't detected. Bundles a preflight / profile-lock guard
  (`launch.py`) and a Firefox-tuned automation-leak canary (`canary.py`, with a
  browser-free scoring self-test), plus coherence/behaviour and detection references.
  Also ships `pwcli_config.py` — a bridge that lets **playwright-cli** drive a
  fully-stealthed Camoufox by launching it via a generated config — and
  `--pin-identity`, which freezes the fingerprint in the profile so a manual login
  can be reused across agent turns as the same device.
- **camoufox-setup** — idempotent install/verify of the Camoufox stealth toolchain
  (`camoufox[geoip]`, the `camoufox fetch` browser binary, a Linux Xvfb check, and
  the `playwright-cli install --skills` agent skills), with a machine-readable
  `setup_check.py`. Documents the tested playwright-cli↔Camoufox reality: `attach`
  can't (Playwright server has no contexts), but `open --config` from
  `pwcli_config.py` launches a stealthed Camoufox.
- **docs/setup-prompt.md** — paste-ready `/goal` orchestrating the skills.
- **docs/authorized-use.md** — shared authorized-use / dual-use policy.

### Notes
- The detection eval is folded into the `camoufox` skill as a built-in verification
  step (no longer a standalone skill). Live-tested against real Camoufox 0.5.4.
- **`camoufox-server` was dropped** (advise-max-unanimous): a Playwright WS server
  hands each client an isolated, ephemeral context, so it never shared a session or
  profile — and playwright-cli can't attach. Its niche (multi-process/cross-language
  `firefox.connect`) and an MCP-host pointer are folded into the `camoufox` skill.
- playwright-cli↔Camoufox: `attach` is impossible (a Playwright server exposes no
  contexts, `--cdp` is Chromium-only), but launching Camoufox via playwright-cli's
  `browser.launchOptions` works with stealth intact — verified live
  (`navigator.webdriver=false`, spoofed fingerprint). `pwcli_config.py` automates it.
- **Fingerprint pinning** — a persistent profile carries cookies but Camoufox
  re-rolls the fingerprint per launch (verified); `--pin-identity` reuses a saved
  launch config so canvas/WebGL/screen/cores stay constant (verified) — needed for a
  durable manual-login identity.
