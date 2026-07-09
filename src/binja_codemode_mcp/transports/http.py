from __future__ import annotations

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from ._result import result_data


class HttpTransport:
    def __init__(self, url: str, auth_token: str | None = None) -> None:
        self.url = url
        self.auth_token = auth_token.strip() if auth_token else None

    def describe(self) -> dict:
        return {
            "transport": "http",
            "url": self.url,
            "auth": bool(self.auth_token),
        }

    async def execute(self, code: str) -> dict:
        return await self._call("execute", {"code": code})

    async def close(self) -> dict:
        return {"closed": True}

    async def _call(self, tool: str, arguments: dict) -> dict:
        headers = None
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
        transport = StreamableHttpTransport(self.url, headers=headers)
        async with Client(transport) as client:
            result = await client.call_tool(tool, arguments)
        return result_data(result)
