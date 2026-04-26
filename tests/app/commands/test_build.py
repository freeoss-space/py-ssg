from pathlib import Path
from types import MappingProxyType
from unittest.mock import MagicMock, call, patch

from pyssg.commands.build import (
    BuildCommand,
    BuildPaths,
    RenderSummary,
    TemplateRenderResult,
    _copy_static_assets,
    _discover_components,
)
from pyssg.modules.config import FeedConfig, SiteConfig, SyntaxConfig, TocConfig
from pyssg.modules.markdown import MarkdownCollection, MarkdownContent

TEST_PATH = "pyssg.commands.build"


def _default_config(
    *,
    name: str = "",
    url: str = "",
    description: str = "",
    static_dir: str = "static",
    static_dir_output: str = "static",
    content_sort: str = "date_desc",
    cache: bool = True,
    syntax: SyntaxConfig | None = None,
    toc: TocConfig | None = None,
) -> SiteConfig:
    syntax = syntax or SyntaxConfig(enabled=False)
    toc = toc or TocConfig(enabled=False)
    return SiteConfig(
        name=name,
        url=url,
        description=description,
        static_dir=static_dir,
        static_dir_output=static_dir_output,
        content_sort=content_sort,
        cache=cache,
        syntax=syntax,
        toc=toc,
    )


def _make_collection(*posts: MarkdownContent) -> MarkdownCollection:
    collection = MarkdownCollection()
    for post in posts:
        collection.add(post)
    return collection


class SilentBuildCommand(BuildCommand):
    def _info(self, message: str) -> None:
        pass

    def _success(self, message: str) -> None:
        pass


class RecordingBuildCommand(BuildCommand):
    def __init__(
        self,
        paths: BuildPaths,
        collection: MarkdownCollection,
        render_summary: RenderSummary,
        feed_count: int,
    ) -> None:
        self.paths = paths
        self.collection = collection
        self.render_summary = render_summary
        self.feed_count = feed_count
        self.calls: list[str] = []
        self.summary_args: dict[str, object] | None = None

    def _info(self, message: str) -> None:
        pass

    def _success(self, message: str) -> None:
        pass

    def _build_paths(self) -> BuildPaths:
        self.calls.append("build_paths")
        return self.paths

    def _create_highlighter(self, config: SiteConfig) -> None:
        self.calls.append("create_highlighter")
        return None

    def _create_toc_generator(self, config: SiteConfig) -> None:
        self.calls.append("create_toc_generator")
        return None

    def _parse_markdown(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        render_markdown,
        toc_generator,
    ) -> tuple[MarkdownCollection, float]:
        self.calls.append("parse_markdown")
        return self.collection, 0.25

    def _render_templates(
        self,
        paths: BuildPaths,
        config: SiteConfig,
        cache,
        collection: MarkdownCollection,
        highlighter,
    ) -> RenderSummary:
        self.calls.append("render_templates")
        return self.render_summary

    def _generate_feeds(
        self,
        config: SiteConfig,
        output_dir: Path,
        collection: MarkdownCollection,
    ) -> int:
        self.calls.append("generate_feeds")
        return self.feed_count

    def _print_summary(
        self,
        render_summary: RenderSummary,
        feed_count: int,
        parsing_time: float,
        total_time: float,
    ) -> None:
        self.calls.append("print_summary")
        self.summary_args = {
            "render_summary": render_summary,
            "feed_count": feed_count,
            "parsing_time": parsing_time,
            "total_time": total_time,
        }


def test_discover_components_supports_nested_directories(tmp_path: Path) -> None:
    components_dir = tmp_path / "components"
    components_dir.mkdir()
    (components_dir / "Navbar.html").write_text("", encoding="utf-8")
    (components_dir / "README.md").write_text("", encoding="utf-8")
    ui_dir = components_dir / "UI"
    ui_dir.mkdir()
    (ui_dir / "Card.html").write_text("", encoding="utf-8")
    nested_dir = ui_dir / "Forms"
    nested_dir.mkdir()
    (nested_dir / "Input.html").write_text("", encoding="utf-8")

    component_names = _discover_components(components_dir)

    assert sorted(component_names) == ["Navbar", "UI.Card", "UI.Forms.Input"]


def test_copy_static_assets_copies_to_static_directory_by_default(
    tmp_path: Path,
) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "site.css").write_text("body {}", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    output_path = _copy_static_assets(static_dir, output_dir, "static")

    assert output_path == "output/static/"
    assert (output_dir / "static" / "site.css").read_text(encoding="utf-8") == "body {}"


def test_copy_static_assets_returns_none_when_source_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    output_path = _copy_static_assets(tmp_path / "missing-static", output_dir, "static")

    assert output_path is None


@patch(f"{TEST_PATH}.Path.cwd")
def test_build_paths_use_project_directories(mock_cwd: MagicMock) -> None:
    mock_cwd.return_value = Path("/project")
    command = BuildCommand()

    paths = command._build_paths()

    assert paths == BuildPaths(
        project_dir=Path("/project"),
        templates_dir=Path("/project/templates"),
        components_dir=Path("/project/components"),
        output_dir=Path("/project/output"),
    )


@patch(f"{TEST_PATH}.SyntaxHighlighter")
def test_create_highlighter_returns_instance_when_enabled(
    mock_highlighter_cls: MagicMock,
) -> None:
    config = _default_config(
        syntax=SyntaxConfig(enabled=True, theme_light="tango", theme_dark="dracula")
    )
    command = BuildCommand()

    highlighter = command._create_highlighter(config)

    assert highlighter is mock_highlighter_cls.return_value
    mock_highlighter_cls.assert_called_once_with(
        theme_light="tango",
        theme_dark="dracula",
    )


def test_create_highlighter_returns_none_when_disabled() -> None:
    command = BuildCommand()

    highlighter = command._create_highlighter(
        _default_config(syntax=SyntaxConfig(enabled=False))
    )

    assert highlighter is None


@patch(f"{TEST_PATH}.TocGenerator")
def test_create_toc_generator_returns_instance_when_enabled(
    mock_toc_cls: MagicMock,
) -> None:
    config = _default_config(toc=TocConfig(enabled=True, max_depth=4))
    command = BuildCommand()

    toc_generator = command._create_toc_generator(config)

    assert toc_generator is mock_toc_cls.return_value
    mock_toc_cls.assert_called_once_with(max_depth=4)


def test_create_toc_generator_returns_none_when_disabled() -> None:
    command = BuildCommand()

    toc_generator = command._create_toc_generator(
        _default_config(toc=TocConfig(enabled=False))
    )

    assert toc_generator is None


def test_sort_content_defaults_to_newest_first_and_undated_last() -> None:
    command = BuildCommand()
    older = MarkdownContent(filename="older.md", html="", timestamp="2024-01-01")
    newer = MarkdownContent(filename="newer.md", html="", timestamp="2025-01-01")
    undated = MarkdownContent(filename="undated.md", html="")

    sorted_content = command._sort_content(
        _make_collection(older, undated, newer), "date_desc"
    )

    assert sorted_content == [newer, older, undated]


def test_sort_content_supports_filename_order() -> None:
    command = SilentBuildCommand()
    z_post = MarkdownContent(filename="z-post.md", html="")
    a_post = MarkdownContent(filename="a-post.md", html="")

    sorted_content = command._sort_content(_make_collection(z_post, a_post), "filename")

    assert sorted_content == [a_post, z_post]


def test_sort_content_supports_date_ascending() -> None:
    command = SilentBuildCommand()
    older = MarkdownContent(filename="older.md", html="", timestamp="2024-01-01")
    newer = MarkdownContent(filename="newer.md", html="", timestamp="2025-01-01")
    undated = MarkdownContent(filename="undated.md", html="")

    sorted_content = command._sort_content(
        _make_collection(newer, undated, older), "date_asc"
    )

    assert sorted_content == [older, newer, undated]


def test_sort_content_supports_none() -> None:
    command = SilentBuildCommand()
    first = MarkdownContent(filename="first.md", html="")
    second = MarkdownContent(filename="second.md", html="")

    sorted_content = command._sort_content(_make_collection(first, second), "none")

    assert sorted_content == [first, second]


def test_build_tag_map_groups_posts_by_tag_in_sorted_order() -> None:
    command = SilentBuildCommand()
    newest = MarkdownContent(
        filename="newest.md",
        html="",
        timestamp="2025-01-01",
        tags=["python", "release"],
    )
    older = MarkdownContent(
        filename="older.md",
        html="",
        timestamp="2024-01-01",
        tags=["python"],
    )
    undated = MarkdownContent(filename="undated.md", html="", tags=["notes"])

    tag_map = command._build_tag_map([newest, older, undated])

    assert isinstance(tag_map, MappingProxyType)
    assert tag_map == {
        "python": (newest, older),
        "release": (newest,),
        "notes": (undated,),
    }


@patch.object(BuildCommand, "_info")
@patch(f"{TEST_PATH}.MarkdownParser")
@patch(f"{TEST_PATH}.os.cpu_count")
def test_parse_markdown_configures_parser_and_returns_timing(
    mock_cpu_count: MagicMock,
    mock_parser_cls: MagicMock,
    mock_info: MagicMock,
) -> None:
    mock_cpu_count.return_value = 4
    collection = _make_collection(MarkdownContent(filename="post.md", html=""))
    mock_parser_cls.return_value.parse.return_value = collection
    paths = BuildPaths(
        project_dir=Path("/project"),
        templates_dir=Path("/project/templates"),
        components_dir=Path("/project/components"),
        output_dir=Path("/project/output"),
    )
    config = _default_config(
        syntax=SyntaxConfig(enabled=True, theme_light="friendly", theme_dark="monokai"),
        toc=TocConfig(enabled=True, max_depth=2),
    )
    command = BuildCommand()

    parsed_collection, parsing_time = command._parse_markdown(
        paths=paths,
        config=config,
        render_markdown=None,
        toc_generator=None,
    )

    assert parsed_collection is collection
    assert parsing_time >= 0
    mock_info.assert_called_once_with("Parsing markdown files...")
    mock_parser_cls.assert_called_once_with(
        content_dir=Path("/project/content"),
        render_markdown=None,
        toc_generator=None,
    )
    mock_parser_cls.return_value.parse.assert_called_once_with(
        workers=4,
        syntax_config={
            "enabled": True,
            "theme_light": "friendly",
            "theme_dark": "monokai",
        },
        toc_config={"enabled": True, "max_depth": 2},
    )


def test_copy_template_directories_replaces_existing_directory(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    assets_dir = templates_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "new.css").write_text("new", encoding="utf-8")
    (templates_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    existing_assets_dir = output_dir / "assets"
    existing_assets_dir.mkdir()
    (existing_assets_dir / "old.css").write_text("old", encoding="utf-8")
    paths = BuildPaths(
        project_dir=tmp_path,
        templates_dir=templates_dir,
        components_dir=tmp_path / "components",
        output_dir=output_dir,
    )
    command = BuildCommand()

    command._copy_template_directories(paths)

    assert not (output_dir / "assets" / "old.css").exists()
    assert (output_dir / "assets" / "new.css").read_text(encoding="utf-8") == "new"


def test_render_template_file_builds_static_template(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("<h1>Template</h1>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    engine = MagicMock()
    engine.render.return_value = "<h1>Rendered</h1>"
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = False
    cache.needs_rebuild.return_value = True
    command = BuildCommand()
    post = MarkdownContent(filename="post.md", html="<p>Hi</p>", title="Post")

    result = command._render_template_file(
        filename="index.html",
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        sorted_content=[post],
        tag_map=MappingProxyType({"python": (post,)}),
        cache=cache,
    )

    assert result == TemplateRenderResult(built=True, cached=False)
    engine.render.assert_called_once_with(
        "<h1>Template</h1>",
        context={"content": (post,), "tags": MappingProxyType({"python": (post,)})},
    )
    cache.update.assert_called_once_with("index.html", "<h1>Template</h1>")
    assert (output_dir / "index.html").read_text(
        encoding="utf-8"
    ) == "<h1>Rendered</h1>"


def test_render_template_file_skips_unchanged_static_template(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("<h1>Template</h1>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    engine = MagicMock()
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = False
    cache.needs_rebuild.return_value = False
    command = BuildCommand()

    result = command._render_template_file(
        filename="index.html",
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        sorted_content=[],
        tag_map={},
        cache=cache,
    )

    assert result == TemplateRenderResult(built=False, cached=True)
    engine.render.assert_not_called()
    cache.update.assert_not_called()
    assert not (output_dir / "index.html").exists()


def test_render_template_file_does_not_update_cache_for_dynamic_templates(
    tmp_path: Path,
) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text(
        "{% for post in content %}", encoding="utf-8"
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    engine = MagicMock()
    engine.render.return_value = "<h1>Rendered</h1>"
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = True
    cache.needs_rebuild.return_value = False
    command = BuildCommand()

    result = command._render_template_file(
        filename="index.html",
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        sorted_content=[],
        tag_map={},
        cache=cache,
    )

    assert result == TemplateRenderResult(built=True, cached=False)
    cache.update.assert_not_called()


def test_render_template_files_counts_only_html_files(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    (templates_dir / "about.html").write_text("<h1>About</h1>", encoding="utf-8")
    (templates_dir / "styles.css").write_text("body {}", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    engine = MagicMock()
    engine.render.side_effect = ["<h1>Home</h1>", "<h1>About</h1>"]
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = False
    cache.needs_rebuild.return_value = True
    command = SilentBuildCommand()

    summary = command._render_template_files(
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        collection=_make_collection(),
        cache=cache,
        content_sort="date_desc",
    )

    assert summary == (2, 2, 0)
    assert engine.render.call_count == 2


def test_render_template_files_passes_immutable_sorted_content(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    newer = MarkdownContent(filename="new.md", html="", timestamp="2025-01-01")
    older = MarkdownContent(filename="old.md", html="", timestamp="2024-01-01")
    engine = MagicMock()
    engine.render.return_value = "<h1>Rendered</h1>"
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = False
    cache.needs_rebuild.return_value = True
    command = SilentBuildCommand()

    command._render_template_files(
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        collection=_make_collection(older, newer),
        cache=cache,
        content_sort="date_desc",
    )

    render_context = engine.render.call_args.kwargs["context"]
    assert render_context["content"] == (newer, older)
    assert isinstance(render_context["content"], tuple)


def test_render_template_files_passes_tags_mapping_to_templates(tmp_path: Path) -> None:
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    newer = MarkdownContent(
        filename="new.md",
        html="",
        timestamp="2025-01-01",
        tags=["python", "release"],
    )
    older = MarkdownContent(
        filename="old.md",
        html="",
        timestamp="2024-01-01",
        tags=["python"],
    )
    engine = MagicMock()
    engine.render.return_value = "<h1>Rendered</h1>"
    cache = MagicMock()
    cache.has_dynamic_constructs.return_value = False
    cache.needs_rebuild.return_value = True
    command = SilentBuildCommand()

    command._render_template_files(
        templates_dir=templates_dir,
        output_dir=output_dir,
        engine=engine,
        collection=_make_collection(older, newer),
        cache=cache,
        content_sort="date_desc",
    )

    render_context = engine.render.call_args.kwargs["context"]
    assert isinstance(render_context["tags"], MappingProxyType)
    assert render_context["tags"] == {
        "python": (newer, older),
        "release": (newer,),
    }


def test_write_syntax_stylesheet_writes_css_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    highlighter = MagicMock()
    highlighter.get_stylesheet.return_value = "body { color: red; }"
    command = SilentBuildCommand()

    command._write_syntax_stylesheet(output_dir=output_dir, highlighter=highlighter)

    assert (output_dir / "syntax.css").read_text(
        encoding="utf-8"
    ) == "body { color: red; }"


@patch.object(BuildCommand, "_info")
def test_copy_static_assets_reports_destination(
    mock_info: MagicMock, tmp_path: Path
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    static_dir = project_dir / "static"
    static_dir.mkdir()
    (static_dir / "site.css").write_text("body {}", encoding="utf-8")
    output_dir = project_dir / "output"
    output_dir.mkdir()
    command = BuildCommand()
    paths = BuildPaths(
        project_dir=project_dir,
        templates_dir=project_dir / "templates",
        components_dir=project_dir / "components",
        output_dir=output_dir,
    )

    command._copy_static_assets(paths, _default_config())

    mock_info.assert_called_once_with("Copied static assets -> output/static/")
    assert (output_dir / "static" / "site.css").exists()


@patch.object(BuildCommand, "_info")
@patch(f"{TEST_PATH}.RssFeedGenerator")
def test_generate_feeds_writes_each_feed_and_returns_count(
    mock_generator_cls: MagicMock,
    mock_info: MagicMock,
    tmp_path: Path,
) -> None:
    config = _default_config()
    config.feeds = [FeedConfig(title="Main"), FeedConfig(title="News")]
    collection = _make_collection(MarkdownContent(filename="post.md", html="<p>Hi</p>"))
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    mock_generator_cls.return_value.generate.return_value = [
        ("feed.xml", "<rss />"),
        ("news.xml", "<rss />"),
    ]
    command = BuildCommand()

    feed_count = command._generate_feeds(
        config=config,
        output_dir=output_dir,
        collection=collection,
    )

    assert feed_count == 2
    mock_info.assert_called_once_with("Generating RSS feeds...")
    mock_generator_cls.assert_called_once_with(config=config)
    assert (output_dir / "feed.xml").read_text(encoding="utf-8") == "<rss />"
    assert (output_dir / "news.xml").read_text(encoding="utf-8") == "<rss />"


@patch.object(BuildCommand, "_info")
@patch(f"{TEST_PATH}.RssFeedGenerator")
def test_generate_feeds_skips_generator_when_no_feeds_configured(
    mock_generator_cls: MagicMock,
    mock_info: MagicMock,
    tmp_path: Path,
) -> None:
    command = BuildCommand()

    feed_count = command._generate_feeds(
        config=_default_config(),
        output_dir=tmp_path,
        collection=_make_collection(),
    )

    assert feed_count == 0
    mock_info.assert_not_called()
    mock_generator_cls.assert_not_called()


@patch.object(BuildCommand, "_success")
def test_print_summary_reports_all_totals(mock_success: MagicMock) -> None:
    command = BuildCommand()
    render_summary = RenderSummary(
        total_files=3,
        built_files=2,
        cached_files=1,
        component_names=["Navbar", "UI.Card"],
        rendering_time=0.2,
    )

    command._print_summary(
        render_summary=render_summary,
        feed_count=4,
        parsing_time=0.1,
        total_time=0.4,
    )

    assert mock_success.call_args_list == [
        call("Build complete!"),
        call("Total files: 3"),
        call("Total components: 2"),
        call("Built: 2"),
        call("Cached: 1"),
        call("RSS feeds: 4"),
        call("Parsing time: 0.100s"),
        call("Rendering time: 0.200s"),
        call("Total time: 0.400s"),
    ]


@patch(f"{TEST_PATH}.time.perf_counter")
@patch(f"{TEST_PATH}.BuildScript")
@patch(f"{TEST_PATH}.BuildCache")
@patch(f"{TEST_PATH}.SiteConfig.load")
def test_execute_orchestrates_build_steps_and_updates_context(
    mock_load_config: MagicMock,
    mock_cache_cls: MagicMock,
    mock_build_script_cls: MagicMock,
    mock_perf_counter: MagicMock,
) -> None:
    paths = BuildPaths(
        project_dir=Path("/project"),
        templates_dir=Path("/project/templates"),
        components_dir=Path("/project/components"),
        output_dir=Path("/project/output"),
    )
    collection = _make_collection(MarkdownContent(filename="post.md", html="<p>Hi</p>"))
    render_summary = RenderSummary(
        total_files=1,
        built_files=1,
        cached_files=0,
        component_names=["Navbar"],
        rendering_time=0.5,
    )
    command = RecordingBuildCommand(
        paths=paths,
        collection=collection,
        render_summary=render_summary,
        feed_count=2,
    )
    config = _default_config(name="Example")
    mock_load_config.return_value = config
    mock_perf_counter.side_effect = [10.0, 12.0]
    mock_cache = mock_cache_cls.return_value
    mock_script = mock_build_script_cls.return_value
    seen_content: list[MarkdownCollection | None] = []
    mock_script.before_build.side_effect = lambda ctx: seen_content.append(ctx.content)
    mock_script.after_build.side_effect = lambda ctx: seen_content.append(ctx.content)

    command.execute()

    assert command.calls == [
        "build_paths",
        "create_highlighter",
        "create_toc_generator",
        "parse_markdown",
        "render_templates",
        "generate_feeds",
        "print_summary",
    ]
    mock_load_config.assert_called_once_with(Path("/project"))
    mock_cache_cls.assert_called_once_with(cache_dir=Path("/project"), enabled=True)
    mock_cache.load.assert_called_once()
    mock_cache.save.assert_called_once()
    mock_build_script_cls.assert_called_once_with(Path("/project"))
    mock_script.before_build.assert_called_once()
    mock_script.before_markdown_parsing.assert_called_once()
    mock_script.before_component_parsing.assert_called_once()
    mock_script.after_build.assert_called_once()
    assert seen_content[0] is None
    assert seen_content[1] is collection
    assert command.summary_args == {
        "render_summary": render_summary,
        "feed_count": 2,
        "parsing_time": 0.25,
        "total_time": 2.0,
    }
