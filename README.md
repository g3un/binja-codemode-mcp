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
claude mcp add binja-codemode-mcp --scope user -- uv run --directory /path/to/binja-codemode-mcp binja-codemode-gateway
codex mcp add binja-codemode-mcp -- uv run --directory /path/to/binja-codemode-mcp binja-codemode-gateway
```

For an `http` session, start a Binary Ninja MCP HTTP server first. In the GUI,
use `Binja Codemode MCP\Start`. In a headless environment, use a Python that
can import Binary Ninja and run:

```bash
uv run --directory /path/to/binja-codemode-mcp binja-codemode-http
```

Then create an `http` session from the agent. Create a `stdio` session to
launch a dedicated worker process instead. Headless Binary Ninja requires
Binary Ninja Commercial or higher.

## Environment

- `BINJA_CODEMODE_MCP_HTTP_URL`: MCP HTTP endpoint used by gateway `http`
  sessions. Defaults to `http://127.0.0.1:44044/mcp/`.
- `BINJA_CODEMODE_MCP_PYTHON`: Python executable used by gateway `stdio`
  sessions. Defaults to the Python running the gateway.
- `BINJA_CODEMODE_MCP_INSECURE_BIND`: set to `1` in the Binary Ninja process
  running the HTTP server to allow binding to a non-loopback host.
