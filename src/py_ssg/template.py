"""Template engine with HTML component partials support.

Supports:
- <partial src="components/navbar.html" key=value ... /> syntax
- {{ variable || default }} interpolation inside partials
"""

from __future__ import annotations

import re
from pathlib import Path

PARTIAL_RE = re.compile(r'<partial\s+src="([^"]+)"((?:\s+\w+=(?:"[^"]*"|\'[^\']*\'|\S+))*)\s*/>')
ATTR_RE = re.compile(r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))')
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*(?:\|\|\s*(.*?))?\s*\}\}")


def parse_attributes(attr_string: str) -> dict[str, str]:
    """Parse key=value attributes from a partial tag."""
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(attr_string):
        key = match.group(1)
        value = match.group(2) or match.group(3) or match.group(4) or ""
        attrs[key] = value
    return attrs


def interpolate(html: str, variables: dict[str, str]) -> str:
    """Replace {{ var || default }} expressions with values."""

    def replacer(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        if name in variables:
            return variables[name]
        if default is not None:
            return default.strip()
        return ""

    return VAR_RE.sub(replacer, html)


def render_partial(src: str, attributes: dict[str, str], base_dir: Path) -> str:
    """Load and render a partial component."""
    partial_path = base_dir / src
    if not partial_path.is_file():
        raise FileNotFoundError(f"Partial not found: {partial_path}")
    content = partial_path.read_text()
    rendered = interpolate(content, attributes)
    # Recursively resolve nested partials
    rendered = resolve_partials(rendered, base_dir)
    return rendered


def resolve_partials(html: str, base_dir: Path) -> str:
    """Find and replace all <partial .../> tags in the HTML."""

    def replacer(match: re.Match[str]) -> str:
        src = match.group(1)
        attr_string = match.group(2)
        attributes = parse_attributes(attr_string)
        return render_partial(src, attributes, base_dir)

    return PARTIAL_RE.sub(replacer, html)


def render(html: str, base_dir: Path) -> str:
    """Render an HTML template, resolving all partials."""
    return resolve_partials(html, base_dir)
