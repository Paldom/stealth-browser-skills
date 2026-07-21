# Authorized use

These skills drive a **real browser with human-like input** — the same capability
a person has with Firefox, automated. That is deliberately capability-neutral
technology with legitimate uses: testing your own sites' bot defenses, QA and
monitoring of properties you operate, privacy-respecting automation, accessibility
and compatibility testing, and authorized security research.

## Use them only when all of these hold

- **You own the target, or are explicitly authorized to test it** (a contract, a
  bug-bounty scope, a written engagement, or it's your own infrastructure).
- **You honor the site's Terms of Service and `robots.txt`**, and any rate limits
  or access rules that apply to you.
- **You are not defeating an access control you have no right to bypass** — paywalls,
  authentication, licensing, or geo-restrictions you aren't entitled to circumvent.

## Do not use them for

- Fraud, payment or credential abuse, account takeover, or mass account creation.
- Scraping in violation of terms, or at volumes that degrade a service
  (denial-of-service).
- Evading bans or bot defenses on services you don't control, to abuse them.
- Harassment, disinformation, or any unlawful activity.

## Notes

- **Stealth ≠ permission.** Looking human to a detector does not make an
  unauthorized action authorized. The detection-eval skill measures leaks; it is
  not a license to bypass a specific site's protection.
- **Session state is sensitive.** Persistent profiles and server endpoints hold
  live cookies and logins — treat them as credentials (restrictive permissions, not
  shared directories, never committed, never exposed on the network).
- **You are responsible for how you use these skills.** The maintainers provide
  them for lawful, authorized use only.
