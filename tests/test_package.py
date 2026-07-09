from diagram_mcp_rendering_engine import __version__
from diagram_mcp_rendering_engine.server import implementation_status


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_implementation_status_points_to_spec() -> None:
    status = implementation_status()
    assert status["status"] == "spec_scaffold"
    assert status["spec_id"] == "016-diagram-mcp-rendering-engine"
