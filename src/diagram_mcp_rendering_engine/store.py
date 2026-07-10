from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain import normalize_diagram_spec, stable_diagram_id, validate_diagram_spec


DEFAULT_STORE_DIR = ".data/diagrams"


class DiagramStore:
    def __init__(self, root: str | Path | None = None) -> None:
        configured = root or os.environ.get("DIAGRAM_MCP_STORE_DIR") or DEFAULT_STORE_DIR
        self.root = Path(configured).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, spec: dict[str, Any], *, title: str | None = None) -> dict[str, Any]:
        normalized = normalize_diagram_spec(spec)
        validation = validate_diagram_spec(normalized)
        if not validation["valid"]:
            raise ValueError(validation["errors"][0]["message"])
        normalized = validation["spec"]
        if title:
            normalized["title"] = title
        record = {
            "diagramId": normalized.get("id") or stable_diagram_id(normalized),
            "schemaVersion": normalized["version"],
            "createdAt": _now(),
            "updatedAt": _now(),
            "spec": normalized,
            "history": [{"operation": "create_component_diagram", "timestamp": _now()}],
            "svgCache": None,
            "svgCacheAuthoritative": False,
        }
        self._write(record)
        return record

    def get(self, diagram_id: str) -> dict[str, Any]:
        path = self._path(diagram_id)
        if not path.is_file():
            raise KeyError(f"Diagram not found: {diagram_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, record: dict[str, Any], operation: str) -> dict[str, Any]:
        validation = validate_diagram_spec(record["spec"])
        if not validation["valid"]:
            raise ValueError(validation["errors"][0]["message"])
        record["spec"] = validation["spec"]
        record["updatedAt"] = _now()
        record.setdefault("history", []).append({"operation": operation, "timestamp": _now()})
        record["svgCache"] = None
        record["svgCacheAuthoritative"] = False
        self._write(record)
        return record

    def cache_svg(self, diagram_id: str, svg: str) -> None:
        record = self.get(diagram_id)
        record["svgCache"] = svg
        record["svgCacheAuthoritative"] = False
        record["updatedAt"] = _now()
        self._write(record)

    def _path(self, diagram_id: str) -> Path:
        return self.root / f"{diagram_id}.json"

    def _write(self, record: dict[str, Any]) -> None:
        self._path(record["diagramId"]).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
