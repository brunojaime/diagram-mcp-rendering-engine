from __future__ import annotations

import argparse
import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.responses import JSONResponse
from starlette.routing import Route

from . import __version__
from .diagnostics import diagram_diagnostics as engine_diagram_diagnostics
from .domain import validate_diagram_spec as engine_validate_diagram_spec
from .engine import (
    add_component as engine_add_component,
    add_connection as engine_add_connection,
    auto_layout_diagram as engine_auto_layout_diagram,
    create_component_diagram as engine_create_component_diagram,
    export_diagram as engine_export_diagram,
    move_node as engine_move_node,
    remove_element as engine_remove_element,
    update_node as engine_update_node,
)
from .renderer import render_diagram_svg as engine_render_diagram_svg


SPEC_ID = "016-diagram-mcp-rendering-engine"

_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_MUTATING = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


@dataclass(frozen=True)
class HttpsLoopbackConfig:
    host: str
    port: int
    cert_file: str
    key_file: str
    allowed_origins: tuple[str, ...]
    auth_token: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "cert_file": self.cert_file,
            "key_file": self.key_file,
            "allowed_origins": list(self.allowed_origins),
            "auth_token_required": bool(self.auth_token),
        }


def implementation_status() -> dict[str, object]:
    return {
        "status": "implemented_mvp",
        "spec_id": SPEC_ID,
        "version": __version__,
        "implemented_tools": [
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
        ],
        "transports": ["https", "stdio"],
    }


def build_mcp(*, host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    app = FastMCP(
        "Diagram MCP Rendering Engine",
        instructions=(
            "Create, validate, layout, render, edit, and export deterministic "
            "UML component diagrams. DiagramSpec remains the source of truth."
        ),
        host=host,
        port=port,
        streamable_http_path="/mcp",
        json_response=True,
        log_level="WARNING",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
            allowed_origins=["https://127.0.0.1:*", "https://localhost:*", "https://[::1]:*"],
        ),
    )
    _register_tools(app)
    return app


def build_http_app(app: FastMCP):
    http_app = app.streamable_http_app()
    http_app.router.routes.append(Route("/healthz", endpoint=_healthz, methods=["GET"]))
    return http_app


async def _healthz(request) -> JSONResponse:  # noqa: ANN001
    return JSONResponse(
        {
            "status": "ok",
            "name": "diagram-mcp-rendering-engine",
            "version": __version__,
            "specId": SPEC_ID,
        }
    )


def _register_tools(app: FastMCP) -> None:
    @app.tool(annotations=_READ_ONLY)
    def implementation_status_tool() -> dict[str, object]:
        """Return the current implementation status."""
        return implementation_status()

    @app.tool(name="create_component_diagram", annotations=_MUTATING)
    def create_component_diagram_tool(
        title: str = "Architecture Diagram",
        description: str = "",
        components: list[dict[str, Any]] | None = None,
        connections: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create and persist an initial DiagramSpec and SVG render."""
        return _wrap(
            lambda: engine_create_component_diagram(
                title=title,
                description=description,
                components=components,
                connections=connections,
            )
        )

    @app.tool(name="validate_diagram_spec", annotations=_READ_ONLY)
    def validate_diagram_spec_tool(spec: dict[str, Any]) -> dict[str, Any]:
        """Validate structure, semantics, templates, and references."""
        return engine_validate_diagram_spec(spec)

    @app.tool(name="auto_layout_diagram", annotations=_READ_ONLY)
    def auto_layout_diagram_tool(spec: dict[str, Any]) -> dict[str, Any]:
        """Calculate deterministic LR layout for a DiagramSpec."""
        return _wrap(lambda: engine_auto_layout_diagram(spec))

    @app.tool(name="render_diagram_svg", annotations=_READ_ONLY)
    def render_diagram_svg_tool(spec: dict[str, Any]) -> dict[str, Any]:
        """Render a DiagramSpec to self-contained deterministic SVG."""
        return _wrap(lambda: engine_render_diagram_svg(spec))

    @app.tool(name="add_component", annotations=_MUTATING)
    def add_component_tool(diagram_id: str, component: dict[str, Any]) -> dict[str, Any]:
        """Add a component to a persisted diagram."""
        return _wrap(lambda: engine_add_component(diagram_id, component))

    @app.tool(name="add_connection", annotations=_MUTATING)
    def add_connection_tool(diagram_id: str, connection: dict[str, Any]) -> dict[str, Any]:
        """Add a consumer-interface-provider connection to a persisted diagram."""
        return _wrap(lambda: engine_add_connection(diagram_id, connection))

    @app.tool(name="move_node", annotations=_MUTATING)
    def move_node_tool(diagram_id: str, node_id: str, position: dict[str, Any]) -> dict[str, Any]:
        """Move a component, snap it to grid, and pin its manual position."""
        return _wrap(lambda: engine_move_node(diagram_id, node_id, position))

    @app.tool(name="update_node", annotations=_MUTATING)
    def update_node_tool(
        diagram_id: str,
        node_id: str,
        label: str | None = None,
        metadata: dict[str, Any] | None = None,
        template: str | None = None,
    ) -> dict[str, Any]:
        """Update component label, metadata, or compatible template."""
        return _wrap(
            lambda: engine_update_node(
                diagram_id,
                node_id,
                label=label,
                metadata=metadata,
                template=template,
            )
        )

    @app.tool(name="remove_element", annotations=_MUTATING)
    def remove_element_tool(
        diagram_id: str,
        element_id: str,
        element_type: str = "auto",
        confirm: bool = True,
    ) -> dict[str, Any]:
        """Remove a component or connection after validating impact."""
        return _wrap(
            lambda: engine_remove_element(
                diagram_id,
                element_id,
                element_type=element_type,
                confirm=confirm,
            )
        )

    @app.tool(name="export_diagram", annotations=_READ_ONLY)
    def export_diagram_tool(diagram_id: str, format: str = "svg") -> dict[str, Any]:
        """Export a persisted diagram. MVP supports SVG only."""
        return _wrap(lambda: engine_export_diagram(diagram_id, format=format))

    @app.tool(name="diagram_diagnostics", annotations=_READ_ONLY)
    def diagram_diagnostics_tool(spec: dict[str, Any]) -> dict[str, Any]:
        """Return bounded validation, layout, and routing diagnostics."""
        return _wrap(lambda: engine_diagram_diagnostics(spec))


def _wrap(callable_: Any) -> dict[str, Any]:
    try:
        return callable_()
    except Exception as exc:  # noqa: BLE001
        return {
            "valid": False,
            "errors": [
                {
                    "code": exc.__class__.__name__,
                    "path": "$",
                    "message": str(exc),
                    "severity": "error",
                }
            ],
            "warnings": [],
        }


def https_loopback_config_from_env(env: dict[str, str] | None = None) -> HttpsLoopbackConfig:
    values = env or os.environ
    host = values.get("DIAGRAM_MCP_HOST", "127.0.0.1")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("DIAGRAM_MCP_HOST must be a loopback host for the MVP.")
    cert_file = values.get("DIAGRAM_MCP_TLS_CERT")
    key_file = values.get("DIAGRAM_MCP_TLS_KEY")
    if not cert_file or not key_file:
        raise ValueError("DIAGRAM_MCP_TLS_CERT and DIAGRAM_MCP_TLS_KEY are required for HTTPS mode.")
    port = int(values.get("DIAGRAM_MCP_PORT", "8765"))
    origins = tuple(
        origin.strip()
        for origin in values.get(
            "DIAGRAM_MCP_ALLOWED_ORIGINS",
            "https://localhost,https://127.0.0.1",
        ).split(",")
        if origin.strip()
    )
    return HttpsLoopbackConfig(
        host=host,
        port=port,
        cert_file=str(Path(cert_file).expanduser()),
        key_file=str(Path(key_file).expanduser()),
        allowed_origins=origins,
        auth_token=values.get("DIAGRAM_MCP_TOKEN"),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Diagram MCP Rendering Engine.")
    parser.add_argument("--transport", choices=("https", "stdio"), default=os.environ.get("DIAGRAM_MCP_TRANSPORT", "stdio"))
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--certfile", default=None)
    parser.add_argument("--keyfile", default=None)
    args = parser.parse_args(argv)

    if args.transport == "stdio":
        build_mcp().run(transport="stdio")
        return

    env = dict(os.environ)
    if args.host:
        env["DIAGRAM_MCP_HOST"] = args.host
    if args.port:
        env["DIAGRAM_MCP_PORT"] = str(args.port)
    if args.certfile:
        env["DIAGRAM_MCP_TLS_CERT"] = args.certfile
    if args.keyfile:
        env["DIAGRAM_MCP_TLS_KEY"] = args.keyfile
    config = https_loopback_config_from_env(env)
    app = build_mcp(host=config.host, port=config.port)
    uvicorn_module = importlib.import_module("uvicorn")
    uvicorn_module.run(
        build_http_app(app),
        host=config.host,
        port=config.port,
        ssl_certfile=config.cert_file,
        ssl_keyfile=config.key_file,
        log_level="warning",
    )


mcp = build_mcp()


if __name__ == "__main__":
    main()
