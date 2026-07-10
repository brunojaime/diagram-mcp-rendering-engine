from __future__ import annotations

from diagram_mcp_rendering_engine.layout import build_render_model


def test_browser_gateway_database_and_api_server_layout_left_to_right(component_diagram_spec) -> None:
    model = build_render_model(component_diagram_spec())
    nodes = {node["id"]: node for node in model["nodes"] if node["type"] == "component"}

    assert model["valid"] is True
    assert nodes["browser"]["x"] < nodes["gateway"]["x"]
    assert nodes["gateway"]["x"] < nodes["api_server"]["x"]
    assert nodes["api_server"]["x"] < nodes["database"]["x"]

