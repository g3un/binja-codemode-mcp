from __future__ import annotations

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class HttpTransport:
    def __init__(self, url: str, headers: dict[str, str] | None = None) -> None:
        self.url = url
        self.headers = headers

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
        transport = StreamableHttpTransport(self.url, headers=self.headers)
        async with Client(transport) as client:
            result = await client.call_tool(tool, arguments)
        return _result_data(result)


def _result_data(result) -> dict:
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    return {"result": data}
