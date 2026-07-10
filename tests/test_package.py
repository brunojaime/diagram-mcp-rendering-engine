from importlib.metadata import entry_points

from diagram_mcp_rendering_engine import __version__
from diagram_mcp_rendering_engine.server import implementation_status, main


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_implementation_status_points_to_spec() -> None:
    status = implementation_status()
    assert status["status"] == "spec_scaffold"
    assert status["spec_id"] == "016-diagram-mcp-rendering-engine"


def test_console_script_targets_server_main() -> None:
    scripts = entry_points(group="console_scripts")
    command = next(
        script
        for script in scripts
        if script.name == "diagram-mcp-rendering-engine"
    )
    assert command.value == "diagram_mcp_rendering_engine.server:main"
    assert command.load() is main
