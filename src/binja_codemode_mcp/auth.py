from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets
from dataclasses import dataclass

from fastmcp.server.auth import AccessToken, TokenVerifier

VERSION = 1
PREFIX = f"bcmcp_v{VERSION}_"
KEY_ID_SIZE = 16
SECRET_SIZE = 32
PAYLOAD_SIZE = KEY_ID_SIZE + SECRET_SIZE


@dataclass(frozen=True)
class ApiKey:
    token: str
    key_id: bytes
    secret_hash: bytes


def generate_api_key() -> ApiKey:
    key_id = secrets.token_bytes(KEY_ID_SIZE)
    secret = secrets.token_bytes(SECRET_SIZE)
    payload = key_id + secret
    token = PREFIX + base64.b32encode(payload).decode("ascii").lower()
    return ApiKey(token=token, key_id=key_id, secret_hash=_hash_api_key(key_id, secret))


def parse_api_key(token: str) -> tuple[bytes, bytes] | None:
    token = token.strip()
    if not token.startswith(PREFIX):
        return None
    body = token[len(PREFIX) :]
    if body != body.lower():
        return None
    try:
        payload = base64.b32decode(body.upper())
    except (binascii.Error, ValueError):
        return None
    if len(payload) != PAYLOAD_SIZE:
        return None
    return payload[:KEY_ID_SIZE], payload[KEY_ID_SIZE:]


def _hash_api_key(key_id: bytes, secret: bytes) -> bytes:
    hasher = hashlib.sha3_512()
    hasher.update(key_id)
    hasher.update(VERSION.to_bytes(2, "little"))
    hasher.update(secret)
    return hasher.digest()


class EphemeralApiKeyVerifier(TokenVerifier):
    def __init__(self, api_key: ApiKey) -> None:
        super().__init__(required_scopes=["execute"])
        self.key_id = api_key.key_id
        self.secret_hash = api_key.secret_hash

    async def verify_token(self, token: str) -> AccessToken | None:
        parsed = parse_api_key(token)
        if parsed is None:
            return None
        key_id, secret = parsed
        if not hmac.compare_digest(key_id, self.key_id):
            return None
        if not hmac.compare_digest(_hash_api_key(key_id, secret), self.secret_hash):
            return None
        return AccessToken(
            token=token,
            client_id="binja-codemode-mcp",
            scopes=["execute"],
            claims={"api_key_id": key_id.hex()},
        )
