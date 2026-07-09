# Binja Codemode MCP

An MCP bridge for running Python inside Binary Ninja.

The idea is simple: give the agent one `execute(code)` tool instead of wrapping
a pile of Binary Ninja APIs. The agent can inspect the API, filter results in
Python, and print the small bit of output it actually needs. Sandboxing and
permissions stay on the MCP/server side.

## Installation

Install the Binary Ninja GUI plugin with
[bnpm](https://codeberg.org/g3un/bnpm):

```bash
bnpm add binja-codemode-mcp --git https://codeberg.org/g3un/binja-codemode-mcp
```

The examples below use `/path/to/binja-codemode-mcp` for the plugin directory
that `bnpm` installs. By default that is:

- macOS/Linux: `~/.local/share/bnpm/plugins/binja-codemode-mcp`
- Windows: `%LOCALAPPDATA%\bnpm\plugins\binja-codemode-mcp`

### MCP server

Register the gateway MCP server with your agent:

```bash
# Claude Code
claude mcp add binja-codemode-mcp --scope user -- uv run --directory /path/to/binja-codemode-mcp gateway

# Codex CLI
codex mcp add binja-codemode-mcp -- uv run --directory /path/to/binja-codemode-mcp gateway
```

Or add it to a JSON config:

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

Install the bundled Agent Skill so the agent knows the Binary Ninja workflow
and the safety rules:

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

For project-local installs, use `.claude/skills/` for Claude Code or
`.agents/skills/` for Codex CLI. Copy the skill directory instead of symlinking
if that fits your setup better.

## Usage

Pick the transport that matches where Binary Ninja is running:

- `stdio`: starts a private headless Binary Ninja worker for the session. This
  is the usual headless mode and does not need a separate HTTP server.
- `http`: connects to a Binary Ninja MCP HTTP server that is already running.
  Use it to attach to the GUI process, or to a headless process that you exposed
  over HTTP on purpose.

For an `http` session from the GUI, start the server with
`Binja Codemode MCP\Start`. The plugin also adds settings for the HTTP bind
address (`host:port`) and autostart.

For an `http` session from a headless environment, use a Python that can import
Binary Ninja and run:

```bash
uv run --directory /path/to/binja-codemode-mcp serve
```

Headless Binary Ninja requires Binary Ninja Commercial or higher.

## Environment

- `BINJA_CODEMODE_MCP_HTTP_URL`: MCP HTTP endpoint for gateway `http` sessions.
  Defaults to `http://127.0.0.1:44044/mcp/`.
- `BINJA_CODEMODE_MCP_INSECURE_BIND`: set this in the Binary Ninja process only
  if you really want the HTTP server to bind to a non-loopback host.
