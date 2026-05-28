from __future__ import annotations

import os
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from ._bnpm_runtime import plugin_python
from .session import GatewaySessionRegistry
from .transports import HttpTransport, StdioTransport

mcp = FastMCP("binja-codemode-mcp-gateway")
_sessions = GatewaySessionRegistry()
DEFAULT_HTTP_URL = "http://127.0.0.1:44044/mcp/"
HTTP_URL_ENV = "BINJA_CODEMODE_MCP_HTTP_URL"


@mcp.tool
async def create_session(
    transport: Annotated[
        Literal["http", "stdio"],
        Field(
            description=(
                "'http' connects to an already-running Binary Ninja MCP server "
                "at BINJA_CODEMODE_MCP_HTTP_URL. 'stdio' launches a dedicated "
                "worker process in the bnpm Binary Ninja environment."
            )
        ),
    ],
) -> dict:
    """Create a session. Env: BINJA_CODEMODE_MCP_HTTP_URL."""
    session_transport = _make_transport(transport)
    session = _sessions.add(
        transport=session_transport,
    )
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
                "Python code to execute. Print concise, filtered results; use "
                "dir/help/inspect for API discovery. Do not print full object "
                "dumps or large collections unless requested."
            )
        ),
    ],
) -> dict:
    """Execute code in a session.

    Prefer small scripts that print filtered summaries. Do not dump whole Binary
    Ninja objects or large collections unless explicitly requested.
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
    session = _sessions.remove(session_id)
    result = await session.transport.close()
    return {
        **result,
        "session_id": session.id,
    }


@mcp.tool
def list_sessions() -> dict:
    """List sessions."""
    return {"sessions": _sessions.list()}


def _make_transport(transport: str):
    if transport == "http":
        return HttpTransport(url=os.environ.get(HTTP_URL_ENV, DEFAULT_HTTP_URL))
    if transport == "stdio":
        worker = plugin_python()
        return StdioTransport(
            command=str(worker.command),
            env=worker.env,
            cwd=str(worker.cwd),
        )
    raise ValueError(f"unsupported transport: {transport}")


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
