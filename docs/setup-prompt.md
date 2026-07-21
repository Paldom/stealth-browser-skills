# Setup prompt — stand up a verified stealth browser

A paste-ready `/goal` that orchestrates the skills in order, with a verifier gate at
each stage. Replace `<YOUR AUTHORIZED TASK>` and paste into a session with these
skills installed (or run from inside this repo). It performs **no git actions**.

Order: `camoufox-setup` (once) → the **`camoufox`** skill drives the task and runs
its built-in verification; use `--pin-identity` when you need a manual login to
survive across agent turns. Each skill runs its own bundled script via
`${CLAUDE_SKILL_DIR}`; the gates below key off each script's `RESULT:` line, so
they work whether the skills are installed or run in-repo.

```
/goal Stand up a verified, human-like Camoufox stealth browser and use it for <YOUR AUTHORIZED TASK on a site you OWN or are AUTHORIZED to test>. Work autonomously; stop only if a stage's verifier fails twice.

Rules: authorized targets only — honor Terms of Service and robots.txt; no fraud, credential abuse, mass account creation, or evading defenses on services you do not control. Never run git commit or git push.

1) SETUP — use the camoufox-setup skill. Run its setup_check.py; if any REQUIRED component is MISSING, re-run with --install. GATE: a clean re-run prints "RESULT: ok". (Linux + headless='virtual' only: also ensure Xvfb is installed.)

2) RUN THE TASK — use the camoufox skill. First run launch.py --check --profile ./.camoufox-profile (GATE: "RESULT: ok" and profile not locked; if it reports Camoufox missing, do step 1 first). Then drive from code: Camoufox(persistent_context=True, user_data_dir="./.camoufox-profile", headless=False, humanize=True, os="<real host OS>"). Reuse the SAME user_data_dir to RESUME. With a proxy add geoip=True (or set locale/timezone) so timezone/locale match the egress IP. One profile per identity. Act human: pace actions, scroll with page.mouse.wheel (never JS scrollTo/scrollBy), type with keyboard events; don't rotate IP mid-session on a logged-in profile.

3) VERIFY (built into the camoufox skill) — BEFORE trusting the browser on the target, run canary.py. GATE: "RESULT: ok" — every required canary passes. For any [FAIL], apply the failure→fix table in the skill's detection-tools reference and re-run. Re-run after any Camoufox/Firefox update.

OPTIONAL — reuse a manual login: to log in by hand first, run launch.py --pin-identity --profile ./accounts/x --os <host OS> headful, log in, close; then have the agent relaunch with the SAME --pin-identity --profile so it is the same device + same cookies. (A plain persistent profile keeps cookies but re-rolls the fingerprint — the agent would look like a new device.) Use a sticky proxy + geoip for both steps if the site is IP-sensitive.

Deliverable: the task completed via the verified stealth browser, the canary scorecard, and any [WARN] advisories with how you handled them. Report exactly what changed. Zero git commits or pushes.
```

## Notes

- **Camoufox is under active development** and self-labels "may not be suitable for
  stable production use." Pin a channel for reproducibility
  (`python3 -m camoufox set official/stable` then `python3 -m camoufox fetch`) and
  lean on the built-in `camoufox` verification as your regression gate.
- **Authorized use only** — the full policy is in
  [authorized-use.md](authorized-use.md).
- The local canaries are a floor, not a guarantee: live commercial walls also score
  network fingerprints (JA3/JA4) and behaviour over a whole session.
