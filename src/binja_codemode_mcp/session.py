from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from threading import RLock
from typing import Protocol


class Transport(Protocol):
    def describe(self) -> dict: ...

    async def execute(self, code: str) -> dict: ...

    async def close(self) -> dict: ...


@dataclass
class GatewaySession:
    id: str
    transport: Transport
    created_at: float

    def describe(self) -> dict:
        return {
            "session_id": self.id,
            "created_at": self.created_at,
            "transport": self.transport.describe(),
        }


class GatewaySessionRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, GatewaySession] = {}

    def add(self, transport: Transport) -> GatewaySession:
        session = GatewaySession(
            id=uuid.uuid4().hex,
            transport=transport,
            created_at=time.time(),
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> GatewaySession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session: {session_id}")
        return session

    def remove(self, session_id: str) -> GatewaySession:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            raise KeyError(f"unknown session: {session_id}")
        return session

    def list(self) -> list[dict]:
        with self._lock:
            sessions = list(self._sessions.values())
        return [session.describe() for session in sessions]
