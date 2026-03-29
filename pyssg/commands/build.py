import os
import shutil
import time
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.build_script import BuildContext, BuildScript
from pyssg.modules.cache import BuildCache
from pyssg.modules.config import SiteConfig
from pyssg.modules.html import HtmlTemplateEngine
from pyssg.modules.markdown import MarkdownParser, TocGenerator
from pyssg.modules.rss import RssFeedGenerator
from pyssg.modules.syntax import SyntaxHighlighter


class BuildCommand(BaseCommand):
    def execute(self) -> None:
        start_time = time.perf_counter()

        project_dir = Path.cwd()
        templates_dir = project_dir / "templates"
        components_dir = project_dir / "components"
        output_dir = project_dir / "output"

        config = SiteConfig.load(project_dir)

        cache = BuildCache(cache_dir=project_dir, enabled=config.cache)
        cache.load()

        build_script = BuildScript(project_dir)
        context = BuildContext(
            config=config,
            cache=cache,
            project_dir=project_dir,
            templates_dir=templates_dir,
            components_dir=components_dir,
            output_dir=output_dir,
        )

        build_script.before_build(context)

        highlighter = None
        render_markdown = None
        if config.syntax.enabled:
            highlighter = SyntaxHighlighter(
                theme_light=config.syntax.theme_light,
                theme_dark=config.syntax.theme_dark,
            )
            render_markdown = highlighter.render_markdown

        toc_generator = None
        if config.toc.enabled:
            toc_generator = TocGenerator(max_depth=config.toc.max_depth)

        build_script.before_markdown_parsing(context)

        self._info("Parsing markdown files...")
        parsing_start = time.perf_counter()
        parser = MarkdownParser(
            content_dir=project_dir / "content",
            render_markdown=render_markdown,
            toc_generator=toc_generator,
        )
        workers = os.cpu_count() or 1
        collection = parser.parse(
            workers=workers,
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
        parsing_time = time.perf_counter() - parsing_start

        context.content = collection

        build_script.before_component_parsing(context)

        self._info("Rendering templates...")
        rendering_start = time.perf_counter()
        component_names = [
            f.removesuffix(".html")
            for f in os.listdir(components_dir)
            if f.endswith(".html")
        ]
        engine = HtmlTemplateEngine(
            templates_dir=templates_dir,
            components_dir=components_dir,
            component_names=component_names,
            config=config,
        )
        os.makedirs(output_dir, exist_ok=True)

        total_files = 0
        built_files = 0
        cached_files = 0

        for entry in os.listdir(templates_dir):
            entry_path = os.path.join(templates_dir, entry)
            if os.path.isdir(entry_path):
                dest = os.path.join(output_dir, entry)
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(entry_path, dest)
                continue

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

        if highlighter:
            css_path = os.path.join(output_dir, "syntax.css")
            with open(css_path, "w") as f:
                f.write(highlighter.get_stylesheet())

        rendering_time = time.perf_counter() - rendering_start

        feed_count = 0
        if config.feeds:
            self._info("Generating RSS feeds...")
            generator = RssFeedGenerator(config=config)
            for output_name, xml in generator.generate(collection):
                output_path = os.path.join(output_dir, output_name)
                with open(output_path, "w") as f:
                    f.write(xml)
                feed_count += 1

        cache.save()

        build_script.after_build(context)

        total_time = time.perf_counter() - start_time

        self._success("Build complete!")
        self._success(f"Total files: {total_files}")
        self._success(f"Total components: {len(component_names)}")
        self._success(f"Built: {built_files}")
        self._success(f"Cached: {cached_files}")
        self._success(f"RSS feeds: {feed_count}")
        self._success(f"Parsing time: {parsing_time:.3f}s")
        self._success(f"Rendering time: {rendering_time:.3f}s")
        self._success(f"Total time: {total_time:.3f}s")
