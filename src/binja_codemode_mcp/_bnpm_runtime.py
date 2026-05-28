from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

PLUGIN_NAME = "binja-codemode-mcp"


# Vendored subset of bnpm.runtime.python for launching plugin-owned workers.
@dataclass(frozen=True)
class PluginPython:
    command: Path
    cwd: Path
    env: dict[str, str]


def plugin_python(
    name: str = PLUGIN_NAME,
    *,
    env: dict[str, str] | None = None,
) -> PluginPython:
    plugin_path = _resolve_plugin_path(name)
    return PluginPython(
        command=_resolve_plugin_python_executable(),
        cwd=plugin_path,
        env=_build_plugin_python_env(name, plugin_path, env=env),
    )


@cache
def _resolve_plugin_python_executable() -> Path:
    python = _bnpm_venv_python()
    if not python.exists():
        raise RuntimeError("BNPM Python environment is missing; run `bnpm setup`")
    return python


def _build_plugin_python_env(
    name: str,
    plugin_path: Path,
    *,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    entry = _resolve_plugin_entry(name, plugin_path)
    if entry is None:
        raise RuntimeError(f"{name}: missing plugin entry point")
    _, import_base = entry

    result = dict(os.environ if env is None else env)
    result["PYTHONPATH"] = _join_pythonpath(
        _collect_plugin_pythonpath_entries(import_base),
        result.get("PYTHONPATH"),
    )
    return result


@cache
def _resolve_plugin_path(name: str) -> Path:
    target = (_bnpm_plugin_dir() / _encode_path_segment(name)).resolve()
    home = _bnpm_plugin_dir().resolve()
    if not target.is_relative_to(home):
        raise RuntimeError(f"plugin path escapes BNPM home: {name}")
    if not target.exists():
        raise RuntimeError(f"{name}: installed plugin not found: {target}")
    return target


@cache
def _collect_plugin_pythonpath_entries(import_base: Path) -> tuple[Path, ...]:
    entries = [import_base]
    packages = _bnpm_package_dir()
    if packages.exists():
        entries.append(packages)
    return tuple(entries)


@cache
def _resolve_plugin_entry(name: str, plugin_path: Path) -> tuple[Path, Path] | None:
    pyproject_path = plugin_path / "pyproject.toml"
    if pyproject_path.exists():
        entry = _resolve_pyproject_entry(name, plugin_path, pyproject_path)
        if entry is not None:
            return entry

    init_path = plugin_path / "__init__.py"
    if init_path.exists():
        return init_path, plugin_path
    return None


@cache
def _resolve_pyproject_entry(
    name: str,
    plugin_path: Path,
    pyproject_path: Path,
) -> tuple[Path, Path] | None:
    pyproject = _load_toml(pyproject_path)
    explicit = _resolve_tool_bnpm_entry(name, plugin_path, pyproject)
    if explicit is not None:
        return explicit

    project = pyproject.get("project", {})
    if not isinstance(project, dict):
        return None
    project_name = project.get("name")
    if not isinstance(project_name, str) or not project_name:
        return None

    package_name = re.sub(r"[-.]+", "_", project_name)
    init_path = plugin_path / "src" / package_name / "__init__.py"
    if init_path.exists():
        return init_path, plugin_path / "src"
    return None


def _resolve_tool_bnpm_entry(
    name: str,
    plugin_path: Path,
    pyproject: dict[str, Any],
) -> tuple[Path, Path] | None:
    tool = pyproject.get("tool", {})
    if not isinstance(tool, dict) or "bnpm" not in tool:
        return None
    bnpm = tool.get("bnpm")
    if not isinstance(bnpm, dict) or not bnpm:
        return None

    package = bnpm.get("package")
    source = bnpm.get("source", ".")
    if not isinstance(package, str) or not package:
        raise RuntimeError(f"{name}: [tool.bnpm].package must be a string")
    if not isinstance(source, str) or not source:
        raise RuntimeError(f"{name}: [tool.bnpm].source must be a string")

    import_base = (plugin_path / source).resolve()
    if not import_base.is_relative_to(plugin_path.resolve()):
        raise RuntimeError(f"{name}: [tool.bnpm].source escapes plugin directory")

    init_path = import_base / package / "__init__.py"
    if not init_path.exists():
        raise RuntimeError(f"{name}: missing {init_path}")
    return init_path, import_base


@cache
def _bnpm_plugin_dir() -> Path:
    return _bnpm_data_dir() / "plugins"


@cache
def _bnpm_package_dir() -> Path:
    return _bnpm_data_dir() / "packages"


@cache
def _bnpm_venv_python() -> Path:
    if platform.system() == "Windows":
        return _bnpm_data_dir() / "venv" / "Scripts" / "python.exe"
    return _bnpm_data_dir() / "venv" / "bin" / "python"


@cache
def _bnpm_data_dir() -> Path:
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return Path(base) / "bnpm"
    return Path.home() / ".local" / "share" / "bnpm"


def _join_pythonpath(entries: tuple[Path, ...], existing: str | None) -> str:
    values = [str(path) for path in entries]
    if existing:
        values.append(existing)
    return os.pathsep.join(values)


def _encode_path_segment(value: str) -> str:
    from urllib.parse import quote

    if not value:
        raise RuntimeError("empty plugin path segment")
    return quote(value, safe="")


@cache
def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:
        return _parse_toml_subset(path.read_text(encoding="utf-8"))

    with path.open("rb") as handle:
        return tomllib.load(handle)


def _parse_toml_subset(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] = data
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = data
            for part in line[1:-1].split("."):
                current = current.setdefault(part.strip(), {})
            continue
        key, sep, raw_value = line.partition("=")
        if not sep:
            continue
        value = raw_value.strip()
        if value.startswith('"') and value.endswith('"'):
            current[key.strip()] = value[1:-1]
    return data
