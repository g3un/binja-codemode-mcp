from __future__ import annotations

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from ._result import result_data


class HttpTransport:
    def __init__(self, url: str) -> None:
        self.url = url

    def describe(self) -> dict:
        return {
            "transport": "http",
            "url": self.url,
        }

    async def execute(self, code: str) -> dict:
        return await self._call("execute", {"code": code})

    async def close(self) -> dict:
        return {"closed": True}

    async def _call(self, tool: str, arguments: dict) -> dict:
        transport = StreamableHttpTransport(self.url)
        async with Client(transport) as client:
            result = await client.call_tool(tool, arguments)
        return result_data(result)
