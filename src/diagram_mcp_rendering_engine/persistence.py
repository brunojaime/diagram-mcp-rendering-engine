from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .domain import normalize_diagram_spec, stable_diagram_id


def diagram_record(spec: dict[str, Any], svg: str | None = None) -> dict[str, Any]:
    normalized = normalize_diagram_spec(spec)
    diagram_id = normalized.get("id") or stable_diagram_id(normalized)
    return {
        "id": diagram_id,
        "schema_version": normalized["version"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec": normalized,
        "svg_cache": svg,
        "svg_cache_authoritative": False,
    }

