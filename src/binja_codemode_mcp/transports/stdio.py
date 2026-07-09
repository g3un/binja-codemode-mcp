from __future__ import annotations

import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport as FastMCPStdioTransport

from ._result import result_data


class StdioTransport:
    def __init__(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        self.command = command or sys.executable
        self.args = args or ["-m", "binja_codemode_mcp.worker"]
        self.env = env
        self.cwd = cwd
        self._transport = FastMCPStdioTransport(
            self.command,
            self.args,
            env=self.env,
            cwd=self.cwd,
            keep_alive=True,
        )
        self._client = Client(self._transport)
        self._entered = False
        self._lock = asyncio.Lock()

    def describe(self) -> dict:
        return {
            "transport": "stdio",
            "command": self.command,
            "args": self.args,
            "cwd": self.cwd,
        }

    async def execute(self, code: str) -> dict:
        async with self._lock:
            client = await self._connect()
            return result_data(await client.call_tool("execute", {"code": code}))

    async def close(self) -> dict:
        async with self._lock:
            await self.aclose()
        return {"closed": True}

    async def aclose(self) -> None:
        if self._entered:
            self._entered = False
            await self._client.__aexit__(None, None, None)

    async def _connect(self) -> Client:
        if not self._entered:
            await self._client.__aenter__()
            self._entered = True
        return self._client
