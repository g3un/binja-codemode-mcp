import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from threading import RLock

_CAPTURE_LOCK = RLock()


class Executor:
    def __init__(self, name: str, globals: dict | None = None) -> None:
        self._lock = RLock()
        self.globals = {
            "__name__": name,
            **(globals or {}),
        }

    def run(self, code: str) -> dict:
        out, err = StringIO(), StringIO()
        exc: str | None = None
        with self._lock, _CAPTURE_LOCK, redirect_stdout(out), redirect_stderr(err):
            try:
                exec(compile(code, "<mcp>", "exec"), self.globals)
            except BaseException:
                exc = traceback.format_exc()
        return {
            "stdout": out.getvalue(),
            "stderr": err.getvalue(),
            "exception": exc,
        }


def run(code: str) -> dict:
    return _DEFAULT_EXECUTOR.run(code)


_DEFAULT_EXECUTOR = Executor("__binja_codemode_mcp__")
