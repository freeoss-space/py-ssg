import os
import shutil
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.build_script import BuildContext, BuildScript
from pyssg.modules.cache import BuildCache
from pyssg.modules.config import SiteConfig
from pyssg.modules.html import HtmlTemplateEngine
from pyssg.modules.markdown import MarkdownParser, TocGenerator
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


class BuildCommand(BaseCommand):
    def execute(self) -> None:
        start_time = time.perf_counter()
        paths = self._build_paths()
        config = SiteConfig.load(paths.project_dir)
        cache = BuildCache(cache_dir=paths.project_dir, enabled=config.cache)
        cache.load()
        build_script = BuildScript(paths.project_dir)
        context = BuildContext(
            config=config,
            cache=cache,
            project_dir=paths.project_dir,
            templates_dir=paths.templates_dir,
            components_dir=paths.components_dir,
            output_dir=paths.output_dir,
        )

        build_script.before_build(context)
        highlighter = self._create_highlighter(config)
        render_markdown = highlighter.render_markdown if highlighter else None
        toc_generator = self._create_toc_generator(config)

        build_script.before_markdown_parsing(context)
        collection, parsing_time = self._parse_markdown(
            paths=paths,
            config=config,
            render_markdown=render_markdown,
            toc_generator=toc_generator,
        )
        context.content = collection

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
        render_markdown,
        toc_generator: TocGenerator | None,
    ):
        self._info("Parsing markdown files...")
        parsing_start = time.perf_counter()
        parser = MarkdownParser(
            content_dir=paths.project_dir / ProjectDirectory.CONTENT,
            render_markdown=render_markdown,
            toc_generator=toc_generator,
        )
        collection = parser.parse(
            workers=os.cpu_count() or 1,
            syntax_config={
                "enabled": config.syntax.enabled,
                "theme_light": config.syntax.theme_light,
                "theme_dark": config.syntax.theme_dark,
            },
            toc_config={
                "enabled": config.toc.enabled,
                "max_depth": config.toc.max_depth,
            },
        )
        return collection, time.perf_counter() - parsing_start

    def _render_templates(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        cache: BuildCache,
        collection,
        highlighter: SyntaxHighlighter | None,
    ) -> RenderSummary:
        self._info("Rendering templates...")
        rendering_start = time.perf_counter()
        component_names = _discover_components(paths.components_dir)
        engine = HtmlTemplateEngine(
            templates_dir=paths.templates_dir,
            components_dir=paths.components_dir,
            component_names=component_names,
            config=config,
        )
        os.makedirs(paths.output_dir, exist_ok=True)

        self._copy_template_directories(paths)
        total_files, built_files, cached_files = self._render_template_files(
            templates_dir=paths.templates_dir,
            output_dir=paths.output_dir,
            engine=engine,
            collection=collection,
            cache=cache,
        )
        self._write_syntax_stylesheet(
            output_dir=paths.output_dir, highlighter=highlighter
        )
        self._copy_static_assets(paths=paths, config=config)

        return RenderSummary(
            total_files=total_files,
            built_files=built_files,
            cached_files=cached_files,
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
            shutil.copytree(entry_path, dest)

    def _render_template_files(
        self,
        templates_dir: Path,
        output_dir: Path,
        engine: HtmlTemplateEngine,
        collection,
        cache: BuildCache,
    ) -> tuple[int, int, int]:
        total_files = 0
        built_files = 0
        cached_files = 0

        for filename in os.listdir(templates_dir):
            if not filename.endswith(".html"):
                continue

            total_files += 1
            filepath = os.path.join(templates_dir, filename)
            with open(filepath) as f:
                template = f.read()

            is_dynamic = cache.has_dynamic_constructs(template)
            if not is_dynamic and not cache.needs_rebuild(filename, template):
                cached_files += 1
                continue

            rendered = engine.render(template, context={"content": list(collection)})
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w") as f:
                f.write(rendered)

            if not is_dynamic:
                cache.update(filename, template)
            built_files += 1

        return total_files, built_files, cached_files

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
            self._info(f"Copied static assets -> {static_output}")

    def _generate_feeds(self, config: SiteConfig, output_dir: Path, collection) -> int:
        if not config.feeds:
            return 0

        self._info("Generating RSS feeds...")
        generator = RssFeedGenerator(config=config)
        feed_count = 0
        for output_name, xml in generator.generate(collection):
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
        self._success("Build complete!")
        self._success(f"Total files: {render_summary.total_files}")
        self._success(f"Total components: {len(render_summary.component_names)}")
        self._success(f"Built: {render_summary.built_files}")
        self._success(f"Cached: {render_summary.cached_files}")
        self._success(f"RSS feeds: {feed_count}")
        self._success(f"Parsing time: {parsing_time:.3f}s")
        self._success(f"Rendering time: {render_summary.rendering_time:.3f}s")
        self._success(f"Total time: {total_time:.3f}s")
