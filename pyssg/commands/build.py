import hashlib
import os
import posixpath
import shutil
import time
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.build_script import BuildContext, BuildScript
from pyssg.modules.cache import BuildCache
from pyssg.modules.config import SiteConfig
from pyssg.modules.html import HtmlTemplateEngine
from pyssg.modules.markdown import (
    MarkdownCollection,
    MarkdownContent,
    MarkdownParser,
    TocGenerator,
    content_url_from_filename,
)
from pyssg.modules.rss import RssFeedGenerator
from pyssg.modules.syntax import SyntaxHighlighter


def _discover_components(components_dir: Path) -> list[str]:
    names: list[str] = []
    components_dir_str = str(components_dir)
    for dirpath, _, filenames in os.walk(components_dir):
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            name = filename.removesuffix(".html")
            dirpath_str = str(dirpath)
            if dirpath_str == components_dir_str:
                names.append(name)
            else:
                rel = dirpath_str[len(components_dir_str) :].lstrip("/\\")
                parts = [p for p in rel.replace("\\", "/").split("/") if p]
                names.append(".".join(parts + [name]))
    return names


def _is_render_only_template(filename: str) -> bool:
    return filename.endswith(".tmpl.html")


def _is_output_template(filename: str) -> bool:
    return filename.endswith(".html") and not _is_render_only_template(filename)


def _content_template_name(content: MarkdownContent) -> str | None:
    template_name = getattr(content.custom_fields, "template", None)
    if not isinstance(template_name, str) or template_name == "":
        return None
    return template_name


def _content_output_filename(content: MarkdownContent) -> str:
    return f"{content_url_from_filename(content.filename).strip('/')}/index.html"


class ProjectDirectory(StrEnum):
    CONTENT = "content"
    TEMPLATES = "templates"
    COMPONENTS = "components"
    OUTPUT = "output"
    STATIC = "static"


class StaticDirOutputMode(StrEnum):
    STATIC = "static"
    ROOT = "root"

    def destination(self, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        if self is StaticDirOutputMode.ROOT:
            return output_dir
        return output_dir / self.value

    @property
    def output_path(self) -> str:
        if self is StaticDirOutputMode.ROOT:
            return "output/"
        return f"output/{self.value}/"


def _copy_static_assets(
    static_dir: Path, output_dir: Path, output_mode: str
) -> str | None:
    if not os.path.isdir(static_dir):
        return None

    mode = StaticDirOutputMode(output_mode)
    dest = mode.destination(output_dir)
    shutil.copytree(static_dir, dest, dirs_exist_ok=os.path.exists(dest))
    return mode.output_path


def _compute_asset_version(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:12]


def _normalize_asset_lookup_path(path: str) -> str:
    normalized = posixpath.normpath(path.lstrip("/"))
    return "" if normalized == "." else normalized


@dataclass(frozen=True)
class AssetVersionManifest:
    versions: Mapping[str, str]

    def asset_url(self, path: str) -> str:
        parsed = urlsplit(path)
        if parsed.scheme != "" or parsed.netloc != "":
            return path

        lookup_path = _normalize_asset_lookup_path(parsed.path)
        if lookup_path == "":
            return path

        version = self.versions.get(lookup_path)
        if version is None:
            return path

        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        query_items.append(("v", version))
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(query_items),
                parsed.fragment,
            )
        )

    def fingerprint(self) -> str:
        return "|".join(
            f"{path}={version}" for path, version in sorted(self.versions.items())
        )


@dataclass
class BuildPaths:
    project_dir: Path
    templates_dir: Path
    components_dir: Path
    output_dir: Path


@dataclass
class RenderSummary:
    total_files: int
    built_files: int
    cached_files: int
    component_names: list[str]
    rendering_time: float


@dataclass
class TemplateRenderResult:
    built: bool
    cached: bool


type TagMap = Mapping[str, Sequence[MarkdownContent]]


class BuildCommand(BaseCommand):
    def __init__(self, *, verbose: bool = False, dry_run: bool = False) -> None:
        super().__init__(verbose=verbose, dry_run=dry_run)

    def execute(self) -> None:
        start_time = time.perf_counter()
        paths = self._build_paths()
        config = SiteConfig.load(paths.project_dir)
        cache = BuildCache(cache_dir=paths.project_dir, enabled=config.cache)
        cache.load()
        build_script = BuildScript(paths.project_dir)
        if self._dry_run:
            self._warning(
                "Dry run enabled: output files and build hooks will be skipped"
            )
        self._detail(f"Project directory: {paths.project_dir}")
        self._detail(f"Output directory: {paths.output_dir}")
        self._detail(f"Cache enabled: {config.cache}")
        context = BuildContext(
            config=config,
            cache=cache,
            project_dir=paths.project_dir,
            templates_dir=paths.templates_dir,
            components_dir=paths.components_dir,
            output_dir=paths.output_dir,
        )

        if not self._dry_run:
            build_script.before_build(context)
        highlighter = self._create_highlighter(config)
        render_markdown = highlighter.render_markdown if highlighter else None
        toc_generator = self._create_toc_generator(config)

        if not self._dry_run:
            build_script.before_markdown_parsing(context)
        collection, parsing_time = self._parse_markdown(
            paths=paths,
            config=config,
            cache=cache,
            render_markdown=render_markdown,
            toc_generator=toc_generator,
        )
        context.content = collection

        if not self._dry_run:
            build_script.before_component_parsing(context)
        render_summary = self._render_templates(
            paths=paths,
            config=config,
            cache=cache,
            collection=collection,
            highlighter=highlighter,
        )
        feed_count = self._generate_feeds(
            config=config,
            output_dir=paths.output_dir,
            collection=collection,
        )

        if not self._dry_run:
            cache.save()
            build_script.after_build(context)
        total_time = time.perf_counter() - start_time
        self._print_summary(
            render_summary=render_summary,
            feed_count=feed_count,
            parsing_time=parsing_time,
            total_time=total_time,
        )

    def _build_paths(self) -> BuildPaths:
        project_dir = Path.cwd()
        return BuildPaths(
            project_dir=project_dir,
            templates_dir=project_dir / ProjectDirectory.TEMPLATES,
            components_dir=project_dir / ProjectDirectory.COMPONENTS,
            output_dir=project_dir / ProjectDirectory.OUTPUT,
        )

    def _create_highlighter(self, config: SiteConfig) -> SyntaxHighlighter | None:
        if not config.syntax.enabled:
            return None
        return SyntaxHighlighter(
            theme_light=config.syntax.theme_light,
            theme_dark=config.syntax.theme_dark,
        )

    def _create_toc_generator(self, config: SiteConfig) -> TocGenerator | None:
        if not config.toc.enabled:
            return None
        return TocGenerator(max_depth=config.toc.max_depth)

    def _parse_markdown(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        cache: BuildCache,
        render_markdown: Callable[[str], str] | None,
        toc_generator: TocGenerator | None,
    ) -> tuple[MarkdownCollection, float]:
        self._info("Parsing markdown content")
        parsing_start = time.perf_counter()
        parser = MarkdownParser(
            content_dir=paths.project_dir / ProjectDirectory.CONTENT,
            cache=cache,
            render_markdown=render_markdown,
            toc_generator=toc_generator,
        )
        syntax_config = {
            "enabled": config.syntax.enabled,
            "theme_light": config.syntax.theme_light,
            "theme_dark": config.syntax.theme_dark,
        }
        toc_config = {
            "enabled": config.toc.enabled,
            "max_depth": config.toc.max_depth,
        }
        collection = parser.parse(
            workers=os.cpu_count() or 1,
            syntax_config=syntax_config,
            toc_config=toc_config,
        )
        return collection, time.perf_counter() - parsing_start

    def _render_templates(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        cache: BuildCache,
        collection: MarkdownCollection,
        highlighter: SyntaxHighlighter | None,
    ) -> RenderSummary:
        self._info("Rendering templates")
        rendering_start = time.perf_counter()
        component_names = _discover_components(paths.components_dir)
        asset_manifest = self._build_asset_manifest(
            paths=paths,
            config=config,
            highlighter=highlighter,
        )
        engine = HtmlTemplateEngine(
            templates_dir=paths.templates_dir,
            components_dir=paths.components_dir,
            component_names=component_names,
            config=config,
            asset_manifest=asset_manifest,
        )
        cache_seed = asset_manifest.fingerprint()
        self._detail(f"Discovered {len(component_names)} components")
        if not self._dry_run:
            os.makedirs(paths.output_dir, exist_ok=True)

        if self._dry_run:
            self._detail(
                f"Dry run: would copy template directories into {paths.output_dir}"
            )
        else:
            self._copy_template_directories(paths)
        total_files, built_files, cached_files = self._render_template_files(
            templates_dir=paths.templates_dir,
            output_dir=paths.output_dir,
            engine=engine,
            collection=collection,
            cache=cache,
            content_sort=config.content_sort,
            cache_seed=cache_seed,
        )
        (
            content_total_files,
            content_built_files,
            content_cached_files,
        ) = self._render_content_pages(
            templates_dir=paths.templates_dir,
            output_dir=paths.output_dir,
            engine=engine,
            collection=collection,
            cache=cache,
            content_sort=config.content_sort,
        )
        if self._dry_run:
            if highlighter:
                self._detail(
                    f"Dry run: would write syntax stylesheet to {paths.output_dir / 'syntax.css'}"
                )
            if os.path.isdir(paths.project_dir / config.static_dir):
                self._detail(
                    f"Dry run: would copy static assets from {paths.project_dir / config.static_dir}"
                )
        else:
            self._write_syntax_stylesheet(
                output_dir=paths.output_dir, highlighter=highlighter
            )
            self._copy_static_assets(paths=paths, config=config)

        return RenderSummary(
            total_files=total_files + content_total_files,
            built_files=built_files + content_built_files,
            cached_files=cached_files + content_cached_files,
            component_names=component_names,
            rendering_time=time.perf_counter() - rendering_start,
        )

    def _copy_template_directories(self, paths: BuildPaths) -> None:
        for entry in os.listdir(paths.templates_dir):
            entry_path = os.path.join(paths.templates_dir, entry)
            if not os.path.isdir(entry_path):
                continue
            dest = os.path.join(paths.output_dir, entry)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(
                entry_path,
                dest,
                ignore=shutil.ignore_patterns("*.html"),
            )

    def _build_asset_manifest(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        highlighter: SyntaxHighlighter | None,
    ) -> AssetVersionManifest:
        versions: dict[str, str] = {}

        for asset_path in sorted(paths.templates_dir.rglob("*")):
            if not asset_path.is_file() or asset_path.suffix == ".html":
                continue
            output_path = asset_path.relative_to(paths.templates_dir).as_posix()
            versions[output_path] = _compute_asset_version(asset_path.read_bytes())

        if highlighter:
            versions["syntax.css"] = _compute_asset_version(
                highlighter.get_stylesheet().encode("utf-8")
            )

        static_dir = paths.project_dir / config.static_dir
        if static_dir.is_dir():
            static_mode = StaticDirOutputMode(config.static_dir_output)
            for asset_path in sorted(static_dir.rglob("*")):
                if not asset_path.is_file():
                    continue
                rel_path = asset_path.relative_to(static_dir).as_posix()
                if static_mode is StaticDirOutputMode.ROOT:
                    output_path = rel_path
                else:
                    output_path = f"{static_mode.value}/{rel_path}"
                versions[output_path] = _compute_asset_version(asset_path.read_bytes())

        return AssetVersionManifest(versions=MappingProxyType(versions))

    def _iter_template_filenames(self, templates_dir: Path) -> list[str]:
        return sorted(
            str(path.relative_to(templates_dir).as_posix())
            for path in templates_dir.rglob("*.html")
            if _is_output_template(path.name)
        )

    def _render_template_files(
        self,
        templates_dir: Path,
        output_dir: Path,
        engine: HtmlTemplateEngine,
        collection: MarkdownCollection,
        cache: BuildCache,
        content_sort: str,
        cache_seed: str,
    ) -> tuple[int, int, int]:
        total_files = 0
        built_files = 0
        cached_files = 0
        sorted_content = self._sort_content(collection, content_sort)
        tag_map = self._build_tag_map(sorted_content)

        for filename in self._iter_template_filenames(templates_dir):
            total_files += 1
            result = self._render_template_file(
                filename=filename,
                templates_dir=templates_dir,
                output_dir=output_dir,
                engine=engine,
                sorted_content=sorted_content,
                tag_map=tag_map,
                cache=cache,
                cache_seed=cache_seed,
            )
            if result.cached:
                cached_files += 1
            if result.built:
                built_files += 1

        return total_files, built_files, cached_files

    def _render_content_pages(
        self,
        templates_dir: Path,
        output_dir: Path,
        engine: HtmlTemplateEngine,
        collection: MarkdownCollection,
        cache: BuildCache,
        content_sort: str,
    ) -> tuple[int, int, int]:
        total_files = 0
        built_files = 0
        cached_files = 0
        sorted_content = self._sort_content(collection, content_sort)
        tag_map = self._build_tag_map(sorted_content)
        self._warn_for_non_render_only_content_templates(sorted_content)

        for post in sorted_content:
            template_name = _content_template_name(post)
            if template_name is None:
                continue

            total_files += 1
            result = self._render_content_page(
                template_name=template_name,
                output_filename=_content_output_filename(post),
                templates_dir=templates_dir,
                output_dir=output_dir,
                engine=engine,
                sorted_content=sorted_content,
                tag_map=tag_map,
                post=post,
                cache=cache,
            )
            if result.cached:
                cached_files += 1
            if result.built:
                built_files += 1

        return total_files, built_files, cached_files

    def _warn_for_non_render_only_content_templates(
        self, sorted_content: list[MarkdownContent]
    ) -> None:
        warned_templates: set[str] = set()
        for post in sorted_content:
            template_name = _content_template_name(post)
            if template_name is None:
                continue
            if _is_render_only_template(template_name):
                continue
            if template_name in warned_templates:
                continue
            warned_templates.add(template_name)
            self._warning(
                f"Content template {template_name} is not render-only and will "
                "also be rendered as a standalone page. Rename it to "
                f"{template_name.removesuffix('.html')}.tmpl.html if it should "
                "only be used through frontmatter."
            )

    def _render_content_page(
        self,
        template_name: str,
        output_filename: str,
        templates_dir: Path,
        output_dir: Path,
        engine: HtmlTemplateEngine,
        sorted_content: list[MarkdownContent],
        tag_map: TagMap,
        post: MarkdownContent,
        cache: BuildCache,
    ) -> TemplateRenderResult:
        del cache
        filepath = os.path.join(templates_dir, template_name)
        with open(filepath) as f:
            template = f.read()

        rendered = engine.render(
            template,
            context={
                "content": tuple(sorted_content),
                "tags": tag_map,
                "post": post,
            },
        )
        if self._dry_run:
            self._detail(f"Dry run: would render {output_filename}")
            return TemplateRenderResult(built=True, cached=False)
        output_path = os.path.join(output_dir, output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(rendered)

        return TemplateRenderResult(built=True, cached=False)

    def _render_template_file(
        self,
        filename: str,
        templates_dir: Path,
        output_dir: Path,
        engine: HtmlTemplateEngine,
        sorted_content: list[MarkdownContent],
        tag_map: TagMap,
        cache: BuildCache,
        cache_seed: str,
    ) -> TemplateRenderResult:
        filepath = os.path.join(templates_dir, filename)
        with open(filepath) as f:
            template = f.read()

        cache_content = self._template_cache_content(template, cache_seed)
        is_dynamic = cache.has_dynamic_constructs(template)
        if not is_dynamic and not cache.needs_rebuild(filename, cache_content):
            return TemplateRenderResult(built=False, cached=True)

        rendered = engine.render(
            template,
            context={"content": tuple(sorted_content), "tags": tag_map},
        )
        if self._dry_run:
            self._detail(f"Dry run: would render {filename}")
            return TemplateRenderResult(built=True, cached=False)
        output_path = os.path.join(output_dir, filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(rendered)

        if not is_dynamic:
            cache.update(filename, cache_content)
        return TemplateRenderResult(built=True, cached=False)

    def _template_cache_content(self, template: str, cache_seed: str) -> str:
        if cache_seed == "":
            return template
        return f"{template}\0{cache_seed}"

    def _sort_content(
        self, collection: MarkdownCollection, content_sort: str
    ) -> list[MarkdownContent]:
        items = list(collection)
        if content_sort == "none":
            return items
        if content_sort == "filename":
            return sorted(items, key=lambda post: post.filename)

        dated = [post for post in items if post.timestamp]
        undated = [post for post in items if not post.timestamp]
        reverse = content_sort == "date_desc"
        sorted_dated = sorted(dated, key=lambda post: post.timestamp, reverse=reverse)
        return sorted_dated + undated

    def _build_tag_map(self, sorted_content: list[MarkdownContent]) -> TagMap:
        tag_map: defaultdict[str, list[MarkdownContent]] = defaultdict(list)
        for post in sorted_content:
            for tag in post.tags:
                tag_map[tag].append(post)
        frozen_tag_map = {tag: tuple(posts) for tag, posts in tag_map.items()}
        return MappingProxyType(frozen_tag_map)

    def _write_syntax_stylesheet(
        self,
        output_dir: Path,
        highlighter: SyntaxHighlighter | None,
    ) -> None:
        if not highlighter:
            return
        css_path = os.path.join(output_dir, "syntax.css")
        with open(css_path, "w") as f:
            f.write(highlighter.get_stylesheet())

    def _copy_static_assets(self, paths: BuildPaths, config: SiteConfig) -> None:
        static_output = _copy_static_assets(
            static_dir=paths.project_dir / config.static_dir,
            output_dir=paths.output_dir,
            output_mode=config.static_dir_output,
        )
        if static_output:
            self._info(f"Copied static assets to {static_output}")

    def _generate_feeds(
        self,
        config: SiteConfig,
        output_dir: Path,
        collection: MarkdownCollection,
    ) -> int:
        if not config.feeds:
            return 0

        self._info("Generating RSS feeds")
        generator = RssFeedGenerator(config=config)
        feed_count = 0
        for output_name, xml in generator.generate(collection):
            if self._dry_run:
                self._detail(f"Dry run: would write feed {output_name}")
                feed_count += 1
                continue
            output_path = os.path.join(output_dir, output_name)
            with open(output_path, "w") as f:
                f.write(xml)
            feed_count += 1
        return feed_count

    def _print_summary(
        self,
        render_summary: RenderSummary,
        feed_count: int,
        parsing_time: float,
        total_time: float,
    ) -> None:
        summary_label = "Dry run complete" if self._dry_run else "Build complete"
        self._success(
            f"{summary_label}: "
            f"{render_summary.total_files} templates, "
            f"{render_summary.built_files} built, "
            f"{render_summary.cached_files} cached, "
            f"{len(render_summary.component_names)} components, "
            f"{feed_count} RSS feeds"
        )
        self._info(
            "Timings: "
            f"parse {parsing_time:.3f}s, "
            f"render {render_summary.rendering_time:.3f}s, "
            f"total {total_time:.3f}s"
        )
