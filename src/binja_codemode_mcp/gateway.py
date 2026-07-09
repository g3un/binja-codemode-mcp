from __future__ import annotations

import os
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from ._bnpm_runtime import plugin_python
from .session import GatewaySessionRegistry
from .transports import HttpTransport, StdioTransport

INSTRUCTIONS = """\
Binary Ninja codemode MCP: run Python in a live Binary Ninja interpreter.
Only printed output comes back to the model. Do loops, filtering, and traversal
inside one execute() call, and print short summaries. Do not dump whole objects
or large collections. Use dir/help/inspect for API discovery.

Workflow:
1. create_session(transport): 'stdio' starts a private headless worker;
   'http' attaches to the user's running Binary Ninja, often the GUI process.
2. execute(session_id, code): stateful. Globals persist across calls, so load
   the binary once and reuse `bv`.
3. close_session(session_id) when done.

Safety: an 'http' session is shared. Treat the user's view and GUI as read-only:
no patching, renaming, comments, type edits, create_database, or GUI calls
(openFilename/closeTab/navigate/...) unless explicitly asked. `bn.load()` is a
safe private copy that is not shown in the GUI.
"""

mcp = FastMCP("binja-codemode-mcp-gateway", instructions=INSTRUCTIONS)
_sessions = GatewaySessionRegistry()
DEFAULT_HTTP_URL = "http://127.0.0.1:44044/mcp/"
HTTP_URL_ENV = "BINJA_CODEMODE_MCP_HTTP_URL"


@mcp.tool
async def create_session(
    transport: Annotated[
        Literal["http", "stdio"],
        Field(
            description=(
                "'http' connects to the Binary Ninja MCP server at "
                "BINJA_CODEMODE_MCP_HTTP_URL. 'stdio' starts a private worker "
                "in the bnpm Binary Ninja environment."
            )
        ),
    ],
    auth_token: Annotated[
        str | None,
        Field(description="Bearer token for http sessions, if the server requires one."),
    ] = None,
) -> dict:
    """Create a session. Uses BINJA_CODEMODE_MCP_HTTP_URL for http."""
    session_transport = _make_transport(transport, auth_token)
    session = _sessions.add(session_transport)
    return session.describe()


@mcp.tool
async def execute(
    session_id: Annotated[
        str,
        Field(description="Session id from create_session."),
    ],
    code: Annotated[
        str,
        Field(
            description=(
                "Python code to run. Print concise, filtered results; use "
                "dir/help/inspect for API discovery. Do not print full object "
                "dumps or large collections unless the user asks for them."
            )
        ),
    ],
) -> dict:
    """Execute code in a session.

    Prefer small scripts that print filtered summaries. Do not dump whole Binary
    Ninja objects or large collections unless the user asks for them.
    """
    session = _sessions.get(session_id)
    result = await session.transport.execute(code)
    return {
        **result,
        "session_id": session.id,
    }


@mcp.tool
async def close_session(
    session_id: Annotated[
        str,
        Field(description="Session id from create_session."),
    ],
) -> dict:
    """Close a session."""
    session = _sessions.get(session_id)
    result = await session.transport.close()
    _sessions.remove(session_id)
    return {
        **result,
        "session_id": session.id,
    }


@mcp.tool
def list_sessions() -> dict:
    """List sessions."""
    return {"sessions": _sessions.list()}


def _make_transport(transport: str, auth_token: str | None = None):
    if transport == "http":
        return HttpTransport(
            url=os.environ.get(HTTP_URL_ENV, DEFAULT_HTTP_URL),
            auth_token=auth_token,
        )
    if transport == "stdio":
        worker = plugin_python()
        return StdioTransport(
            command=str(worker.command),
            args=worker.args,
            env=worker.env,
            cwd=str(worker.cwd),
        )
    raise ValueError(f"unsupported transport: {transport}")


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
