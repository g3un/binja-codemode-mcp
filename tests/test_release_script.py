from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "create_forgejo_release.py"
spec = importlib.util.spec_from_file_location("create_forgejo_release", SCRIPT)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = release
spec.loader.exec_module(release)


def test_validate_server_url_requires_https_without_credentials() -> None:
    assert (
        release.validate_server_url("https://codeberg.org/") == "https://codeberg.org"
    )

    for url in [
        "http://codeberg.org",
        "https://token@codeberg.org",
        "https://codeberg.org/path",
        "https://codeberg.org?x=1",
        "https://codeberg.org#x",
        "codeberg.org",
    ]:
        with pytest.raises(SystemExit):
            release.validate_server_url(url)
