from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from diagram_mcp_rendering_engine import server
from diagram_mcp_rendering_engine.server import https_loopback_config_from_env


DOCUMENTED_TOOLS = {
    "create_component_diagram",
    "validate_diagram_spec",
    "auto_layout_diagram",
    "render_diagram_svg",
    "add_component",
    "add_connection",
    "move_node",
    "update_node",
    "remove_element",
    "export_diagram",
    "diagram_diagnostics",
}


def test_server_requires_https_loopback_configuration() -> None:
    with pytest.raises(ValueError, match="TLS_CERT"):
        https_loopback_config_from_env({"DIAGRAM_MCP_HOST": "127.0.0.1"})

    with pytest.raises(ValueError, match="loopback"):
        https_loopback_config_from_env(
            {
                "DIAGRAM_MCP_HOST": "0.0.0.0",
                "DIAGRAM_MCP_TLS_CERT": "cert.pem",
                "DIAGRAM_MCP_TLS_KEY": "key.pem",
            }
        )

    config = https_loopback_config_from_env(
        {
            "DIAGRAM_MCP_HOST": "localhost",
            "DIAGRAM_MCP_TLS_CERT": "cert.pem",
            "DIAGRAM_MCP_TLS_KEY": "key.pem",
            "DIAGRAM_MCP_PORT": "9443",
        }
    )
    assert config.as_dict()["host"] == "localhost"
    assert config.as_dict()["port"] == 9443


def test_stdio_mode_runs_stdio_transport(monkeypatch) -> None:
    calls = []

    class FakeMcp:
        def run(self, *, transport):
            calls.append(transport)

    monkeypatch.delenv("DIAGRAM_MCP_TRANSPORT", raising=False)
    monkeypatch.setattr(server, "build_mcp", lambda: FakeMcp())

    server.main(["--transport", "stdio"])

    assert calls == ["stdio"]


def test_https_mode_runs_streamable_http_with_tls(monkeypatch) -> None:
    calls = []

    def fake_run(app, **kwargs):
        calls.append({"app": app, **kwargs})

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("DIAGRAM_MCP_TRANSPORT", "https")
    monkeypatch.setenv("DIAGRAM_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("DIAGRAM_MCP_PORT", "9443")
    monkeypatch.setenv("DIAGRAM_MCP_TLS_CERT", "cert.pem")
    monkeypatch.setenv("DIAGRAM_MCP_TLS_KEY", "key.pem")

    server.main([])

    assert calls
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 9443
    assert calls[0]["ssl_certfile"] == "cert.pem"
    assert calls[0]["ssl_keyfile"] == "key.pem"


def test_mcp_tool_registry_exposes_documented_tools() -> None:
    app = server.build_mcp()
    tools = app._tool_manager._tools  # SDK registry; no server process required.

    assert DOCUMENTED_TOOLS.issubset(set(tools))
    for tool_name in DOCUMENTED_TOOLS:
        assert callable(tools[tool_name].fn)
