from __future__ import annotations

from diagram_mcp_rendering_engine.engine import (
    add_component,
    add_connection,
    create_component_diagram,
    export_diagram,
    move_node,
    remove_element,
    update_node,
)
from diagram_mcp_rendering_engine.store import DiagramStore


def test_persisted_diagram_tool_flow(tmp_path) -> None:
    store = DiagramStore(tmp_path)

    created = create_component_diagram(
        title="Persisted",
        description="Browser connects to API Server via HTTP",
        store=store,
    )
    diagram_id = created["diagramId"]

    add_component(diagram_id, {"id": "database", "label": "Database"}, store=store)
    add_connection(
        diagram_id,
        {"id": "api_database_sql", "from": "api_server", "to": "database", "interface": "SQL"},
        store=store,
    )
    moved = move_node(diagram_id, "api_server", {"x": 433, "y": 155}, store=store)
    updated = update_node(diagram_id, "api_server", label="API", store=store)
    preview = remove_element(diagram_id, "database", confirm=False, store=store)
    exported = export_diagram(diagram_id, store=store)

    api_server = next(component for component in moved["spec"]["components"] if component["id"] == "api_server")
    assert updated["valid"] is True
    assert api_server["position"] == {"x": 440, "y": 160}
    assert preview["wouldRemove"]["connections"] == ["api_database_sql"]
    assert exported["valid"] is True
    assert exported["contentType"] == "image/svg+xml"
    assert exported["content"].startswith("<svg ")
