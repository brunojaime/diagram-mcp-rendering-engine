from __future__ import annotations

from typing import Any

from .domain import normalize_diagram_spec, slug_id
from .layout import build_render_model
from .renderer import render_diagram_svg
from .store import DiagramStore


def create_component_diagram(
    *,
    title: str = "Architecture Diagram",
    description: str = "",
    components: list[dict[str, Any]] | None = None,
    connections: list[dict[str, Any]] | None = None,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    inferred_components, inferred_connections = _infer_description(description)
    spec = normalize_diagram_spec(
        {
            "version": "1.0",
            "diagramType": "uml_component",
            "title": title,
            "layout": {"direction": "LR", "mode": "auto"},
            "components": components or inferred_components,
            "connections": connections or inferred_connections,
        }
    )
    diagram_store = store or DiagramStore()
    record = diagram_store.create(spec, title=title)
    rendered = render_diagram_svg(record["spec"])
    if rendered["valid"]:
        diagram_store.cache_svg(record["diagramId"], rendered["svg"])
    return {
        "diagramId": record["diagramId"],
        "spec": record["spec"],
        "layout": auto_layout_diagram(record["spec"]),
        "svg": rendered.get("svg", ""),
        "warnings": rendered.get("warnings", []),
        "errors": rendered.get("errors", []),
    }


def auto_layout_diagram(spec: dict[str, Any]) -> dict[str, Any]:
    model = build_render_model(spec)
    return {
        "valid": model["valid"],
        "spec": model["spec"],
        "nodes": model["nodes"],
        "connectors": model["connectors"],
        "errors": model["errors"],
        "warnings": model["warnings"],
    }


def add_component(
    diagram_id: str,
    component: dict[str, Any],
    *,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    diagram_store = store or DiagramStore()
    record = diagram_store.get(diagram_id)
    spec = normalize_diagram_spec(record["spec"])
    normalized_component = dict(component)
    if "type" in normalized_component and "template" not in normalized_component:
        normalized_component["template"] = normalized_component.pop("type")
    normalized_component.setdefault("label", normalized_component.get("id", "Component"))
    normalized_component.setdefault("template", "uml_component")
    if any(item["id"] == normalized_component["id"] for item in spec["components"]):
        raise ValueError(f"Component already exists: {normalized_component['id']}")
    spec["components"].append(normalized_component)
    record["spec"] = spec
    diagram_store.save(record, "add_component")
    return _render_persisted(diagram_store, diagram_id)


def add_connection(
    diagram_id: str,
    connection: dict[str, Any],
    *,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    diagram_store = store or DiagramStore()
    record = diagram_store.get(diagram_id)
    spec = normalize_diagram_spec(record["spec"])
    normalized_connection = dict(connection)
    normalized_connection.setdefault("id", _connection_id(normalized_connection))
    if any(item["id"] == normalized_connection["id"] for item in spec["connections"]):
        raise ValueError(f"Connection already exists: {normalized_connection['id']}")
    spec["connections"].append(normalized_connection)
    record["spec"] = spec
    diagram_store.save(record, "add_connection")
    return _render_persisted(diagram_store, diagram_id)


def move_node(
    diagram_id: str,
    node_id: str,
    position: dict[str, Any],
    *,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    diagram_store = store or DiagramStore()
    record = diagram_store.get(diagram_id)
    spec = normalize_diagram_spec(record["spec"])
    grid = int(spec.get("layout", {}).get("grid", 20))
    for component in spec["components"]:
        if component["id"] == node_id:
            component["position"] = {
                "x": _snap(float(position["x"]), grid),
                "y": _snap(float(position["y"]), grid),
            }
            component["pinned"] = True
            record["spec"] = spec
            diagram_store.save(record, "move_node")
            return _render_persisted(diagram_store, diagram_id)
    raise KeyError(f"Node not found or not movable: {node_id}")


def update_node(
    diagram_id: str,
    node_id: str,
    *,
    label: str | None = None,
    metadata: dict[str, Any] | None = None,
    template: str | None = None,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    diagram_store = store or DiagramStore()
    record = diagram_store.get(diagram_id)
    spec = normalize_diagram_spec(record["spec"])
    for component in spec["components"]:
        if component["id"] == node_id:
            if label is not None:
                component["label"] = label
            if metadata is not None:
                component["metadata"] = metadata
            if template is not None:
                component["template"] = template
            record["spec"] = spec
            diagram_store.save(record, "update_node")
            return _render_persisted(diagram_store, diagram_id)
    raise KeyError(f"Node not found: {node_id}")


def remove_element(
    diagram_id: str,
    element_id: str,
    *,
    element_type: str = "auto",
    confirm: bool = True,
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    diagram_store = store or DiagramStore()
    record = diagram_store.get(diagram_id)
    spec = normalize_diagram_spec(record["spec"])
    component_ids = {component["id"] for component in spec["components"]}
    if element_type in {"auto", "component"} and element_id in component_ids:
        affected = [
            connection["id"]
            for connection in spec["connections"]
            if connection["from"] == element_id or connection["to"] == element_id
        ]
        if not confirm:
            return {"valid": True, "wouldRemove": {"component": element_id, "connections": affected}}
        spec["components"] = [component for component in spec["components"] if component["id"] != element_id]
        spec["connections"] = [
            connection
            for connection in spec["connections"]
            if connection["from"] != element_id and connection["to"] != element_id
        ]
        record["spec"] = spec
        diagram_store.save(record, "remove_component")
        return _render_persisted(diagram_store, diagram_id)
    if element_type in {"auto", "connection"}:
        before = len(spec["connections"])
        spec["connections"] = [
            connection for connection in spec["connections"] if connection["id"] != element_id
        ]
        if len(spec["connections"]) != before:
            record["spec"] = spec
            diagram_store.save(record, "remove_connection")
            return _render_persisted(diagram_store, diagram_id)
    raise KeyError(f"Element not found: {element_id}")


def export_diagram(
    diagram_id: str,
    *,
    format: str = "svg",
    store: DiagramStore | None = None,
) -> dict[str, Any]:
    if format != "svg":
        return {
            "valid": False,
            "format": format,
            "errors": [
                {
                    "code": "UNSUPPORTED_EXPORT_FORMAT",
                    "path": "/format",
                    "message": "Only svg export is supported in the MVP.",
                    "severity": "error",
                }
            ],
            "warnings": [],
        }
    diagram_store = store or DiagramStore()
    rendered = _render_persisted(diagram_store, diagram_id)
    return {
        "diagramId": diagram_id,
        "valid": rendered["valid"],
        "format": "svg",
        "contentType": "image/svg+xml",
        "content": rendered.get("svg", ""),
        "errors": rendered.get("errors", []),
        "warnings": rendered.get("warnings", []),
    }


def _render_persisted(store: DiagramStore, diagram_id: str) -> dict[str, Any]:
    record = store.get(diagram_id)
    rendered = render_diagram_svg(record["spec"])
    if rendered["valid"]:
        store.cache_svg(diagram_id, rendered["svg"])
    return {"diagramId": diagram_id, **rendered}


def _infer_description(description: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = " ".join(str(description or "").replace("->", " connects to ").split())
    lower = text.lower()
    marker = " connects to "
    if marker not in lower:
        return [], []
    source_label = text[: lower.index(marker)].strip()
    rest = text[lower.index(marker) + len(marker) :].strip()
    target_label = rest
    interface = "Interface"
    for separator in (" through ", " via ", " over ", " using "):
        index = rest.lower().find(separator)
        if index >= 0:
            target_label = rest[:index].strip()
            interface = rest[index + len(separator) :].strip()
            break
    if not source_label or not target_label:
        return [], []
    source_id = slug_id(source_label, fallback="consumer")
    target_id = slug_id(target_label, fallback="provider")
    return (
        [
            {"id": source_id, "label": source_label, "template": "uml_component"},
            {"id": target_id, "label": target_label, "template": "uml_component"},
        ],
        [
            {
                "id": f"{source_id}_to_{target_id}",
                "from": source_id,
                "to": target_id,
                "interface": interface,
            }
        ],
    )


def _connection_id(connection: dict[str, Any]) -> str:
    return f"{connection.get('from', 'from')}_to_{connection.get('to', 'to')}"


def _snap(value: float, grid: int) -> int:
    return int(round(value / grid) * grid)
