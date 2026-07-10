from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .domain import normalize_diagram_spec, validate_diagram_spec


def move_node(spec: dict[str, Any], node_id: str, x: float, y: float) -> dict[str, Any]:
    normalized = normalize_diagram_spec(spec)
    grid = int(normalized.get("layout", {}).get("grid", 20))
    snapped = {"x": _snap(x, grid), "y": _snap(y, grid)}
    for component in normalized["components"]:
        if component["id"] == node_id:
            component["position"] = snapped
            component["pinned"] = True
            validation = validate_diagram_spec(normalized)
            return {
                "ok": validation["valid"],
                "spec": validation["spec"],
                "operation": {
                    "type": "move_node",
                    "node_id": node_id,
                    "position": snapped,
                    "pinned": True,
                },
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }
    return {
        "ok": False,
        "spec": normalized,
        "operation": None,
        "errors": [
            {
                "code": "NODE_NOT_FOUND",
                "path": "/components",
                "message": f"Node '{node_id}' does not exist.",
                "severity": "error",
            }
        ],
        "warnings": [],
    }


def selection_for_svg_id(render_model: dict[str, Any], svg_node_id: str) -> dict[str, Any]:
    raw_id = svg_node_id.removeprefix("node-").replace("_", ":", 1)
    for node in render_model.get("nodes", []):
        if node["id"] == raw_id or f"node-{node['id'].replace(':', '_')}" == svg_node_id:
            return {"ok": True, "selection": node}
    return {
        "ok": False,
        "selection": None,
        "errors": [
            {
                "code": "SELECTION_NOT_FOUND",
                "path": "/svg",
                "message": f"SVG node id '{svg_node_id}' is not mapped to a diagram element.",
                "severity": "error",
            }
        ],
    }


@dataclass
class DiagramHistory:
    initial_spec: dict[str, Any]
    undo_stack: list[dict[str, Any]] = field(default_factory=list)
    redo_stack: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_spec = normalize_diagram_spec(self.initial_spec)

    def apply_move(self, node_id: str, x: float, y: float) -> dict[str, Any]:
        self.undo_stack.append(copy.deepcopy(self.current_spec))
        self.redo_stack.clear()
        result = move_node(self.current_spec, node_id, x, y)
        if result["ok"]:
            self.current_spec = result["spec"]
        else:
            self.undo_stack.pop()
        return result

    def undo(self) -> dict[str, Any]:
        if not self.undo_stack:
            return {"ok": False, "spec": self.current_spec}
        self.redo_stack.append(copy.deepcopy(self.current_spec))
        self.current_spec = self.undo_stack.pop()
        return {"ok": True, "spec": self.current_spec}

    def redo(self) -> dict[str, Any]:
        if not self.redo_stack:
            return {"ok": False, "spec": self.current_spec}
        self.undo_stack.append(copy.deepcopy(self.current_spec))
        self.current_spec = self.redo_stack.pop()
        return {"ok": True, "spec": self.current_spec}


def _snap(value: float, grid: int) -> int:
    return int(round(value / grid) * grid)

