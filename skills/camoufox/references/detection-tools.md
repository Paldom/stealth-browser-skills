# Detection & fingerprint test tools

Verified reachable/behavior as of 2026-07. Local canaries are the authoritative
gate; the sites below are optional evidence for human review.

**Contents:** [Local canary signals](#local-canary-signals) ·
[Self-serve endpoints](#self-serve-endpoints) ·
[Commercial walls](#commercial-walls-not-self-serve) ·
[Behavioral note](#behavioral-note) · [Authorized use](#authorized-use)

## Local canary signals

`canary.py` asserts these against the browser itself (no third party needed).
Tuned for Firefox/Camoufox.

**Required (a failure is a real tell):**

- `navigator.webdriver === false` — and inside iframes too.
- No automation globals: `cdc_*` (ChromeDriver), `__selenium`, `__webdriver`,
  `_phantom`, `callPhantom`, `domAutomation`.
- User-agent contains no `Headless`.
- Canvas hash **identical across two draws** — a per-call noise injector differs
  (and over-uniform/blank is the opposite "too clean" tell).
- Wheel input is `isTrusted` — real driver input is trusted; JS `scrollTo`/
  `scrollBy` produces untrusted `scroll` events with no `wheel`.

**Advisory (softer signals):**

- WebGL `UNMASKED_RENDERER` is a real GPU, not `SwiftShader`/`llvmpipe`/software.
- `navigator.languages` non-empty; consistent with `Accept-Language`.
- `hardwareConcurrency > 0` and plausible.
- UA OS token coherent with `navigator.platform`/`oscpu` (Chrome-UA-on-Linux is a
  seam — but with Camoufox keep the identity Firefox end to end).

## Reading failures → fixes

| Canary failure | Likely cause | Fix |
| --- | --- | --- |
| `navigator.webdriver` true / automation globals | not launched through Camoufox | launch via the `camoufox` skill (Camoufox patches `webdriver` to false) |
| canvas hash unstable | a per-call canvas-noise injector is active | remove stacked JS anti-fingerprint patches; let Camoufox handle canvas |
| UA has "Headless" / software WebGL | running headless | switch to `headless=False` or `"virtual"` (Xvfb) |
| UA/platform incoherent | spoofed OS mismatch | set `os` to the real host; align `geoip`/`locale` to the proxy |
| wheel input not trusted | scrolling via JS `scrollTo`/`scrollBy` | drive scroll with `page.mouse.wheel(...)` |

Local canaries are necessary, not sufficient: passing them means no obvious static
tell, but live commercial walls (Cloudflare, DataDome, Akamai, Kasada, HUMAN) also
score network fingerprints (JA3/JA4, HTTP/2) and behaviour over a whole session,
which one page load can't exercise. Re-run the check after any Camoufox/Firefox
update.

## Self-serve endpoints

Optional pages you can navigate to. "Machine-readable" ones expose a parseable
result; the rest are visual only (screenshot for human review).

| Tool | URL | Reads as |
| --- | --- | --- |
| Sannysoft / Intoli | `https://bot.sannysoft.com` | visual green/red table |
| CreepJS | `https://abrahamjuliot.github.io/creepjs` | visual trust % + lie list — **official GitHub Pages ONLY; other domains are honeypots** |
| BrowserScan bot detection | `https://www.browserscan.net/bot-detection` | visual verdict (Webdriver/UA/CDP/Navigator) |
| Brotector | `https://kaliiiiiiiiii.github.io/brotector/` | **machine-readable** ("copy as JSON" of detections) |
| Rebrowser bot-detector | `https://bot-detector.rebrowser.net/` | **machine-readable** (`#detections-json`; needs trigger calls) |
| bot.incolumitas | `https://bot.incolumitas.com/` | **machine-readable** `behavioralClassificationScore` 0→1 (needs interaction/time) |
| Fingerprint playground | `https://demo.fingerprint.com/playground` | bot signal JSON in the DOM |
| BotD (local lib) | `github.com/fingerprintjs/botd` | **machine-readable** JSON, runs fully client-side |
| deviceandbrowserinfo | `https://deviceandbrowserinfo.com/are_you_a_bot` | fingerprint bot verdict + API |
| BrowserLeaks | `https://browserleaks.com` (`/canvas`,`/webgl`,`/tls`,`/webrtc`) | raw values (incl. your JA3/JA4) — eyeball, not a verdict |

For an automated external check, prefer the machine-readable ones (Brotector,
rebrowser, incolumitas, BotD). Always pin CreepJS to the official URL.

## Commercial walls (not self-serve)

No neutral pass/fail page — the only signal is whether you reach content vs a
challenge/block. Test against a site that *uses* the vendor, not the vendor's
homepage, and only where you are authorized:

- **Cloudflare** Bot Management + Turnstile (JA3/JA4, HTTP/2, CDP; Precursor adds
  session-long behavioral scoring) — challenge page / `cf_clearance`, `__cf_bm`, 403.
- **DataDome** (TLS-first per-request ML) — challenge / `datadome` cookie / 403.
- **Akamai** Bot Manager — `_abck`/`bm_sz` cookies, sensor challenge.
- **Kasada** — `x-kpsdk-*` headers, 429.
- **HUMAN / PerimeterX** — `px`/`_px` cookies, block/CAPTCHA.

## Behavioral note

Static passes don't cover behavior. Session-level cross-modal consistency (mouse,
typing, scroll, dwell) is what continuous monitors score, and **naive
randomization is itself a signature**. Any specific px/s or millisecond figures are
directional heuristics — tune with a calibration knob, don't hardcode as
thresholds.

## Authorized use

These checks are for browsers you operate, against your own or authorized
properties. Honor Terms of Service and `robots.txt`; do not use the toolchain for
fraud, credential abuse, mass account creation, or denial-of-service. You are
responsible for how you use it.
