# Binja Codemode MCP

A codemode MCP for Binary Ninja:
- Provide an `execute(code)` tool for arbitrary Python execution instead of
  wrapping selected Binary Ninja APIs.
- Let agents discover, filter, and call available APIs from inside the Python
  interpreter.
- Leave sandboxing and permission control to the MCP server side.

## Usage

Install the Binary Ninja GUI plugin with
[bnpm](https://codeberg.org/g3un/bnpm):

```bash
bnpm add binja-codemode-mcp --git https://codeberg.org/g3un/binja-codemode-mcp
```

Register the gateway MCP server with your agent:
```bash
# Replace /path/to/binja-codemode-mcp with the plugin checkout path.
# macOS/Linux: ~/.local/share/bnpm/plugins/binja-codemode-mcp
# Windows:     %LOCALAPPDATA%\bnpm\plugins\binja-codemode-mcp
claude mcp add binja-codemode-mcp --scope user -- uv run --directory /path/to/binja-codemode-mcp gateway
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

For an `http` session, start a Binary Ninja MCP HTTP server first. In the GUI,
use `Binja Codemode MCP\Start`. The GUI plugin also adds Binary Ninja settings
for the HTTP bind address (`host:port`) and autostart. In a headless
environment, use a Python that can import Binary Ninja and run:

```bash
uv run --directory /path/to/binja-codemode-mcp serve
```

Then create an `http` session from the agent. Create a `stdio` session to
launch a dedicated worker process in the bnpm Binary Ninja environment instead.
Headless Binary Ninja requires Binary Ninja Commercial or higher.

## Environment

- `BINJA_CODEMODE_MCP_HTTP_URL`: MCP HTTP endpoint used by gateway `http`
  sessions. Defaults to `http://127.0.0.1:44044/mcp/`.
- `BINJA_CODEMODE_MCP_INSECURE_BIND`: set to `1` in the Binary Ninja process
  running the HTTP server to allow binding to a non-loopback host.
