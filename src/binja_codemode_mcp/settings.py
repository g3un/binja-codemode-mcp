import json

from binaryninja import Settings


def register() -> None:
    s = Settings()
    s.register_group("binjaCodemodeMcp", "Binja Codemode MCP")
    s.register_setting(
        "binjaCodemodeMcp.bind",
        json.dumps(
            {
                "title": "Bind address",
                "type": "string",
                "default": "127.0.0.1:44044",
                "description": (
                    "host:port for the MCP HTTP server. Non-loopback hosts "
                    "require the BINJA_CODEMODE_MCP_INSECURE_BIND environment "
                    "variable."
                ),
            }
        ),
    )
    s.register_setting(
        "binjaCodemodeMcp.autostart",
        json.dumps(
            {
                "title": "Autostart",
                "type": "boolean",
                "default": False,
                "description": "Start the MCP server when Binary Ninja launches.",
            }
        ),
    )


def bind() -> str:
    return Settings().get_string("binjaCodemodeMcp.bind")


def autostart() -> bool:
    return Settings().get_bool("binjaCodemodeMcp.autostart")
