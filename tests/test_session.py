from __future__ import annotations

import pytest

from binja_codemode_mcp.session import GatewaySessionRegistry


class DummyTransport:
    def describe(self) -> dict:
        return {"transport": "dummy"}

    async def execute(self, code: str) -> dict:
        return {"code": code}

    async def close(self) -> dict:
        return {"closed": True}


def test_registry_add_get_list_remove() -> None:
    registry = GatewaySessionRegistry()
    transport = DummyTransport()

    session = registry.add(transport, metadata={"name": "test"})

    assert registry.get(session.id) is session
    assert registry.list() == [session.describe()]
    assert session.describe()["transport"] == {"transport": "dummy"}
    assert session.describe()["metadata"] == {"name": "test"}
    assert registry.remove(session.id) is session
    assert registry.list() == []


def test_registry_unknown_session_raises_key_error() -> None:
    registry = GatewaySessionRegistry()

    with pytest.raises(KeyError, match="unknown session: missing"):
        registry.get("missing")

    with pytest.raises(KeyError, match="unknown session: missing"):
        registry.remove("missing")
