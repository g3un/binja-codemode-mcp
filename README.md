# Binja Codemode MCP

A codemode MCP for Binary Ninja:
- Provide an `execute(code)` tool for arbitrary Python execution instead of
  wrapping selected Binary Ninja APIs.
- Let agents discover, filter, and call available APIs from inside the Python
  interpreter.
- Leave sandboxing and permission control to the MCP server side.

## Installation

Install the Binary Ninja GUI plugin with
[bnpm](https://codeberg.org/g3un/bnpm):

```bash
bnpm add binja-codemode-mcp --git https://codeberg.org/g3un/binja-codemode-mcp
```

Use the plugin directory installed by `bnpm` as `/path/to/binja-codemode-mcp`
in all commands below. The default install path is:

- macOS/Linux: `~/.local/share/bnpm/plugins/binja-codemode-mcp`
- Windows: `%LOCALAPPDATA%\bnpm\plugins\binja-codemode-mcp`

### MCP server

Register the gateway MCP server with an MCP-capable agent:

```bash
# Claude Code
claude mcp add binja-codemode-mcp --scope user -- uv run --directory /path/to/binja-codemode-mcp gateway

# Codex CLI
codex mcp add binja-codemode-mcp -- uv run --directory /path/to/binja-codemode-mcp gateway
```

Or add via JSON config:

```json
{
  "mcpServers": {
    "binja-codemode-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/binja-codemode-mcp", "gateway"]
    }
  }
}
```

### Agent Skill

Install the bundled Agent Skill to teach your agent Binary Ninja analysis
workflows and safety guidelines:

```bash
# pi
pi install /path/to/binja-codemode-mcp

# Claude Code, user-wide
mkdir -p ~/.claude/skills
ln -s /path/to/binja-codemode-mcp/skills/binja-codemode-mcp ~/.claude/skills/binja-codemode-mcp

# Codex CLI, user-wide
mkdir -p ~/.agents/skills
ln -s /path/to/binja-codemode-mcp/skills/binja-codemode-mcp ~/.agents/skills/binja-codemode-mcp
```

For project-local skill installs, use `.claude/skills/` for Claude Code or
`.agents/skills/` for Codex CLI instead. Copy the skill directory instead of
symlinking if preferred.

## Usage

Choose a session transport depending on how you want the agent to reach
Binary Ninja:

- `stdio`: launches a dedicated headless Binary Ninja worker process for the
  session. This is the normal headless mode and does not require a separate
  HTTP server.
- `http`: connects to an already-running Binary Ninja MCP HTTP server. Use this
  when you want to attach to the GUI process, or when you specifically want to
  expose a headless Binary Ninja process over HTTP.

For an `http` session from the GUI, start the server with
`Binja Codemode MCP\Start`. The generated bearer token is logged and can be
shown again with `Binja Codemode MCP\Show Auth Token`. The GUI plugin also adds
Binary Ninja settings for the HTTP bind address (`host:port`) and autostart.

For an `http` session from a headless environment, use a Python that can import
Binary Ninja and run:
```bash
uv run --directory /path/to/binja-codemode-mcp serve
```

Headless Binary Ninja requires Binary Ninja Commercial or higher.

Loopback binds do not require auth. Non-loopback binds generate and print an
auth token on startup. HTTP clients send it as `Authorization: Bearer <token>`;
for gateway sessions, pass `auth_token` to
`create_session(transport="http", auth_token="...")`.

## Environment

- `BINJA_CODEMODE_MCP_HTTP_URL`: MCP HTTP endpoint used by gateway `http`
  sessions. Defaults to `http://127.0.0.1:44044/mcp/`.
