# Diagram MCP Rendering Engine

Spec-first repository for a local HTTPS MCP server that generates, validates,
lays out, renders, edits, and exports deterministic UML component diagrams.

The canonical product contract currently lives in:

- `specs/016-diagram-mcp-rendering-engine/spec.md`
- `specs/016-diagram-mcp-rendering-engine/plan.md`
- `specs/016-diagram-mcp-rendering-engine/tasks.md`
- `specs/016-diagram-mcp-rendering-engine/traceability.yaml`

The MVP implementation keeps `DiagramSpec` as the source of truth and exposes
deterministic validation, layout, SVG rendering, node movement, diagnostics, and
SVG export through pure Python functions and MCP tools.

## Development

```bash
uv sync --extra dev
uv run pytest
```

## Python API

```python
from diagram_mcp_rendering_engine.renderer import render_diagram_svg

result = render_diagram_svg({
    "version": "1.0",
    "diagram_type": "uml_component",
    "components": [
        {"id": "browser", "label": "Browser"},
        {"id": "api_server", "label": "API Server"},
    ],
    "connections": [
        {"id": "browser_api_http", "from": "browser", "to": "api_server", "interface": "HTTP"},
    ],
})

svg = result["svg"]
```

## Running The MCP Server

From a checkout:

```bash
uv run diagram-mcp-rendering-engine --transport https \
  --host 127.0.0.1 \
  --port 8765 \
  --certfile /path/to/localhost.pem \
  --keyfile /path/to/localhost-key.pem
```

After installing the package into an environment:

```bash
diagram-mcp-rendering-engine --transport https --certfile /path/to/localhost.pem --keyfile /path/to/localhost-key.pem
```

The command defaults to stdio for MCP client compatibility:

```bash
uv run diagram-mcp-rendering-engine --transport stdio
```

HTTPS loopback mode fails clearly when certificate/key configuration is missing.
The MCP tools include:

- `create_component_diagram`
- `validate_diagram_spec`
- `auto_layout_diagram`
- `add_component`
- `add_connection`
- `move_node`
- `update_node`
- `remove_element`
- `render_diagram_svg`
- `export_diagram`
- `diagram_diagnostics`

For HTTPS loopback mode, set the transport and TLS configuration:

```bash
DIAGRAM_MCP_TRANSPORT=https \
DIAGRAM_MCP_HOST=127.0.0.1 \
DIAGRAM_MCP_PORT=8765 \
DIAGRAM_MCP_TLS_CERT=/path/to/localhost.pem \
DIAGRAM_MCP_TLS_KEY=/path/to/localhost-key.pem \
uv run diagram-mcp-rendering-engine
```

HTTPS mode intentionally rejects public bind hosts and requires certificate/key
paths before startup.

Persisted diagram tools store records under `.data/diagrams` by default. Set
`DIAGRAM_MCP_STORE_DIR` to use a different local directory.
