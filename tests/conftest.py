from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def component_diagram_spec() -> dict[str, Any]:
    def build() -> dict[str, Any]:
        return {
            "version": "1.0",
            "diagram_type": "uml_component",
            "title": "Browser to API",
            "layout": {"direction": "LR", "grid": 20},
            "components": [
                {"id": "browser", "label": "Browser"},
                {"id": "gateway", "label": "Gateway"},
                {"id": "api_server", "label": "API Server"},
                {"id": "database", "label": "Database"},
            ],
            "connections": [
                {
                    "id": "browser_gateway_http",
                    "from": "browser",
                    "to": "gateway",
                    "interface": "HTTP",
                },
                {
                    "id": "gateway_api_json",
                    "from": "gateway",
                    "to": "api_server",
                    "interface": "JSON API",
                },
                {
                    "id": "api_database_sql",
                    "from": "api_server",
                    "to": "database",
                    "interface": "SQL",
                },
            ],
        }

    return build


@pytest.fixture
def fanout_diagram_spec() -> dict[str, Any]:
    def build() -> dict[str, Any]:
        spec = {
            "version": "1.0",
            "diagram_type": "uml_component",
            "title": "Fanout",
            "layout": {"direction": "LR", "grid": 20},
            "components": [
                {"id": "browser", "label": "Browser"},
                {"id": "gateway", "label": "Gateway"},
                {"id": "api_server", "label": "API Server"},
                {"id": "metrics", "label": "Metrics"},
            ],
            "connections": [
                {
                    "id": "browser_gateway_http",
                    "from": "browser",
                    "to": "gateway",
                    "interface": "HTTP",
                },
                {
                    "id": "gateway_api_json",
                    "from": "gateway",
                    "to": "api_server",
                    "interface": "JSON API",
                },
                {
                    "id": "gateway_metrics_events",
                    "from": "gateway",
                    "to": "metrics",
                    "interface": "Events",
                },
            ],
        }
        return spec

    return build
