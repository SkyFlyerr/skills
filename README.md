# Open Agent Skills

Reusable skills, scripts, and workflow patterns for coding agents.

This is a public subset of battle-tested agent workflows: small enough to copy,
specific enough to be useful, and documented so another builder can run them
without inheriting a private workspace.

## Published Skills

| Skill | What it does | Status |
| --- | --- | --- |
| [`mcp-client`](skills/mcp-client/) | Inspect and call MCP servers from a lightweight CLI instead of loading every tool schema into context upfront. | Ready |

## Release Principles

- One skill per release.
- Each release includes a README, demo path, examples, and an agent-facing `SKILL.md`.
- Skills must be portable: no private paths, tokens, accounts, or internal services.
- Scripts should be boring and inspectable. The agent instructions should explain when to use them, not hide the implementation.

## Repository Layout

```text
skills/
  mcp-client/
    README.md
    SKILL.md
    scripts/
    examples/
    docs/
assets/
  threads/
```

## Roadmap

- `video-analyze`: turn videos into transcripts, frames, and structured scene JSON.
- `sop-creator`: templates and instructions for practical runbooks and operating docs.
- `pptx-generator`: reusable slide cookbook and brand-aware deck generation.
- `gitlab-project-manager`: GitLab-first task routing and session tracking.

## License

MIT.
