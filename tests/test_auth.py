from __future__ import annotations

import asyncio

from binja_codemode_mcp.auth import PREFIX, EphemeralApiKeyVerifier, generate_api_key, parse_api_key


def test_generate_api_key_format_and_parse() -> None:
    api_key = generate_api_key()

    assert api_key.token.startswith(PREFIX)
    assert api_key.token == api_key.token.lower()
    assert api_key.token.endswith("=")

    parsed = parse_api_key(api_key.token)
    assert parsed is not None
    key_id, secret = parsed
    assert key_id == api_key.key_id
    assert len(secret) == 32


def test_ephemeral_api_key_verifier() -> None:
    async def run() -> None:
        api_key = generate_api_key()
        verifier = EphemeralApiKeyVerifier(api_key)

        assert await verifier.verify_token(api_key.token) is not None
        assert await verifier.verify_token(api_key.token[:-1] + "a") is None

    asyncio.run(run())
