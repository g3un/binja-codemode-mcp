LOGGER = "Binja Codemode MCP"

try:
    from binaryninja import PluginCommand, core_ui_enabled, log_error, log_info
except ImportError:
    PluginCommand = None
    core_ui_enabled = None
    log_error = None
    log_info = None


def _log_info(message: str) -> None:
    if log_info is not None:
        log_info(message, logger=LOGGER)


def _log_error(message: str) -> None:
    if log_error is not None:
        log_error(message, logger=LOGGER)


if PluginCommand is not None:
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
