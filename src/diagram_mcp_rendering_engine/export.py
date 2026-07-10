from __future__ import annotations

from typing import Any

from .renderer import render_diagram_svg


def export_diagram(spec: dict[str, Any], format: str = "svg") -> dict[str, Any]:
    if format != "svg":
        return {
            "ok": False,
            "format": format,
            "errors": [
                {
                    "code": "UNSUPPORTED_EXPORT_FORMAT",
                    "path": "/format",
                    "message": "Only svg export is supported in the MVP.",
                    "severity": "error",
                }
            ],
        }
    rendered = render_diagram_svg(spec)
    if not rendered["valid"]:
        return {"ok": False, "format": format, "errors": rendered["errors"], "warnings": rendered["warnings"]}
    return {
        "ok": True,
        "format": "svg",
        "mime_type": "image/svg+xml",
        "filename": f"{rendered['spec']['id']}.svg",
        "data": rendered["svg"],
        "warnings": rendered["warnings"],
    }

