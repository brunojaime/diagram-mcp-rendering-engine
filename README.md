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

