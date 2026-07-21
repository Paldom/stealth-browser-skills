# Configuring Camoufox for coherence and human-like interaction

Principle-level guidance distilled from anti-bot research (2026), with specific
numbers flagged as tunable heuristics, not thresholds.

**Contents:** [Coherence is the master signal](#coherence-is-the-master-signal) ·
[Camoufox knobs that matter](#camoufox-knobs-that-matter) ·
[Human-like interaction](#human-like-interaction) ·
[Profiles & identity hygiene](#profiles--identity-hygiene) ·
[Authorized use](#authorized-use)

## Coherence is the master signal

Modern anti-bot systems score the *joint consistency* of many signals across three
layers — network (TLS JA3→JA4, HTTP/2 SETTINGS, negotiated before any JS runs),
browser runtime (canvas/WebGL/fonts/navigator), and session state — rather than
hunting one "tell." A **mismatched combination** is a stronger signal than any
single spoofed value left at its default. Canonical seams to avoid:

- A US IP with a non-US `timezone`/`locale`.
- A Chrome user-agent over a non-Chrome TLS stack (not your concern with Camoufox,
  which ships a real Firefox stack — keep it Firefox end to end; don't spoof a
  Chrome UA onto it).
- A "Windows + NVIDIA" claim whose canvas/WebGL renders through a Linux software
  renderer (SwiftShader/llvmpipe).

The takeaway: build **one coherent persona** and hold it stable for the whole
session. Prefer seeded/deterministic settings (stable within a profile) over
per-call randomization — naive randomness is itself a signature.

## Camoufox knobs that matter

| Goal | Setting | Why |
| --- | --- | --- |
| Match geography to proxy | `geoip=True` (needs `[geoip]` extra) | Derives lat/long/timezone/country/locale from the egress IP so they agree. |
| Explicit locale fallback | `locale="en-US"`, and set timezone via geoip | Use when geoip data is unavailable, so nothing is left mismatched. |
| Plausible OS | `os="windows"` (or the real host OS) | Stack traces can leak the true OS; keep the claim consistent with it. |
| Real headful surface | `headless=False` (or `"virtual"` on Linux) | Headless is easier to fingerprint; virtual display keeps it headful without a screen. |
| Consistent fingerprint | `fingerprint_preset` / let Camoufox generate | Engine-level (C++) generation is internally consistent; avoid hand-spoofing single values. |
| Sticky egress | one proxy for the whole session | Mid-session IP change on a logged-in profile is itself an anomaly. |

Avoid `main_world_eval` unless required — code run in the main world is detectable
by the page (prefix `mw:` opts in deliberately). Do not over-strip (blank canvas,
empty plugins) — "too clean" reads as headless too.

## Human-like interaction

`humanize=True` handles cursor trajectories only. Everything else is on you, and
the durable rule is **cross-modal session consistency**, not any single perfect
gesture. Concrete, checkable rule:

- **Scroll with real wheel input**: `page.mouse.wheel(0, dy)`. JS `scrollTo`/
  `scrollBy` emit a `scroll` event with `isTrusted: false` and **no** underlying
  `wheel` event — a binary bot tell.
- Space out actions; include reading/thinking pauses and occasional idle time. A
  session that is productive every second is inhuman.
- Type via Playwright input (`page.keyboard`/`locator.press_sequentially`) rather
  than setting values directly; vary rhythm, don't use a fixed delay.

**Heuristics, not thresholds (do not hardcode as pass/fail).** Figures cited in
blogs/repos — mouse ~300–900 px/s, ~30% overshoot, keystroke dwell ~60–130 ms,
flight ~50–200 ms, ~4% long "distraction" pauses — are illustrative shape
parameters from non-peer-reviewed sources. Treat them as tunable knobs with a
calibration dial, and validate behavior with the built-in detection check, never as
fixed constants.

Context: continuous session-level behavioral scoring is a real 2026 trend (e.g.
Cloudflare's Precursor). Its general design is well documented; granular mechanics
(tremor-frequency analysis, mid-session revocation) are weakly sourced — do not
build around specific unverified mechanics.

## Profiles & identity hygiene

- One `user_data_dir` per identity/account. Reusing one aged profile across
  accounts links them.
- A brand-new "blank slate" (fresh profile + clean proxy + immediate signup) is
  itself a heuristic flag; real users arrive with history. Warm a profile with
  ordinary browsing before high-stakes actions when it matters.
- The profile stores real cookies/sessions unencrypted — protect it like a
  credential (restrictive permissions, not shared `/tmp`, not committed).

## Authorized use

Real browser + human-like input is capability-neutral technology. Use it only on
properties you own or are authorized to test, and for lawful, privacy-respecting
browsing. Honor Terms of Service and `robots.txt`; do not defeat access controls
you have no right to bypass or use it for fraud, credential abuse, mass account
creation, or denial-of-service. You are responsible for how you use it.
