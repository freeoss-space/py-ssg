import os
import re
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

import frontmatter
import mistune
from mistune.toc import add_toc_hook

_AUTHOR_KEYS = frozenset({"author", "author_email", "author_avatar", "author_url"})


def _slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug).strip("-")
    return slug


class TocGenerator:
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self._md = mistune.create_markdown()
        add_toc_hook(
            self._md,
            max_level=self.max_depth,
            heading_id=lambda token, index: _slugify(token["text"]),
        )

    def generate(self, markdown_text: str) -> str:
        _, state = self._md.parse(markdown_text)
        toc_items: list[tuple[int, str, str]] = state.env.get("toc_items", [])

        if not toc_items:
            return ""

        nav = Element("nav")
        nav.set("class", "toc")
        root_ul = SubElement(nav, "ul")

        stack: list[tuple[Element, int]] = [(root_ul, toc_items[0][0])]

        for level, heading_id, text in toc_items:
            while level < stack[-1][1] and len(stack) > 1:
                stack.pop()

            if level > stack[-1][1]:
                parent_ul = stack[-1][0]
                last_li = list(parent_ul)[-1]
                new_ul = SubElement(last_li, "ul")
                stack.append((new_ul, level))

            current_ul = stack[-1][0]
            li = SubElement(current_ul, "li")
            a = SubElement(li, "a")
            a.set("href", f"#{heading_id}")
            a.text = text

        return tostring(nav, encoding="unicode", method="html")


@dataclass
class ContentAuthor:
    name: str = ""
    email: str = ""
    avatar: str = ""
    url: str = ""

    @classmethod
    def from_post(cls, post: Any) -> ContentAuthor:
        return cls(
            name=str(post.get("author", "")),
            email=str(post.get("author_email", "")),
            avatar=str(post.get("author_avatar", "")),
            url=str(post.get("author_url", "")),
        )


@dataclass
class MarkdownContent:
    filename: str
    html: str
    title: str = ""
    timestamp: str = ""
    tags: list[str] = field(default_factory=list)
    author: ContentAuthor = field(default_factory=ContentAuthor)
    custom_fields: SimpleNamespace = field(default_factory=SimpleNamespace)
    toc: str = ""

    @classmethod
    def from_raw(
        cls,
        filename: str,
        raw: str,
        render_markdown: Callable[[str], str] | None = None,
        toc_generator: TocGenerator | None = None,
    ) -> MarkdownContent:
        post = frontmatter.loads(raw)
        known_fields = {f.name for f in fields(cls)} - {
            "filename",
            "html",
            "author",
            "custom_fields",
        }
        custom = SimpleNamespace()
        for key in post.metadata:
            if key not in known_fields and key not in _AUTHOR_KEYS:
                setattr(custom, key, post.metadata[key])
        raw_tags = post.get("tags")
        tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
        render = render_markdown or mistune.html
        toc = toc_generator.generate(post.content) if toc_generator else ""
        return cls(
            filename=filename,
            html=str(render(post.content)),
            title=str(post.get("title", "")),
            timestamp=str(post.get("timestamp", "")),
            tags=tags,
            author=ContentAuthor.from_post(post),
            custom_fields=custom,
            toc=toc,
        )


@dataclass
class MarkdownCollection:
    _items: list[MarkdownContent] = field(default_factory=list)

    def add(self, content: MarkdownContent) -> None:
        self._items.append(content)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key: str) -> MarkdownContent:
        return next(item for item in self._items if item.filename == key)

    def __contains__(self, key: object) -> bool:
        return any(item.filename == key for item in self._items)


_worker_render_markdown: Callable[[str], str] | None = None
_worker_toc_generator: TocGenerator | None = None


def _init_worker(
    syntax_enabled: bool,
    theme_light: str,
    theme_dark: str,
    toc_enabled: bool,
    toc_max_depth: int,
) -> None:
    global _worker_render_markdown, _worker_toc_generator
    _worker_render_markdown = None
    _worker_toc_generator = None
    if syntax_enabled:
        from pyssg.modules.syntax import SyntaxHighlighter

        hightlighter = SyntaxHighlighter(theme_light=theme_light, theme_dark=theme_dark)
        _worker_render_markdown = hightlighter.render_markdown
    if toc_enabled:
        _worker_toc_generator = TocGenerator(max_depth=toc_max_depth)


def _parse_file_worker(item: tuple[str, str]) -> MarkdownContent:
    return MarkdownContent.from_raw(
        item[0],
        item[1],
        render_markdown=_worker_render_markdown,
        toc_generator=_worker_toc_generator,
    )


class MarkdownParser:
    def __init__(
        self,
        content_dir: Path,
        render_markdown: Callable[[str], str] | None = None,
        toc_generator: TocGenerator | None = None,
    ):
        self.content_dir = content_dir
        self.render_markdown = render_markdown
        self.toc_generator = toc_generator

    def _read_files(self) -> list[tuple[str, str]]:
        items = []
        for filename in os.listdir(self.content_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(self.content_dir, filename)
            with open(filepath) as f:
                raw = f.read()
            items.append((filename, raw))
        return items

    def parse(
        self,
        workers: int = 1,
        syntax_config: dict[str, Any] | None = None,
        toc_config: dict[str, Any] | None = None,
    ) -> MarkdownCollection:
        if workers > 1 and (syntax_config is not None or toc_config is not None):
            return self._parse_parallel(workers, syntax_config, toc_config)
        return self._parse_sequential()

    def _parse_sequential(self) -> MarkdownCollection:
        collection = MarkdownCollection()
        for filename, raw in self._read_files():
            collection.add(
                MarkdownContent.from_raw(
                    filename,
                    raw,
                    render_markdown=self.render_markdown,
                    toc_generator=self.toc_generator,
                )
            )
        return collection

    def _parse_parallel(
        self,
        workers: int,
        syntax_config: dict[str, Any] | None,
        toc_config: dict[str, Any] | None,
    ) -> MarkdownCollection:
        items = self._read_files()

        syntax_enabled = bool(syntax_config and syntax_config.get("enabled"))
        theme_light = (
            syntax_config.get("theme_light", "friendly")
            if syntax_config
            else "friendly"
        )
        theme_dark = (
            syntax_config.get("theme_dark", "monokai") if syntax_config else "monokai"
        )
        toc_enabled = bool(toc_config and toc_config.get("enabled"))
        toc_max_depth = toc_config.get("max_depth", 3) if toc_config else 3

        collection = MarkdownCollection()
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(
                syntax_enabled,
                theme_light,
                theme_dark,
                toc_enabled,
                toc_max_depth,
            ),
        ) as executor:
            for content in executor.map(_parse_file_worker, items, chunksize=64):
                collection.add(content)
        return collection
