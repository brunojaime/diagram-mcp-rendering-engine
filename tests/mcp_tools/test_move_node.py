from __future__ import annotations

from diagram_mcp_rendering_engine.editor import move_node
from diagram_mcp_rendering_engine.layout import build_render_model


def test_move_node_persists_position_and_pins_node(component_diagram_spec) -> None:
    result = move_node(component_diagram_spec(), "gateway", 133, 207)
    gateway = next(component for component in result["spec"]["components"] if component["id"] == "gateway")

    assert result["ok"] is True
    assert gateway["position"] == {"x": 140, "y": 200}
    assert gateway["pinned"] is True


def test_move_node_reroutes_connections_without_changing_semantics(component_diagram_spec) -> None:
    before = build_render_model(component_diagram_spec())
    moved = move_node(component_diagram_spec(), "gateway", 320, 220)["spec"]
    after = build_render_model(moved)

    assert [connector["semantic_connection_id"] for connector in before["connectors"]] == [
        connector["semantic_connection_id"] for connector in after["connectors"]
    ]
    before_gateway_path = next(
        connector["path"] for connector in before["connectors"] if connector["id"] == "browser_gateway_http_required"
    )
    after_gateway_path = next(
        connector["path"] for connector in after["connectors"] if connector["id"] == "browser_gateway_http_required"
    )
    assert before_gateway_path != after_gateway_path
