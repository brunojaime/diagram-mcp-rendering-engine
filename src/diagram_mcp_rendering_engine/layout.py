from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .domain import DEFAULT_LAYOUT, normalize_diagram_spec, validate_diagram_spec
from .templates import PROVIDED_REQUIRED_INTERFACE, UML_COMPONENT


def build_render_model(spec: dict[str, Any]) -> dict[str, Any]:
    validation = validate_diagram_spec(spec)
    if not validation["valid"]:
        return {
            "valid": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "spec": validation["spec"],
            "nodes": [],
            "connectors": [],
        }

    normalized = validation["spec"]
    component_nodes = _layout_components(normalized)
    interface_nodes = _layout_interfaces(normalized, component_nodes)
    connectors = _route_connectors(normalized, component_nodes, interface_nodes)
    warnings = validation["warnings"] + _overlap_warnings(component_nodes)
    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "spec": normalized,
        "nodes": [*component_nodes.values(), *interface_nodes.values()],
        "connectors": connectors,
    }


def _layout_components(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    layout = {**DEFAULT_LAYOUT, **spec.get("layout", {})}
    depths = _component_depths(spec)
    columns: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for component in sorted(spec["components"], key=lambda item: item["id"]):
        columns[depths.get(component["id"], 0)].append(component)

    nodes: dict[str, dict[str, Any]] = {}
    for depth in sorted(columns):
        for row, component in enumerate(columns[depth]):
            position = component.get("position") if component.get("pinned") else None
            x = position["x"] if position else 40 + depth * layout["column_gap"]
            y = position["y"] if position else 40 + row * layout["row_gap"]
            nodes[component["id"]] = {
                "id": component["id"],
                "type": "component",
                "template": "uml_component",
                "label": component["label"],
                "x": int(x),
                "y": int(y),
                "width": UML_COMPONENT.width,
                "height": UML_COMPONENT.height,
                "pinned": bool(component.get("pinned")),
            }
    return nodes


def _component_depths(spec: dict[str, Any]) -> dict[str, int]:
    ids = {component["id"] for component in spec["components"]}
    incoming: dict[str, set[str]] = {component_id: set() for component_id in ids}
    outgoing: dict[str, set[str]] = {component_id: set() for component_id in ids}
    for connection in spec["connections"]:
        outgoing[connection["from"]].add(connection["to"])
        incoming[connection["to"]].add(connection["from"])

    depths = {component_id: 0 for component_id in ids}
    queue = deque(sorted(component_id for component_id in ids if not incoming[component_id]))
    if not queue:
        queue = deque(sorted(ids))

    seen: set[str] = set()
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        for target in sorted(outgoing[current]):
            depths[target] = max(depths[target], depths[current] + 1)
            incoming[target].discard(current)
            if not incoming[target]:
                queue.append(target)
    return depths


def _layout_interfaces(
    spec: dict[str, Any],
    component_nodes: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    interface_nodes: dict[str, dict[str, Any]] = {}
    for connection in sorted(spec["connections"], key=lambda item: item["id"]):
        consumer = component_nodes[connection["from"]]
        provider = component_nodes[connection["to"]]
        interface_id = interface_node_id(connection["id"])
        left = min(consumer["x"] + consumer["width"], provider["x"])
        right = max(consumer["x"] + consumer["width"], provider["x"])
        x = int(left + (right - left - PROVIDED_REQUIRED_INTERFACE.width) / 2)
        y = int((consumer["y"] + provider["y"]) / 2 + 13)
        interface_nodes[interface_id] = {
            "id": interface_id,
            "type": "provided_required_interface",
            "template": "provided_required_interface",
            "connection_id": connection["id"],
            "label": connection.get("label") or connection["interface"],
            "interface": connection["interface"],
            "x": x,
            "y": y,
            "width": PROVIDED_REQUIRED_INTERFACE.width,
            "height": PROVIDED_REQUIRED_INTERFACE.height,
            "pinned": False,
        }
    return interface_nodes


def _route_connectors(
    spec: dict[str, Any],
    component_nodes: dict[str, dict[str, Any]],
    interface_nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    port_order = _port_order(spec)
    connectors: list[dict[str, Any]] = []
    for connection in sorted(spec["connections"], key=lambda item: item["id"]):
        consumer = component_nodes[connection["from"]]
        provider = component_nodes[connection["to"]]
        interface = interface_nodes[interface_node_id(connection["id"])]
        consumer_point = _component_port(
            consumer,
            "right",
            port_order[(consumer["id"], "right")].index(connection["id"]),
            len(port_order[(consumer["id"], "right")]),
        )
        provider_point = _component_port(
            provider,
            "left",
            port_order[(provider["id"], "left")].index(connection["id"]),
            len(port_order[(provider["id"], "left")]),
        )
        required_point = _interface_anchor(interface, "required")
        provided_point = _interface_anchor(interface, "provided")
        connectors.append(
            _connector(
                f"{connection['id']}_required",
                connection["id"],
                consumer["id"],
                interface["id"],
                "consumer_to_required",
                consumer_point,
                required_point,
            )
        )
        connectors.append(
            _connector(
                f"{connection['id']}_provided",
                connection["id"],
                interface["id"],
                provider["id"],
                "provided_to_provider",
                provided_point,
                provider_point,
            )
        )
    return connectors


def _port_order(spec: dict[str, Any]) -> dict[tuple[str, str], list[str]]:
    ports: dict[tuple[str, str], list[str]] = defaultdict(list)
    for connection in sorted(spec["connections"], key=lambda item: item["id"]):
        ports[(connection["from"], "right")].append(connection["id"])
        ports[(connection["to"], "left")].append(connection["id"])
    return ports


def _component_port(node: dict[str, Any], side: str, index: int, count: int) -> dict[str, Any]:
    y = node["y"] + int(round((index + 1) * node["height"] / (count + 1)))
    x = node["x"] if side == "left" else node["x"] + node["width"]
    return {
        "node_id": node["id"],
        "anchor": side,
        "x": x,
        "y": y,
        "port_index": index,
        "port_count": count,
    }


def _interface_anchor(node: dict[str, Any], anchor: str) -> dict[str, Any]:
    if anchor == "required":
        return {
            "node_id": node["id"],
            "anchor": anchor,
            "x": node["x"],
            "y": node["y"] + node["height"] // 2,
        }
    return {
        "node_id": node["id"],
        "anchor": anchor,
        "x": node["x"] + node["width"],
        "y": node["y"] + node["height"] // 2,
    }


def _connector(
    connector_id: str,
    semantic_connection_id: str,
    from_node: str,
    to_node: str,
    role: str,
    start: dict[str, Any],
    end: dict[str, Any],
) -> dict[str, Any]:
    points = orthogonal_points(start["x"], start["y"], end["x"], end["y"])
    return {
        "id": connector_id,
        "semantic_connection_id": semantic_connection_id,
        "from_node": from_node,
        "to_node": to_node,
        "role": role,
        "start": start,
        "end": end,
        "points": points,
        "path": " ".join(
            [f"M {points[0]['x']} {points[0]['y']}"]
            + [f"L {point['x']} {point['y']}" for point in points[1:]]
        ),
    }


def orthogonal_points(x1: int, y1: int, x2: int, y2: int) -> list[dict[str, int]]:
    if y1 == y2:
        return [{"x": x1, "y": y1}, {"x": x2, "y": y2}]
    mid_x = int((x1 + x2) / 2)
    return [
        {"x": x1, "y": y1},
        {"x": mid_x, "y": y1},
        {"x": mid_x, "y": y2},
        {"x": x2, "y": y2},
    ]


def interface_node_id(connection_id: str) -> str:
    return f"interface_{connection_id}"


def _overlap_warnings(nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    values = list(nodes.values())
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            if _overlaps(left, right):
                warnings.append(
                    {
                        "code": "NODE_OVERLAP",
                        "path": f"/components/{left['id']}",
                        "message": f"Node '{left['id']}' overlaps '{right['id']}'.",
                        "severity": "warning",
                    }
                )
    return warnings


def _overlaps(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return not (
        left["x"] + left["width"] <= right["x"]
        or right["x"] + right["width"] <= left["x"]
        or left["y"] + left["height"] <= right["y"]
        or right["y"] + right["height"] <= left["y"]
    )
