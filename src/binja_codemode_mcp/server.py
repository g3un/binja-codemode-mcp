import asyncio
import logging
import os
import threading

from binaryninja import log_error, log_info, log_warn
from fastmcp import FastMCP

from .executor import run

LOGGER = "Binja Codemode MCP"
LOOPBACK = {"127.0.0.1", "::1", "localhost"}

mcp = FastMCP("binja-codemode-mcp")


@mcp.tool
def execute(code: str) -> dict:
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


def _route_uvicorn_logs() -> None:
    handler = _BNHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False
        lg.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True


def _parse_bind(value: str) -> tuple[str, int]:
    host, sep, port = value.rpartition(":")
    if not sep:
        raise ValueError(f"invalid bind '{value}', expected host:port")
    return host, int(port)


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
        host, port = _parse_bind(bind)
    except ValueError as exc:
        log_error(str(exc), logger=LOGGER)
        return
    if host not in LOOPBACK and not os.environ.get(
        "BINJA_CODEMODE_MCP_INSECURE_BIND"
    ):
        log_error(
            f"refusing to bind non-loopback host '{host}'. "
            "Set BINJA_CODEMODE_MCP_INSECURE_BIND=1 to override.",
            logger=LOGGER,
        )
        return

    _route_uvicorn_logs()
    loop = asyncio.new_event_loop()
    uvicorn_config = {
        "log_config": None,
        "access_log": False,
        "lifespan": "on",
    }

    async def _serve() -> None:
        try:
            await mcp.run_http_async(
                show_banner=False,
                transport="http",
                host=host,
                port=port,
                log_level="info",
                uvicorn_config=uvicorn_config,
            )
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
