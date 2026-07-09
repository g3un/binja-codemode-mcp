import asyncio
import argparse
import logging
import sys
import threading
from typing import Annotated

from binaryninja import log_error, log_info, log_warn
from fastmcp import FastMCP
from pydantic import Field

from .auth import ApiKey, EphemeralApiKeyVerifier, generate_api_key
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
                "Python code to run. Print concise, filtered results; use "
                "dir/help/inspect for API discovery. Do not print full object "
                "dumps or large collections unless the user asks for them."
            )
        ),
    ],
) -> dict:
    """Execute code.

    Prefer small scripts that print filtered summaries. Do not dump whole Binary
    Ninja objects or large collections unless the user asks for them.
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


def _validated_bind(bind: str) -> tuple[str, int]:
    host, sep, port = bind.rpartition(":")
    if not sep:
        raise ValueError(f"invalid bind '{bind}', expected host:port")
    return host, int(port)


def _configure_auth(api_key: ApiKey | None) -> None:
    mcp.auth = EphemeralApiKeyVerifier(api_key) if api_key is not None else None


async def _run_http(host: str, port: int, api_key: ApiKey | None) -> None:
    _configure_auth(api_key)
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
_auth_token: str | None = None


def is_running() -> bool:
    return _loop is not None


def auth_token() -> str | None:
    return _auth_token


def _run_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()


def start(bind: str) -> None:
    global _loop, _task, _thread, _auth_token
    if _loop is not None:
        log_info("already running", logger=LOGGER)
        return
    try:
        host, port = _validated_bind(bind)
    except ValueError as exc:
        log_error(str(exc), logger=LOGGER)
        return

    _configure_server_logs(_BNHandler())
    api_key = generate_api_key() if host not in LOOPBACK else None
    loop = asyncio.new_event_loop()

    async def _serve() -> None:
        global _loop, _task, _thread, _auth_token
        try:
            await _run_http(host, port, api_key)
        except asyncio.CancelledError:
            pass
        except BaseException as exc:
            log_error(f"server crashed: {exc!r}", logger=LOGGER)
        finally:
            if _loop is loop:
                _loop, _task, _thread, _auth_token = None, None, None, None
            loop.call_soon(loop.stop)

    _loop = loop
    _auth_token = api_key.token if api_key is not None else None
    _thread = threading.Thread(
        target=_run_loop, args=(loop,), daemon=True, name="binja-codemode-mcp-http"
    )
    _thread.start()
    _task = asyncio.run_coroutine_threadsafe(_serve(), loop)
    log_info(f"listening on http://{host}:{port}/mcp/", logger=LOGGER)
    if api_key is not None:
        log_info(f"auth token: {api_key.token}", logger=LOGGER)


def stop() -> None:
    global _loop, _task, _thread, _auth_token
    if _loop is None:
        log_info("not running", logger=LOGGER)
        return
    loop = _loop
    task = _task
    thread = _thread
    if task is not None:
        task.cancel()
    loop.call_soon_threadsafe(loop.stop)
    if thread is not None:
        thread.join(timeout=2)
    _loop, _task, _thread, _auth_token = None, None, None, None
    log_info("stopped", logger=LOGGER)


def serve(bind: str = DEFAULT_BIND) -> None:
    host, port = _validated_bind(bind)
    api_key = generate_api_key() if host not in LOOPBACK else None
    _configure_server_logs(logging.StreamHandler())
    print(f"{LOGGER}: listening on http://{host}:{port}/mcp/", flush=True)
    if api_key is not None:
        print(f"{LOGGER}: auth token: {api_key.token}", flush=True)
    try:
        asyncio.run(_run_http(host, port, api_key))
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
