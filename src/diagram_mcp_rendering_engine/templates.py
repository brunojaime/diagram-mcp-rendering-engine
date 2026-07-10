from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    id: str
    width: int
    height: int
    anchors: tuple[str, ...]


UML_COMPONENT = Template(
    id="uml_component",
    width=180,
    height=90,
    anchors=("left", "right", "top", "bottom"),
)

PROVIDED_REQUIRED_INTERFACE = Template(
    id="provided_required_interface",
    width=128,
    height=64,
    anchors=("required", "provided"),
)

TEMPLATE_REGISTRY: dict[str, Template] = {
    UML_COMPONENT.id: UML_COMPONENT,
    PROVIDED_REQUIRED_INTERFACE.id: PROVIDED_REQUIRED_INTERFACE,
}


def get_template(template_id: str) -> Template | None:
    return TEMPLATE_REGISTRY.get(template_id)
