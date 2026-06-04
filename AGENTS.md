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
- One logical change per commit
- Use Conventional Commits, such as `feat(server): expose execute tool over MCP`
- Use `!` or `BREAKING CHANGE:` for breaking public API changes
