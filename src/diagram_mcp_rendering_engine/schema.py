from __future__ import annotations

from jsonschema import Draft202012Validator


DIAGRAM_SPEC_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.local/diagram-mcp-rendering-engine/diagram-spec.schema.json",
    "title": "DiagramSpec",
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "diagram_type", "components", "connections"],
    "properties": {
        "id": {"type": "string", "pattern": r"^[a-z][a-z0-9_:-]*$"},
        "version": {"type": "string", "const": "1.0"},
        "diagram_type": {"type": "string", "const": "uml_component"},
        "title": {"type": "string", "maxLength": 120},
        "components": {
            "type": "array",
            "items": {"$ref": "#/$defs/component"},
        },
        "connections": {
            "type": "array",
            "items": {"$ref": "#/$defs/connection"},
        },
        "layout": {"$ref": "#/$defs/layout"},
        "metadata": {
            "type": "object",
            "additionalProperties": {
                "type": ["string", "number", "boolean", "null"],
            },
        },
    },
    "$defs": {
        "component": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "label"],
            "properties": {
                "id": {"type": "string", "pattern": r"^[a-z][a-z0-9_:-]*$"},
                "label": {"type": "string", "minLength": 1, "maxLength": 120},
                "template": {"type": "string", "const": "uml_component"},
                "position": {"$ref": "#/$defs/position"},
                "pinned": {"type": "boolean"},
                "metadata": {
                    "type": "object",
                    "additionalProperties": {
                        "type": ["string", "number", "boolean", "null"],
                    },
                },
            },
        },
        "connection": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "from", "to", "interface"],
            "properties": {
                "id": {"type": "string", "pattern": r"^[a-z][a-z0-9_:-]*$"},
                "from": {"type": "string", "pattern": r"^[a-z][a-z0-9_:-]*$"},
                "to": {"type": "string", "pattern": r"^[a-z][a-z0-9_:-]*$"},
                "interface": {"type": "string", "minLength": 1, "maxLength": 80},
                "label": {"type": "string", "maxLength": 120},
                "metadata": {
                    "type": "object",
                    "additionalProperties": {
                        "type": ["string", "number", "boolean", "null"],
                    },
                },
            },
        },
        "layout": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "direction": {"type": "string", "const": "LR"},
                "mode": {"type": "string", "enum": ["auto", "manual"]},
                "grid": {"type": "integer", "minimum": 1, "maximum": 200},
                "column_gap": {"type": "integer", "minimum": 80, "maximum": 800},
                "row_gap": {"type": "integer", "minimum": 40, "maximum": 800},
            },
        },
        "position": {
            "type": "object",
            "additionalProperties": False,
            "required": ["x", "y"],
            "properties": {
                "x": {"type": "number", "minimum": 0, "maximum": 100000},
                "y": {"type": "number", "minimum": 0, "maximum": 100000},
            },
        },
    },
}


DIAGRAM_SPEC_VALIDATOR = Draft202012Validator(DIAGRAM_SPEC_SCHEMA)
