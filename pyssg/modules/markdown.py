import os
import re
from collections.abc import Callable
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

    def parse(self) -> MarkdownCollection:
        collection = MarkdownCollection()
        for filename in os.listdir(self.content_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(self.content_dir, filename)
            with open(filepath) as f:
                raw = f.read()
            collection.add(
                MarkdownContent.from_raw(
                    filename,
                    raw,
                    render_markdown=self.render_markdown,
                    toc_generator=self.toc_generator,
                )
            )
        return collection
