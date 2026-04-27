from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Protocol

from jinja2 import BaseLoader, Environment, Template

from pyssg.modules.config import SiteConfig
from pyssg.modules.template_helpers import (
    date_format,
    excerpt,
    is_blog_post,
    post_url,
    slug,
)

_jinja_env = Environment(loader=BaseLoader(), autoescape=False)


def _register_template_helpers() -> None:
    _jinja_env.filters["date_format"] = date_format
    _jinja_env.filters["excerpt"] = excerpt
    _jinja_env.filters["slug"] = slug
    setattr(
        _jinja_env,
        "globals",
        {
            **_jinja_env.globals,
            "is_blog_post": is_blog_post,
            "post_url": post_url,
        },
    )


_register_template_helpers()

_TAG_TERMINATORS = frozenset(" />\n\t\r")
_ATTR_NAME_TERMINATORS = frozenset("=>/ \n\t\r")
_WHITESPACE = frozenset(" \n\t\r")


@dataclass
class ComponentMatch:
    name: str
    start: int
    end: int
    attrs: dict[str, str]
    children: str = field(default="")


class AssetManifest(Protocol):
    def asset_url(self, path: str) -> str:
        pass


def _build_line_offsets(html: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(html):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _skip_chars(raw: str, index: int, chars: frozenset[str]) -> int:
    while index < len(raw) and raw[index] in chars:
        index += 1
    return index


def _read_until_chars(
    raw: str, index: int, stop_chars: frozenset[str]
) -> tuple[str, int]:
    start = index
    while index < len(raw) and raw[index] not in stop_chars:
        index += 1
    return raw[start:index], index


def _read_tag_name(raw: str) -> tuple[str, int]:
    return _read_until_chars(raw, 1, _TAG_TERMINATORS)


def _read_attr_name(raw: str, index: int) -> tuple[str, int]:
    return _read_until_chars(raw, index, _ATTR_NAME_TERMINATORS)


def _read_quoted_attr_value(raw: str, index: int, quote: str) -> tuple[str, int]:
    value, index = _read_until_chars(raw, index + 1, frozenset(quote))
    if index < len(raw):
        index += 1
    return value, index


def _read_unquoted_attr_value(raw: str, index: int) -> tuple[str, int]:
    return _read_until_chars(raw, index, _TAG_TERMINATORS)


def _read_attr_value(raw: str, index: int) -> tuple[str, int]:
    if index >= len(raw) or raw[index] != "=":
        return "", index

    value_index = _skip_chars(raw, index + 1, _WHITESPACE)
    if value_index >= len(raw):
        return "", value_index
    if raw[value_index] in "\"'":
        return _read_quoted_attr_value(raw, value_index, raw[value_index])
    return _read_unquoted_attr_value(raw, value_index)


def _parse_raw_tag(raw: str) -> tuple[str, dict[str, str]]:
    """Return (tag_name, attrs) from a raw opening-tag string, preserving case."""
    name, index = _read_tag_name(raw)

    attrs: dict[str, str] = {}
    while index < len(raw):
        index = _skip_chars(raw, index, _WHITESPACE)
        if index >= len(raw) or raw[index] in "/>":
            break

        attr_name, index = _read_attr_name(raw, index)
        if attr_name == "":
            break

        index = _skip_chars(raw, index, _WHITESPACE)
        attr_value, index = _read_attr_value(raw, index)
        attrs[attr_name] = attr_value

    return name, attrs


class _ComponentParser(HTMLParser):
    """HTMLParser subclass that locates component tags while preserving case.

    HTMLParser lowercases all tag/attr names, so we use getpos() to locate each
    tag in the original HTML and re-parse it with fromstring() for case-correct
    names and attributes.
    """

    def __init__(self, html: str, known_names: set[str]) -> None:
        super().__init__(convert_charrefs=False)
        self._known_names = known_names
        self._html = html
        self._line_offsets = _build_line_offsets(html)
        self._matches: list[ComponentMatch] = []
        # (name, tag_start, open_tag_end, attrs) — one entry per open component tag
        self._stack: list[tuple[str, int, int, dict[str, str]]] = []

    def _to_offset(self, line: int, col: int) -> int:
        return self._line_offsets[line - 1] + col

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        raw = self.get_starttag_text()
        if not raw:
            return
        real_name, real_attrs = _parse_raw_tag(raw)
        if real_name not in self._known_names:
            return
        line, col = self.getpos()
        start = self._to_offset(line, col)
        open_end = start + len(raw)
        self._stack.append((real_name, start, open_end, real_attrs))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        raw = self.get_starttag_text()
        if not raw:
            return
        real_name, real_attrs = _parse_raw_tag(raw)
        if real_name not in self._known_names:
            return
        line, col = self.getpos()
        start = self._to_offset(line, col)
        end = start + len(raw)
        self._matches.append(
            ComponentMatch(
                name=real_name, start=start, end=end, attrs=real_attrs, children=""
            )
        )

    def handle_endtag(self, tag: str) -> None:
        line, col = self.getpos()
        start = self._to_offset(line, col)
        # HTMLParser lowercases 'tag', so read the real name from the raw HTML.
        name_start = start + 2  # skip '</'
        name_end = name_start
        while (
            name_end < len(self._html) and self._html[name_end] not in _TAG_TERMINATORS
        ):
            name_end += 1
        real_name = self._html[name_start:name_end]
        if real_name not in self._known_names:
            return
        close_end = self._html.find(">", start) + 1
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == real_name:
                open_name, open_start, open_end, open_attrs = self._stack.pop(i)
                self._matches.append(
                    ComponentMatch(
                        name=open_name,
                        start=open_start,
                        end=close_end,
                        attrs=open_attrs,
                        children=self._html[open_end:start],
                    )
                )
                break

    def get_matches(self) -> list[ComponentMatch]:
        # Sort by start position, then drop nested matches so callers receive
        # only the outermost components; inner ones are processed in later passes.
        sorted_matches = sorted(self._matches, key=lambda m: m.start)
        result: list[ComponentMatch] = []
        last_end = 0
        for match in sorted_matches:
            if match.start >= last_end:
                result.append(match)
                last_end = match.end
        return result


def find_component_tags(html: str, known_names: set[str]) -> list[ComponentMatch]:
    if not known_names:
        return []
    parser = _ComponentParser(html, known_names)
    parser.feed(html)
    return parser.get_matches()


def replace_component_tags(
    html: str,
    matches: list[ComponentMatch],
    replacements: list[str],
) -> str:
    if not matches:
        return html

    parts: list[str] = []
    last_end = 0

    for match, replacement in zip(matches, replacements):
        parts.append(html[last_end : match.start])
        parts.append(replacement)
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
        asset_manifest: AssetManifest | None = None,
    ) -> None:
        self.templates_dir = templates_dir
        self.components_dir = components_dir
        self.component_names = component_names or []
        self.config = config
        self.asset_manifest = asset_manifest
        self._component_set: set[str] = set(self.component_names)
        self._component_cache: dict[str, Template] = {}

    def _get_component(self, name: str) -> Template:
        cached = self._component_cache.get(name)
        if cached is not None:
            return cached
        assert self.components_dir is not None
        parts = name.split(".")
        filepath = (self.components_dir / Path(*parts)).with_suffix(".html")
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
        if self.asset_manifest is not None:
            render_context["asset_url"] = self.asset_manifest.asset_url
        if context:
            render_context.update(context)
        jinja_template = _jinja_env.from_string(template)
        result = jinja_template.render(**render_context)
        return self._render_components(result, render_context)

    def _render_components(self, html: str, context: dict[str, Any]) -> str:
        if not self.component_names or self.components_dir is None:
            return html

        result = html
        for _ in range(10):
            matches = find_component_tags(result, self._component_set)
            if not matches:
                break
            replacements = [
                self._get_component(match.name).render(
                    **context, **match.attrs, children=match.children
                )
                for match in matches
            ]
            result = replace_component_tags(result, matches, replacements)

        return result
