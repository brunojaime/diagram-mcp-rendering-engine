from __future__ import annotations

from diagram_mcp_rendering_engine.layout import build_render_model


def test_all_connector_endpoints_resolve_to_declared_anchors(component_diagram_spec) -> None:
    model = build_render_model(component_diagram_spec())
    anchors = {
        (connector["start"]["node_id"], connector["start"]["anchor"])
        for connector in model["connectors"]
    } | {
        (connector["end"]["node_id"], connector["end"]["anchor"])
        for connector in model["connectors"]
    }

    assert ("browser", "right") in anchors
    assert ("gateway", "left") in anchors
    assert any(anchor == "required" for _, anchor in anchors)
    assert any(anchor == "provided" for _, anchor in anchors)


def test_multiple_outputs_use_distinct_dynamic_ports(fanout_diagram_spec) -> None:
    model = build_render_model(fanout_diagram_spec())
    gateway_outputs = [
        connector["start"]
        for connector in model["connectors"]
        if connector["start"]["node_id"] == "gateway" and connector["start"]["anchor"] == "right"
    ]

    assert len(gateway_outputs) == 2
    assert len({point["y"] for point in gateway_outputs}) == 2
