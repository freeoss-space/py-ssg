from collections.abc import Generator
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import fromstring

from jinja2 import BaseLoader, Environment

from pyssg.modules.config import SiteConfig

_jinja_env = Environment(loader=BaseLoader(), autoescape=False)


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
        result = self._render_components(result)
        return result

    def _find_components(self, html: str) -> Generator[tuple[str, int], str, None]:
        while True:
            earliest_name = ""
            earliest_pos = -1
            for name in self.component_names:
                pos = html.find(f"<{name}")
                if pos != -1 and (earliest_pos == -1 or pos < earliest_pos):
                    earliest_pos = pos
                    earliest_name = name
            if earliest_pos == -1:
                return
            updated = yield earliest_name, earliest_pos
            html = updated if updated is not None else html

    def _render_components(self, html: str) -> str:
        if not self.component_names or self.components_dir is None:
            return html
        result = html
        finder = self._find_components(result)
        found = next(finder, None)
        while found is not None:
            name, start = found
            end = result.find("/>", start) + 2
            attrs = dict(fromstring(result[start:end]).attrib)
            filepath = self.components_dir / f"{name}.html"
            with open(filepath) as f:
                component_content = f.read()
            rendered = _jinja_env.from_string(component_content).render(**attrs)
            result = result[:start] + rendered + result[end:]
            try:
                found = finder.send(result)
            except StopIteration:
                break
        return result
