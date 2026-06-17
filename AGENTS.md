# Binja Codemode MCP: Agent Guide

## Coding Guidelines

- Do not introduce unnecessary code duplication; reuse existing data, helpers, types, and patterns where they already fit.
- Do not keep compatibility aliases, wrappers, or deprecated exports unless the user explicitly asks for backward compatibility.
- Do not implement features, behaviors, or abstractions that were not requested by the user.
- Do not add, change, or rely on environment variables unless the user explicitly asks for them.

## Development Tools

- Use `uv` for Python project management.

## Commits

- Do not create commits unless the user explicitly asks
- Do not bump the project version unless it is release/publish work or the user asks
- Use SemVer-compatible CalVer without leading zeroes: stable `YYYY.M.D` (`2026.6.17`), prerelease `YYYY.M.D-N` (`2026.6.17-0`)
- Do not create release tags unless the user explicitly asks; release tags must be `v${project.version}`
- One logical change per commit; use Conventional Commits, such as `feat(server): expose execute tool over MCP`
- Avoid overly granular scopes; use `!` or `BREAKING CHANGE:` for breaking public API changes
