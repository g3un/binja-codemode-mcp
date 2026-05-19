from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .executor import run

mcp = FastMCP("binja-codemode-mcp-worker")


@mcp.tool
def execute(
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
    """Execute code.

    Prefer small scripts that print filtered summaries. Do not dump whole Binary
    Ninja objects or large collections unless explicitly requested.
    """
    return run(code)


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
