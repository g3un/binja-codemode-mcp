from __future__ import annotations

import os
import sys
from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from .session import GatewaySessionRegistry
from .transports import HttpTransport, StdioTransport

mcp = FastMCP("binja-codemode-mcp-gateway")
_sessions = GatewaySessionRegistry()
DEFAULT_HTTP_URL = "http://127.0.0.1:44044/mcp/"
HTTP_URL_ENV = "BINJA_CODEMODE_MCP_HTTP_URL"
PYTHON_ENV = "BINJA_CODEMODE_MCP_PYTHON"


@mcp.tool
async def create_session(
    transport: Annotated[
        Literal["http", "stdio"],
        Field(
            description=(
                "'http' connects to BINJA_CODEMODE_MCP_HTTP_URL; GUI uses http. "
                "'stdio' launches a worker."
            )
        ),
    ],
) -> dict:
    """Create a session. Env: BINJA_CODEMODE_MCP_HTTP_URL, BINJA_CODEMODE_MCP_PYTHON."""
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
        return StdioTransport(command=os.environ.get(PYTHON_ENV, sys.executable))
    raise ValueError(f"unsupported transport: {transport}")


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
