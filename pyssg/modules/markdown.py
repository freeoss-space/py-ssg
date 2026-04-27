import json
import re
from collections.abc import Callable, Iterator
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Any, TypedDict, cast
from xml.etree.ElementTree import Element, SubElement, tostring

import frontmatter
import mistune
from mistune.toc import add_toc_hook

from pyssg.modules.cache import BuildCache

_AUTHOR_KEYS = frozenset({"author", "author_email", "author_avatar", "author_url"})


def _slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug).strip("-")
    return slug


def content_url_from_filename(filename: str) -> str:
    route = filename.removesuffix(".md").strip("/")
    return f"/{route}/"


def _read_timestamp(post: Any) -> str:
    timestamp = post.get("timestamp", "")
    if timestamp != "":
        return str(timestamp)
    return str(post.get("date", ""))


def _to_json_safe_value(value: object) -> object:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list | tuple):
        return [_to_json_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _to_json_safe_value(item_value)
            for key, item_value in value.items()
        }
    return str(value)


class TocGenerator:
    def __init__(self, max_depth: int = 3) -> None:
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

    def to_dict(self) -> "ContentAuthorData":
        return {
            "name": self.name,
            "email": self.email,
            "avatar": self.avatar,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: "ContentAuthorData") -> "ContentAuthor":
        return cls(
            name=str(data.get("name", "")),
            email=str(data.get("email", "")),
            avatar=str(data.get("avatar", "")),
            url=str(data.get("url", "")),
        )


class ContentAuthorData(TypedDict):
    name: str
    email: str
    avatar: str
    url: str


class MarkdownContentData(TypedDict):
    filename: str
    html: str
    title: str
    timestamp: str
    slug: str
    summary: str
    subtitle: str
    draft: bool
    tags: list[str]
    author: ContentAuthorData
    custom_fields: dict[str, object]
    toc: str


@dataclass(frozen=True)
class ParallelParseConfig:
    syntax_enabled: bool
    theme_light: str
    theme_dark: str
    toc_enabled: bool
    toc_max_depth: int


@dataclass(frozen=True)
class PendingParseItem:
    index: int
    filename: str
    raw: str


@dataclass
class MarkdownContent:
    filename: str
    html: str
    title: str = ""
    timestamp: str = ""
    slug: str = ""
    summary: str = ""
    subtitle: str = ""
    draft: bool = False
    tags: list[str] = field(default_factory=list)
    author: ContentAuthor = field(default_factory=ContentAuthor)
    custom_fields: SimpleNamespace = field(default_factory=SimpleNamespace)
    toc: str = ""

    @property
    def url(self) -> str:
        return content_url_from_filename(self.filename)

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
            timestamp=_read_timestamp(post),
            slug=str(post.get("slug", "")),
            summary=str(post.get("summary", "")),
            subtitle=str(post.get("subtitle", "")),
            draft=bool(post.get("draft", False)),
            tags=tags,
            author=ContentAuthor.from_post(post),
            custom_fields=custom,
            toc=toc,
        )

    def to_dict(self) -> MarkdownContentData:
        return {
            "filename": self.filename,
            "html": self.html,
            "title": self.title,
            "timestamp": self.timestamp,
            "slug": self.slug,
            "summary": self.summary,
            "subtitle": self.subtitle,
            "draft": self.draft,
            "tags": list(self.tags),
            "author": self.author.to_dict(),
            "custom_fields": cast(
                dict[str, object],
                _to_json_safe_value(dict(vars(self.custom_fields))),
            ),
            "toc": self.toc,
        }

    @classmethod
    def from_dict(cls, data: MarkdownContentData) -> "MarkdownContent":
        raw_tags = data.get("tags", [])
        tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else []
        custom_fields_data = data.get("custom_fields", {})
        if not isinstance(custom_fields_data, dict):
            custom_fields_data = {}
        author_data = data.get("author", ContentAuthor().to_dict())
        if not isinstance(author_data, dict):
            author_data = ContentAuthor().to_dict()
        return cls(
            filename=str(data.get("filename", "")),
            html=str(data.get("html", "")),
            title=str(data.get("title", "")),
            timestamp=str(data.get("timestamp", "")),
            slug=str(data.get("slug", "")),
            summary=str(data.get("summary", "")),
            subtitle=str(data.get("subtitle", "")),
            draft=bool(data.get("draft", False)),
            tags=tags,
            author=ContentAuthor.from_dict(author_data),
            custom_fields=SimpleNamespace(**cast(dict[str, Any], custom_fields_data)),
            toc=str(data.get("toc", "")),
        )


@dataclass
class MarkdownCollection:
    _items: list[MarkdownContent] = field(default_factory=list)

    def add(self, content: MarkdownContent) -> None:
        self._items.append(content)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[MarkdownContent]:
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
        cache: BuildCache | None = None,
        render_markdown: Callable[[str], str] | None = None,
        toc_generator: TocGenerator | None = None,
    ) -> None:
        self.content_dir = content_dir
        self.cache = cache
        self.render_markdown = render_markdown
        self.toc_generator = toc_generator

    def _read_files(self) -> list[tuple[str, str]]:
        items = []
        for filepath in sorted(self.content_dir.rglob("*.md")):
            relpath = filepath.relative_to(self.content_dir)
            with filepath.open() as f:
                raw = f.read()
            items.append((relpath.as_posix(), raw))
        return items

    def parse(
        self,
        workers: int = 1,
        syntax_config: dict[str, Any] | None = None,
        toc_config: dict[str, Any] | None = None,
    ) -> MarkdownCollection:
        config_key = self._build_config_key(syntax_config, toc_config)
        if workers > 1 and (syntax_config is not None or toc_config is not None):
            return self._parse_parallel(workers, config_key, syntax_config, toc_config)
        return self._parse_sequential(config_key)

    def _build_config_key(
        self,
        syntax_config: dict[str, Any] | None,
        toc_config: dict[str, Any] | None,
    ) -> str:
        return json.dumps(
            {"syntax": syntax_config or {}, "toc": toc_config or {}},
            sort_keys=True,
            separators=(",", ":"),
        )

    def _get_cached_content(
        self, filename: str, raw: str, config_key: str
    ) -> MarkdownContent | None:
        if self.cache is None:
            return None
        cached = self.cache.get_content(filename, raw, config_key)
        if cached is None:
            return None
        return MarkdownContent.from_dict(cast(MarkdownContentData, cached))

    def _cache_content(
        self, filename: str, raw: str, config_key: str, content: MarkdownContent
    ) -> None:
        if self.cache is None:
            return
        self.cache.set_content(filename, raw, config_key, content.to_dict())

    def _build_parallel_config(
        self,
        syntax_config: dict[str, Any] | None,
        toc_config: dict[str, Any] | None,
    ) -> ParallelParseConfig:
        return ParallelParseConfig(
            syntax_enabled=bool(syntax_config and syntax_config.get("enabled")),
            theme_light=(
                syntax_config.get("theme_light", "friendly")
                if syntax_config
                else "friendly"
            ),
            theme_dark=(
                syntax_config.get("theme_dark", "monokai")
                if syntax_config
                else "monokai"
            ),
            toc_enabled=bool(toc_config and toc_config.get("enabled")),
            toc_max_depth=toc_config.get("max_depth", 3) if toc_config else 3,
        )

    def _partition_cached_items(
        self, items: list[tuple[str, str]], config_key: str
    ) -> tuple[dict[int, MarkdownContent], list[PendingParseItem]]:
        results: dict[int, MarkdownContent] = {}
        pending_items: list[PendingParseItem] = []
        for index, (filename, raw) in enumerate(items):
            cached_content = self._get_cached_content(filename, raw, config_key)
            if cached_content is not None:
                results[index] = cached_content
                continue
            pending_items.append(
                PendingParseItem(index=index, filename=filename, raw=raw)
            )
        return results, pending_items

    def _worker_items(
        self, pending_items: list[PendingParseItem]
    ) -> list[tuple[str, str]]:
        return [(item.filename, item.raw) for item in pending_items]

    def _parse_pending_items(
        self,
        workers: int,
        parallel_config: ParallelParseConfig,
        pending_items: list[PendingParseItem],
    ) -> Iterator[MarkdownContent]:
        with ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(
                parallel_config.syntax_enabled,
                parallel_config.theme_light,
                parallel_config.theme_dark,
                parallel_config.toc_enabled,
                parallel_config.toc_max_depth,
            ),
        ) as executor:
            yield from executor.map(
                _parse_file_worker,
                self._worker_items(pending_items),
                chunksize=64,
            )

    def _store_parsed_results(
        self,
        results: dict[int, MarkdownContent],
        pending_items: list[PendingParseItem],
        parsed_contents: Iterator[MarkdownContent],
        config_key: str,
    ) -> None:
        for pending_item, content in zip(pending_items, parsed_contents):
            results[pending_item.index] = content
            self._cache_content(content.filename, pending_item.raw, config_key, content)

    def _build_collection_from_results(
        self, item_count: int, results: dict[int, MarkdownContent]
    ) -> MarkdownCollection:
        collection = MarkdownCollection()
        for index in range(item_count):
            collection.add(results[index])
        return collection

    def _parse_sequential(self, config_key: str) -> MarkdownCollection:
        collection = MarkdownCollection()
        for filename, raw in self._read_files():
            cached_content = self._get_cached_content(filename, raw, config_key)
            if cached_content is not None:
                collection.add(cached_content)
                continue
            content = MarkdownContent.from_raw(
                filename,
                raw,
                render_markdown=self.render_markdown,
                toc_generator=self.toc_generator,
            )
            self._cache_content(filename, raw, config_key, content)
            collection.add(content)
        return collection

    def _parse_parallel(
        self,
        workers: int,
        config_key: str,
        syntax_config: dict[str, Any] | None,
        toc_config: dict[str, Any] | None,
    ) -> MarkdownCollection:
        items = self._read_files()
        parallel_config = self._build_parallel_config(syntax_config, toc_config)
        results, pending_items = self._partition_cached_items(items, config_key)
        if pending_items:
            parsed_contents = self._parse_pending_items(
                workers,
                parallel_config,
                pending_items,
            )
            self._store_parsed_results(
                results,
                pending_items,
                parsed_contents,
                config_key,
            )
        return self._build_collection_from_results(len(items), results)
