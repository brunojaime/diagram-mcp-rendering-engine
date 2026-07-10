from __future__ import annotations

from diagram_mcp_rendering_engine.layout import build_render_model
from diagram_mcp_rendering_engine.renderer import render_diagram_svg


def test_socket_is_on_consumer_side_and_lollipop_on_provider_side(component_diagram_spec) -> None:
    model = build_render_model(component_diagram_spec())
    first_interface = next(node for node in model["nodes"] if node["id"] == "interface_browser_gateway_http")
    consumer_connector = next(
        connector for connector in model["connectors"] if connector["id"] == "browser_gateway_http_required"
    )
    provider_connector = next(
        connector for connector in model["connectors"] if connector["id"] == "browser_gateway_http_provided"
    )
    svg = render_diagram_svg(component_diagram_spec())["svg"]

    assert consumer_connector["end"]["anchor"] == "required"
    assert provider_connector["start"]["anchor"] == "provided"
    assert consumer_connector["end"]["x"] == first_interface["x"]
    assert provider_connector["start"]["x"] == first_interface["x"] + first_interface["width"]
    assert 'data-anchor="required"' in svg
    assert 'data-anchor="provided"' in svg
