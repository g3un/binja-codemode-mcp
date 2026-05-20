import asyncio
import argparse
import logging
import os
import sys
import threading
from typing import Annotated

from binaryninja import log_error, log_info, log_warn
from fastmcp import FastMCP
from pydantic import Field

from .executor import run

LOGGER = "Binja Codemode MCP"
LOOPBACK = {"127.0.0.1", "::1", "localhost"}
DEFAULT_BIND = "127.0.0.1:44044"

mcp = FastMCP("binja-codemode-mcp")


@mcp.tool
def execute(
    code: Annotated[
        str,
        Field(
            description=(
                "Python code to execute. Print concise, filtered results; use "
                "dir/help/inspect for API discovery. Do not print full object "
                "dumps or large collections unless requested."
            )
        ),
    ],
) -> dict:
    """Execute code.

    Prefer small scripts that print filtered summaries. Do not dump whole Binary
    Ninja objects or large collections unless explicitly requested.
    """
    return run(code)


class _BNHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            log_error(msg, logger=LOGGER)
        elif record.levelno >= logging.WARNING:
            log_warn(msg, logger=LOGGER)
        else:
            log_info(msg, logger=LOGGER)


def _configure_server_logs(handler: logging.Handler) -> None:
    handler.setFormatter(logging.Formatter("%(message)s"))
    for name in ("uvicorn", "uvicorn.error", "fastmcp"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False
        lg.setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").disabled = True


def _quiet_server_logs() -> None:
    _configure_server_logs(_BNHandler())


def _cli_server_logs() -> None:
    _configure_server_logs(logging.StreamHandler())


def _parse_bind(value: str) -> tuple[str, int]:
    host, sep, port = value.rpartition(":")
    if not sep:
        raise ValueError(f"invalid bind '{value}', expected host:port")
    return host, int(port)


def _validated_bind(bind: str) -> tuple[str, int]:
    host, port = _parse_bind(bind)
    if host not in LOOPBACK and not os.environ.get("BINJA_CODEMODE_MCP_INSECURE_BIND"):
        raise ValueError(
            f"refusing to bind non-loopback host '{host}'. "
            "Set BINJA_CODEMODE_MCP_INSECURE_BIND=1 to override."
        )
    return host, port


async def _run_http(host: str, port: int) -> None:
    uvicorn_config = {
        "log_config": None,
        "access_log": False,
        "lifespan": "on",
    }
    await mcp.run_http_async(
        show_banner=False,
        transport="http",
        host=host,
        port=port,
        log_level="warning",
        uvicorn_config=uvicorn_config,
    )


_loop: asyncio.AbstractEventLoop | None = None
_task: asyncio.Task | None = None
_thread: threading.Thread | None = None


def is_running() -> bool:
    return _loop is not None


def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()


def start(bind: str) -> None:
    global _loop, _task, _thread
    if _loop is not None:
        log_info("already running", logger=LOGGER)
        return
    try:
        host, port = _validated_bind(bind)
    except ValueError as exc:
        log_error(str(exc), logger=LOGGER)
        return

    _quiet_server_logs()
    loop = asyncio.new_event_loop()

    async def _serve() -> None:
        try:
            await _run_http(host, port)
        except asyncio.CancelledError:
            pass
        except BaseException as exc:
            log_error(f"server crashed: {exc!r}", logger=LOGGER)

    _thread = threading.Thread(
        target=_run_loop, args=(loop,), daemon=True, name="binja-codemode-mcp-http"
    )
    _thread.start()
    _task = asyncio.run_coroutine_threadsafe(_serve(), loop)
    _loop = loop
    log_info(f"listening on http://{host}:{port}/mcp/", logger=LOGGER)


def stop() -> None:
    global _loop, _task, _thread
    if _loop is None:
        log_info("not running", logger=LOGGER)
        return
    loop = _loop
    task = _task
    if task is not None:
        task.cancel()
    loop.call_soon_threadsafe(loop.stop)
    if _thread is not None:
        _thread.join(timeout=2)
    _loop, _task, _thread = None, None, None
    log_info("stopped", logger=LOGGER)


def serve(bind: str = DEFAULT_BIND) -> None:
    host, port = _validated_bind(bind)
    _cli_server_logs()
    print(f"{LOGGER}: listening on http://{host}:{port}/mcp/", flush=True)
    try:
        asyncio.run(_run_http(host, port))
    except KeyboardInterrupt:
        print(f"{LOGGER}: stopped", file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Binary Ninja Codemode MCP HTTP server."
    )
    parser.add_argument(
        "--bind",
        default=DEFAULT_BIND,
        help=f"host:port to bind the HTTP server to (default: {DEFAULT_BIND})",
    )
    args = parser.parse_args()
    try:
        serve(args.bind)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
