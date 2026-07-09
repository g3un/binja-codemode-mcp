from __future__ import annotations

import pytest

from binja_codemode_mcp import gateway
from binja_codemode_mcp.session import GatewaySessionRegistry


class FailingCloseTransport:
    def describe(self) -> dict:
        return {"transport": "dummy"}

    async def execute(self, code: str) -> dict:
        return {"code": code}

    async def close(self) -> dict:
        raise RuntimeError("close failed")


@pytest.mark.anyio
async def test_close_session_keeps_session_when_close_fails() -> None:
    old_sessions = gateway._sessions
    gateway._sessions = GatewaySessionRegistry()
    try:
        session = gateway._sessions.add(FailingCloseTransport())

        with pytest.raises(RuntimeError, match="close failed"):
            await gateway.close_session(session.id)

        assert gateway._sessions.get(session.id) is session
    finally:
        gateway._sessions = old_sessions
