from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

mcp = FastMCP(
    "Diagram MCP Rendering Engine",
    instructions=(
        "Spec-first MCP server for deterministic UML component diagram rendering. "
        "Implementation should follow specs/016-diagram-mcp-rendering-engine."
    ),
    json_response=True,
    log_level="WARNING",
)


@mcp.tool(annotations=_READ_ONLY)
def implementation_status() -> dict[str, object]:
    """Return the current implementation status for this scaffold."""
    return {
        "status": "spec_scaffold",
        "spec_id": "016-diagram-mcp-rendering-engine",
        "implemented_tools": [],
        "next_tasks": [
            "T001 Define DiagramSpec JSON schema",
            "T006 Define local HTTPS server configuration",
            "T017 Define SVG document contract",
        ],
    }


def main() -> None:
    """Run the MCP server using the SDK's default stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
