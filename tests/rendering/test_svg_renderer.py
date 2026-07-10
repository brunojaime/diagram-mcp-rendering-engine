from __future__ import annotations

from diagram_mcp_rendering_engine.renderer import render_diagram_svg


def test_render_diagram_svg_is_deterministic(component_diagram_spec) -> None:
    first = render_diagram_svg(component_diagram_spec())
    second = render_diagram_svg(component_diagram_spec())

    assert first["valid"] is True
    assert first["svg"] == second["svg"]


def test_svg_can_be_consumed_without_frontend_uml_logic(component_diagram_spec) -> None:
    svg = render_diagram_svg(component_diagram_spec())["svg"]

    assert 'data-renderer="diagram-mcp-rendering-engine"' in svg
    assert 'data-node-id="browser"' in svg
    assert 'data-node-type="uml_component"' in svg
    assert 'data-connection-id="browser_gateway_http"' in svg
    assert "<script" not in svg.lower()
    assert "<foreignObject" not in svg

