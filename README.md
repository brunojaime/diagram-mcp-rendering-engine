# Diagram MCP Rendering Engine

Spec-first repository for a local HTTPS MCP server that generates, validates,
lays out, renders, edits, and exports deterministic UML component diagrams.

The canonical product contract currently lives in:

- `specs/016-diagram-mcp-rendering-engine/spec.md`
- `specs/016-diagram-mcp-rendering-engine/plan.md`
- `specs/016-diagram-mcp-rendering-engine/tasks.md`
- `specs/016-diagram-mcp-rendering-engine/traceability.yaml`

This repo is intentionally scaffolded without a partial renderer. The first
implementation pass should start from the SDD tasks and keep `DiagramSpec` as
the source of truth instead of emitting free-form SVG from an LLM.

## Development

```bash
uv sync --extra dev
uv run pytest
```

## Running The MCP Server

From a checkout:

```bash
uv run diagram-mcp-rendering-engine
```

After installing the package into an environment:

```bash
diagram-mcp-rendering-engine
```

The current command runs the scaffold server over the MCP SDK default stdio
transport. The HTTPS localhost transport, tool surface, renderer, and export
behavior are specified in `specs/016-diagram-mcp-rendering-engine/` and should
be implemented through the planned SDD tasks.
