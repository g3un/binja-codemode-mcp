import traceback
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

_GLOBALS: dict = {"__name__": "__binja_codemode_mcp__"}


def run(code: str) -> dict:
    out, err = StringIO(), StringIO()
    exc: str | None = None
    with redirect_stdout(out), redirect_stderr(err):
        try:
            exec(compile(code, "<mcp>", "exec"), _GLOBALS)
        except BaseException:
            exc = traceback.format_exc()
    return {"stdout": out.getvalue(), "stderr": err.getvalue(), "exception": exc}
