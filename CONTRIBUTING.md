# Contributing

This repository is a curated collection of practical agent skills. The bar is
simple: each skill should help an agent do a real task with less context, less
guesswork, or safer execution.

## Skill Requirements

Every public skill should include:

- `README.md` with problem, quickstart, examples, limits, and dependencies
- `SKILL.md` with the agent-facing operating instructions
- `examples/` with at least one runnable or copyable example
- `scripts/` or `templates/` when the skill depends on executable helpers
- no private paths, credentials, account names, internal hosts, or workspace-only assumptions

## Review Checklist

Before publishing a skill:

- Run the documented quickstart in a clean shell.
- Search for secrets and private context.
- Replace local paths with relative paths or placeholders.
- Keep examples small enough to understand in one screen.
- Explain when the skill should not be used.

## Style

Prefer concrete workflow instructions over abstract prompt advice. If a skill
needs a script to be reliable, include the script instead of asking the agent to
recreate it from prose.
