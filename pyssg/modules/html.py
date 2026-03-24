from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import fromstring

from jinja2 import BaseLoader, Environment, Template

from pyssg.modules.config import SiteConfig

_jinja_env = Environment(loader=BaseLoader(), autoescape=False)

_TAG_TERMINATORS = frozenset(" />\n\t\r")


@dataclass
class ComponentMatch:
    name: str
    start: int
    end: int
    attrs: dict[str, str]


def find_component_tags(html: str, known_names: set[str]) -> list[ComponentMatch]:
    if not known_names:
        return []

    matches: list[ComponentMatch] = []
    search_from = 0

    while search_from < len(html):
        open_bracket = html.find("<", search_from)
        if open_bracket == -1:
            break

        tag_name_start = open_bracket + 1
        tag_name_end = tag_name_start
        while tag_name_end < len(html) and html[tag_name_end] not in _TAG_TERMINATORS:
            tag_name_end += 1

        tag_name = html[tag_name_start:tag_name_end]

        if tag_name not in known_names:
            search_from = open_bracket + 1
            continue

        close_marker = html.find("/>", tag_name_end)
        if close_marker == -1:
            search_from = open_bracket + 1
            continue

        tag_end = close_marker + 2
        tag_text = html[open_bracket:tag_end]
        attrs = dict(fromstring(tag_text).attrib)
        matches.append(
            ComponentMatch(name=tag_name, start=open_bracket, end=tag_end, attrs=attrs)
        )
        search_from = tag_end

    return matches


def replace_component_tags(
    html: str,
    matches: list[ComponentMatch],
    replacements: dict[str, str],
) -> str:
    if not matches:
        return html

    parts: list[str] = []
    last_end = 0

    for match in matches:
        parts.append(html[last_end : match.start])
        parts.append(replacements[match.name])
        last_end = match.end

    parts.append(html[last_end:])
    return "".join(parts)


class HtmlTemplateEngine:
    def __init__(
        self,
        templates_dir: Path,
        components_dir: Path | None = None,
        component_names: list[str] | None = None,
        config: SiteConfig | None = None,
    ):
        self.templates_dir = templates_dir
        self.components_dir = components_dir
        self.component_names = component_names or []
        self.config = config
        self._component_set: set[str] = set(self.component_names)
        self._component_cache: dict[str, Template] = {}

    def _get_component(self, name: str) -> Template:
        cached = self._component_cache.get(name)
        if cached is not None:
            return cached
        assert self.components_dir is not None
        filepath = self.components_dir / f"{name}.html"
        with open(filepath) as f:
            content = f.read()
        template = _jinja_env.from_string(content)
        self._component_cache[name] = template
        return template

    def render(
        self,
        template: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        render_context: dict[str, Any] = {}
        if self.config:
            render_context["site"] = self.config
        if context:
            render_context.update(context)
        if render_context:
            jinja_template = _jinja_env.from_string(template)
            result = jinja_template.render(**render_context)
        else:
            result = template
        return self._render_components(result)

    def _render_components(self, html: str) -> str:
        if not self.component_names or self.components_dir is None:
            return html

        result = html
        for _ in range(10):
            matches = find_component_tags(result, self._component_set)
            if not matches:
                break
            replacements = {
                match.name: self._get_component(match.name).render(**match.attrs)
                for match in matches
            }
            result = replace_component_tags(result, matches, replacements)

        return result
