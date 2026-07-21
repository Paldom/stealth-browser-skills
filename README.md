# Stealth Browser Skills

[![CI](https://github.com/Paldom/stealth-browser-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/Paldom/stealth-browser-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![skills.sh](https://skills.sh/b/Paldom/stealth-browser-skills)](https://skills.sh/Paldom/stealth-browser-skills)

Agent Skills for stealthy, human-like browser automation with Playwright and Camoufox — real-browser agentic browsing that evades bot detection.

Agent Skills for [Claude Code](https://code.claude.com/docs/en/skills) (and any
[Agent Skills](https://agentskills.io)-compatible tool). Each skill is a folder under
[`skills/`](skills/) with a single-purpose `SKILL.md`, trigger evals, and optional
scripts/references — validated on every write, commit, and PR.

## Quick start

Install with the [skills CLI](https://skills.sh) — auto-detects 70+ agents
(Claude Code, Codex, Cursor, Copilot, pi, …):

```bash
npx skills add Paldom/stealth-browser-skills                  # all detected agents
npx skills add Paldom/stealth-browser-skills -a codex -a pi   # or target specific agents
```

Or with the [GitHub CLI](https://cli.github.com/manual/gh_skill_install) (≥ 2.90),
including version-pinned installs from releases:

```bash
gh skill install Paldom/stealth-browser-skills
gh skill install Paldom/stealth-browser-skills <skill> --pin <tag>
```

Or as a Claude Code plugin:

```
/plugin marketplace add Paldom/stealth-browser-skills
/plugin install stealth-browser-skills@stealth-browser-skills
```

Or copy a single skill into a project:

```bash
git clone https://github.com/Paldom/stealth-browser-skills.git
cp -r stealth-browser-skills/skills/<skill-name> your-project/.claude/skills/
```

Then just describe the task — the skill activates on its description — or invoke it
explicitly with `/<skill-name>`.

## Skills

A [Camoufox](https://github.com/daijro/camoufox) (anti-detect Firefox) + Playwright
stealth-browsing toolkit — two single-purpose skills:

| Skill | Description |
| --- | --- |
| [camoufox](skills/camoufox/) | The main entry point — open or resume a headful, human-like stealth session on a persistent profile (with an optional pinned identity for durable manual logins), drive the task, and self-verify it isn't detected. |
| [camoufox-setup](skills/camoufox-setup/) | Install & verify the toolchain — `camoufox[geoip]`, its Firefox binary (`camoufox fetch`), and the playwright-cli agent skills. |

**Typical flow:** `camoufox-setup` (once) → the **`camoufox`** skill drives the task
and verifies it. A paste-ready orchestration prompt is in
[docs/setup-prompt.md](docs/setup-prompt.md).

**Authorized use only.** These skills provide a real browser with human-like input
— capability-neutral technology for automating properties you own or are authorized
to test. See [docs/authorized-use.md](docs/authorized-use.md).

## Repository structure

```
skills/                  # distributed skills, one folder per skill (SKILL.md + evals/ + scripts/)
docs/                    # skill-authoring guide, eval methodology, deployment guide
scripts/                 # deterministic validator used by hooks and CI
skills.sh.json           # skills.sh repo-page customization (groupings)
.claude/                 # agentic dev setup: hooks + bundled add-skill / publish-repo skills
.claude-plugin/          # plugin + marketplace manifests (makes this repo installable)
.local/                  # gitignored working area: sources, research, PROMPT.md (see below)
```

## Working on this repo with an agent

This repo is agent-native: canonical agent instructions live in
[AGENTS.md](AGENTS.md) (CLAUDE.md imports it), hooks validate every `SKILL.md` on
write, `make check` runs the full validator, and CI enforces the same gate on every
PR. The bundled `add-skill` skill walks the eval-first authoring workflow described
in [docs/skill-authoring.md](docs/skill-authoring.md). Maintainers drive sessions
with their own (gitignored, personal) `.local/PROMPT.md` goal prompt.

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the skill-proposal
process, the authoring workflow, and the PR checklist. Please note the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Support

Questions, ideas, or something not working? Start with [SUPPORT.md](SUPPORT.md) —
bugs and skill proposals have [issue templates](../../issues/new/choose), and
security concerns go through [SECURITY.md](SECURITY.md) (never a public issue).

## License

[MIT](LICENSE) © 2026 Paldom
