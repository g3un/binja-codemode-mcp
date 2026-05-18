import importlib
import importlib.util
import io
import site
import sys
from pathlib import Path

from binaryninja import PluginCommand, core_ui_enabled, log_error, log_info

LOGGER = "Binja Codemode MCP"
_REQUIRED = ("fastmcp",)


def _ensure_user_site_on_path() -> None:
    user_site = site.getusersitepackages()
    if user_site:
        site.addsitedir(user_site)


def _bootstrap_dependencies() -> bool:
    _ensure_user_site_on_path()
    missing = [m for m in _REQUIRED if importlib.util.find_spec(m) is None]
    if not missing:
        return True
    req = Path(__file__).with_name("requirements.txt")
    log_info(f"installing dependencies: {', '.join(missing)}", logger=LOGGER)
    try:
        from pip._internal.cli.main import main as pip_main
    except ImportError as exc:
        log_error(f"pip unavailable: {exc}", logger=LOGGER)
        return False

    buf = io.StringIO()
    saved_stdout, saved_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = buf
    try:
        rc = pip_main(
            [
                "install",
                "--user",
                "--quiet",
                "--no-input",
                "--disable-pip-version-check",
                "--progress-bar",
                "off",
                "-r",
                str(req),
            ]
        )
    finally:
        sys.stdout, sys.stderr = saved_stdout, saved_stderr

    output = buf.getvalue().strip()
    if rc != 0:
        log_error(f"pip install exited with {rc}\n{output}", logger=LOGGER)
        return False
    if output:
        log_info(output, logger=LOGGER)
    _ensure_user_site_on_path()
    importlib.invalidate_caches()
    return all(importlib.util.find_spec(m) is not None for m in _REQUIRED)


if not _bootstrap_dependencies():
    raise ImportError("binja-codemode-mcp: failed to install required dependencies")

from . import server, settings  # noqa: E402

settings.register()


def _start(_=None) -> None:
    server.start(settings.bind())


def _stop(_=None) -> None:
    server.stop()


def _can_start(_=None) -> bool:
    return not server.is_running()


def _can_stop(_=None) -> bool:
    return server.is_running()


PluginCommand.register(
    "Binja Codemode MCP\\Start",
    "Start Binja Codemode MCP server",
    _start,
    is_valid=_can_start,
)
PluginCommand.register(
    "Binja Codemode MCP\\Stop",
    "Stop Binja Codemode MCP server",
    _stop,
    is_valid=_can_stop,
)

if core_ui_enabled() and settings.autostart():
    _start()
