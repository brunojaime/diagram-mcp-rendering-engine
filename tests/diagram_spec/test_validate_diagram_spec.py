from __future__ import annotations

from diagram_mcp_rendering_engine.domain import validate_diagram_spec


def test_valid_component_diagram_passes(component_diagram_spec) -> None:
    result = validate_diagram_spec(component_diagram_spec())

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["spec"]["id"].startswith("diagram_")


def test_connection_to_missing_component_fails(component_diagram_spec) -> None:
    spec = component_diagram_spec()
    spec["connections"][0]["to"] = "missing_api"

    result = validate_diagram_spec(spec)

    assert result["valid"] is False
    assert any(error["code"] == "MISSING_COMPONENT" for error in result["errors"])

