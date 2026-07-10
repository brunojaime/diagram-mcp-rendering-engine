from __future__ import annotations

from html import escape
from typing import Any

from .layout import build_render_model


THEME = {
    "background": "#ffffff",
    "component_fill": "#f8fafc",
    "component_stroke": "#334155",
    "interface_fill": "#ffffff",
    "connector_stroke": "#475569",
    "text": "#0f172a",
    "muted": "#64748b",
}


def render_diagram_svg(spec: dict[str, Any]) -> dict[str, Any]:
    model = build_render_model(spec)
    if not model["valid"]:
        return {**model, "svg": ""}

    view_box = _view_box(model)
    parts = [
        _svg_open(view_box),
        _style(),
        '<g id="diagram-connectors" data-layer="connectors">',
    ]
    for connector in model["connectors"]:
        parts.append(_render_connector(connector))
    parts.append("</g>")
    parts.append('<g id="diagram-nodes" data-layer="nodes">')
    for node in model["nodes"]:
        if node["type"] == "component":
            parts.append(_render_component(node))
        else:
            parts.append(_render_interface(node))
    parts.append("</g>")
    parts.append("</svg>")
    return {**model, "svg": "\n".join(parts)}


def _svg_open(view_box: tuple[int, int, int, int]) -> str:
    x, y, width, height = view_box
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="{x} {y} {width} {height}" '
        f'width="{width}" height="{height}" data-renderer="diagram-mcp-rendering-engine">'
    )


def _style() -> str:
    return (
        "<style>"
        ".component{fill:#f8fafc;stroke:#334155;stroke-width:1.5}"
        ".component-icon{fill:#e2e8f0;stroke:#334155;stroke-width:1}"
        ".interface-line,.connector{fill:none;stroke:#475569;stroke-width:1.6}"
        ".socket{fill:none;stroke:#475569;stroke-width:1.6}"
        ".lollipop{fill:#fff;stroke:#475569;stroke-width:1.6}"
        ".label{font-family:Inter,Arial,sans-serif;font-size:13px;fill:#0f172a}"
        ".small-label{font-family:Inter,Arial,sans-serif;font-size:11px;fill:#64748b}"
        "</style>"
    )


def _render_component(node: dict[str, Any]) -> str:
    node_id = _xml_id(node["id"])
    label = escape(_fit_label(node["label"], 24))
    x = node["x"]
    y = node["y"]
    return "\n".join(
        [
            (
                f'<g id="node-{node_id}" data-node-id="{escape(node["id"])}" '
                f'data-node-type="uml_component" transform="translate({x} {y})">'
            ),
            f'<rect class="component" width="{node["width"]}" height="{node["height"]}" rx="4"/>',
            '<rect class="component-icon" x="140" y="14" width="22" height="18" rx="2"/>',
            '<rect class="component-icon" x="132" y="18" width="12" height="4" rx="1"/>',
            '<rect class="component-icon" x="132" y="28" width="12" height="4" rx="1"/>',
            f'<text class="label" x="16" y="44">{label}</text>',
            "</g>",
        ]
    )


def _render_interface(node: dict[str, Any]) -> str:
    node_id = _xml_id(node["id"])
    label = escape(_fit_label(node["label"], 18))
    center_y = node["height"] // 2
    socket_x = 16
    lollipop_x = node["width"] - 16
    return "\n".join(
        [
            (
                f'<g id="node-{node_id}" data-node-id="{escape(node["id"])}" '
                f'data-node-type="provided_required_interface" '
                f'data-connection-id="{escape(node["connection_id"])}" '
                f'transform="translate({node["x"]} {node["y"]})">'
            ),
            f'<text class="small-label" text-anchor="middle" x="{node["width"] // 2}" y="10">{label}</text>',
            f'<path class="interface-line" d="M {socket_x} {center_y} L {lollipop_x} {center_y}"/>',
            (
                f'<path id="{node_id}-socket" class="socket" data-anchor="required" '
                f'd="M {socket_x} {center_y - 12} A 12 12 0 0 1 {socket_x} {center_y + 12}"/>'
            ),
            (
                f'<circle id="{node_id}-lollipop" class="lollipop" data-anchor="provided" '
                f'cx="{lollipop_x}" cy="{center_y}" r="10"/>'
            ),
            "</g>",
        ]
    )


def _render_connector(connector: dict[str, Any]) -> str:
    connector_id = _xml_id(connector["id"])
    return (
        f'<path id="connector-{connector_id}" class="connector" '
        f'data-connection-id="{escape(connector["semantic_connection_id"])}" '
        f'data-from-node="{escape(connector["from_node"])}" '
        f'data-to-node="{escape(connector["to_node"])}" '
        f'data-role="{escape(connector["role"])}" d="{connector["path"]}"/>'
    )


def _view_box(model: dict[str, Any]) -> tuple[int, int, int, int]:
    xs = [0]
    ys = [0]
    for node in model["nodes"]:
        xs.extend([node["x"], node["x"] + node["width"]])
        ys.extend([node["y"], node["y"] + node["height"]])
    for connector in model["connectors"]:
        xs.extend(point["x"] for point in connector["points"])
        ys.extend(point["y"] for point in connector["points"])
    padding = 40
    min_x = min(xs) - padding
    min_y = min(ys) - padding
    max_x = max(xs) + padding
    max_y = max(ys) + padding
    return min_x, min_y, max_x - min_x, max_y - min_y


def _fit_label(label: str, limit: int) -> str:
    text = " ".join(str(label).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _xml_id(value: str) -> str:
    return value.replace(":", "_").replace("/", "_")
