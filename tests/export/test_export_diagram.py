from __future__ import annotations

from diagram_mcp_rendering_engine.export import export_diagram


def test_export_diagram_returns_self_contained_svg(component_diagram_spec) -> None:
    result = export_diagram(component_diagram_spec(), "svg")

    assert result["ok"] is True
    assert result["mime_type"] == "image/svg+xml"
    assert result["filename"].endswith(".svg")
    assert result["data"].startswith("<svg ")
    assert "<style>" in result["data"]

