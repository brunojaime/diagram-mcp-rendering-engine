from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from jsonschema import ValidationError

from .schema import DIAGRAM_SPEC_VALIDATOR
from .templates import UML_COMPONENT, get_template


ID_PATTERN = re.compile(r"^[a-z][a-z0-9_:-]*$")
DEFAULT_LAYOUT = {"direction": "LR", "grid": 20, "column_gap": 320, "row_gap": 120}


def stable_diagram_id(spec: dict[str, Any]) -> str:
    material = copy.deepcopy(spec)
    material.pop("id", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return "diagram_" + hashlib.sha256(encoded).hexdigest()[:12]


def normalize_diagram_spec(spec: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(spec)
    if "diagramType" in normalized and "diagram_type" not in normalized:
        normalized["diagram_type"] = normalized.pop("diagramType")
    normalized.setdefault("version", "1.0")
    normalized.setdefault("diagram_type", "uml_component")
    normalized.setdefault("components", [])
    normalized.setdefault("connections", [])
    normalized["layout"] = {**DEFAULT_LAYOUT, **normalized.get("layout", {})}
    normalized.setdefault("id", stable_diagram_id(normalized))

    for component in normalized["components"]:
        if "type" in component and "template" not in component:
            component["template"] = component.pop("type")
        component.setdefault("label", component.get("id", "component"))
        component.setdefault("template", UML_COMPONENT.id)
        component.setdefault("pinned", bool(component.get("position")))

    for index, connection in enumerate(normalized["connections"]):
        if "id" not in connection:
            from_id = connection.get("from", "from")
            to_id = connection.get("to", "to")
            interface = _slug(connection.get("interface", f"interface_{index + 1}"))
            connection["id"] = f"conn_{from_id}_{interface}_{to_id}"

    return normalized


def validate_diagram_spec(spec: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_diagram_spec(spec)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for error in sorted(DIAGRAM_SPEC_VALIDATOR.iter_errors(normalized), key=_schema_error_key):
        errors.append(_schema_error_to_issue(error))

    component_ids: set[str] = set()
    for index, component in enumerate(normalized.get("components", [])):
        component_id = component.get("id")
        if component_id in component_ids:
            errors.append(
                _issue(
                    "DUPLICATE_COMPONENT_ID",
                    f"/components/{index}/id",
                    f"Component id '{component_id}' is duplicated.",
                )
            )
        if not get_template(component.get("template", "")):
            errors.append(
                _issue(
                    "UNKNOWN_TEMPLATE",
                    f"/components/{index}/template",
                    f"Template '{component.get('template')}' is not registered.",
                )
            )
        component_ids.add(component_id)

    connection_ids: set[str] = set()
    for index, connection in enumerate(normalized.get("connections", [])):
        connection_id = connection.get("id")
        from_id = connection.get("from")
        to_id = connection.get("to")
        if connection_id in connection_ids:
            errors.append(
                _issue(
                    "DUPLICATE_CONNECTION_ID",
                    f"/connections/{index}/id",
                    f"Connection id '{connection_id}' is duplicated.",
                )
            )
        connection_ids.add(connection_id)
        if from_id not in component_ids:
            errors.append(
                _issue(
                    "MISSING_COMPONENT",
                    f"/connections/{index}/from",
                    f"Connection '{connection_id}' references missing consumer '{from_id}'.",
                )
            )
        if to_id not in component_ids:
            errors.append(
                _issue(
                    "MISSING_COMPONENT",
                    f"/connections/{index}/to",
                    f"Connection '{connection_id}' references missing provider '{to_id}'.",
                )
            )
        if from_id == to_id and from_id in component_ids:
            errors.append(
                _issue(
                    "UNSUPPORTED_SELF_CONNECTION",
                    f"/connections/{index}",
                    f"Connection '{connection_id}' cannot connect a component to itself.",
                )
            )

    if not normalized["components"]:
        warnings.append(
            _issue(
                "EMPTY_DIAGRAM",
                "/components",
                "Diagram has no components; render output will contain only an empty canvas.",
                severity="warning",
            )
        )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "spec": normalized,
    }


def _slug(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    if not text or not text[0].isalpha():
        text = "interface_" + text
    return text


def slug_id(value: object, *, fallback: str = "item") -> str:
    text = _slug(value)
    return text if text != "interface_" else fallback


def _schema_error_key(error: ValidationError) -> tuple[str, str]:
    return ("/" + "/".join(str(part) for part in error.path), error.message)


def _schema_error_to_issue(error: ValidationError) -> dict[str, Any]:
    path = "/" + "/".join(str(part) for part in error.path)
    validator = str(error.validator).upper()
    return _issue(f"SCHEMA_{validator}", path, error.message)


def _issue(
    code: str,
    path: str,
    message: str,
    *,
    severity: str = "error",
) -> dict[str, Any]:
    return {"code": code, "path": path, "message": message, "severity": severity}
