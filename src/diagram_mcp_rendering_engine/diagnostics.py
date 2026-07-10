from __future__ import annotations

from typing import Any

from .layout import build_render_model


def diagram_diagnostics(spec: dict[str, Any]) -> dict[str, Any]:
    model = build_render_model(spec)
    return {
        "valid": model["valid"],
        "diagram_id": model["spec"].get("id"),
        "node_count": len(model["nodes"]),
        "connector_count": len(model["connectors"]),
        "errors": model["errors"],
        "warnings": model["warnings"],
    }

