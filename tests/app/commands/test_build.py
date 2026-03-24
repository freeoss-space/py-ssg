from unittest.mock import MagicMock, mock_open, patch

from pyssg.commands.build import BuildCommand
from pyssg.modules.config import SiteConfig, SyntaxConfig
from pyssg.modules.markdown import MarkdownCollection, MarkdownContent

TEST_POST = MarkdownContent(filename="post.md", html="<p>Hi</p>", title="Post")

TEST_PATH = "pyssg.commands.build"


def _default_config(**overrides):
    syntax = overrides.get("syntax", SyntaxConfig(enabled=False))
    return SiteConfig(
        name=overrides.get("name", ""),
        url=overrides.get("url", ""),
        description=overrides.get("description", ""),
        cache=overrides.get("cache", True),
        syntax=syntax,
    )


def _setup_path_and_os(mock_path, mock_os, template_files=None, component_files=None):
    """Common setup for path and os mocks."""
    mock_path.cwd.return_value.__truediv__ = lambda self, x: f"/project/{x}"
    template_files = template_files or []
    component_files = component_files or []

    def listdir_side_effect(path):
        if str(path) == "/project/templates":
            return template_files
        if str(path) == "/project/components":
            return component_files
        return []

    mock_os.listdir.side_effect = listdir_side_effect
    mock_os.path.join.side_effect = lambda d, f: f"{d}/{f}"
    mock_os.path.exists.return_value = False


def _setup_cache(mock_cache_cls):
    """Common setup for cache mock - always rebuilds by default."""
    mock_cache = mock_cache_cls.return_value
    mock_cache.has_dynamic_constructs.return_value = False
    mock_cache.needs_rebuild.return_value = True
    return mock_cache


class TestExecute:
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_parses_markdown_from_content_dir(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_parser_cls.assert_called_once_with(
            content_dir="/project/content", render_markdown=None
        )
        mock_parser_cls.return_value.parse.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_info_message(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with (
            patch.object(command, "_info") as mock_info,
            patch.object(command, "_success"),
        ):
            command.execute()

        mock_info.assert_any_call("Parsing markdown files...")

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_template_engine_with_components(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(
            mock_path, mock_os, component_files=["Navbar.html", "Footer.html"]
        )
        _setup_cache(mock_cache_cls)
        config = _default_config()
        mock_config_cls.load.return_value = config
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_engine_cls.assert_called_once_with(
            templates_dir="/project/templates",
            components_dir="/project/components",
            component_names=["Navbar", "Footer"],
            config=config,
        )

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_discovers_only_html_components(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            component_files=["Navbar.html", "README.md", "styles.css"],
        )
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_engine_cls.call_args[1]
        assert call_kwargs["component_names"] == ["Navbar"]

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_renders_each_template_file(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(
            mock_path, mock_os, template_files=["index.html", "about.html", "style.css"]
        )
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        collection = MarkdownCollection()
        collection.add(
            MarkdownContent(filename="post.md", html="<p>Hi</p>", title="Post")
        )
        mock_parser_cls.return_value.parse.return_value = collection
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        assert mock_engine_cls.return_value.render.call_count == 2

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_passes_content_as_context(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        collection = MarkdownCollection()
        collection.add(TEST_POST)
        mock_parser_cls.return_value.parse.return_value = collection
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_engine_cls.return_value.render.assert_called_once_with(
            "<h1>Template</h1>", context={"content": [TEST_POST]}
        )

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_writes_rendered_output_to_output_dir(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_os.makedirs = MagicMock()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"

        read_handle = mock_open(read_data="<h1>Template</h1>")()
        write_handle = mock_open()()
        mock_file.side_effect = [read_handle, write_handle]

        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        write_handle.write.assert_called_once_with("<h1>Rendered</h1>")

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_output_directory(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_os.makedirs.assert_called_once_with("/project/output", exist_ok=True)

    @patch(f"{TEST_PATH}.time")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_success_message(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_time,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_time.perf_counter.return_value = 0.0
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_any_call("Build complete!")

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_loads_config_from_project_dir(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_config_cls.load.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_passes_cache_enabled_from_config(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(cache=False)
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_cache_cls.call_args[1]
        assert call_kwargs["enabled"] is False


class TestCache:
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_loads_cache_at_start(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_cache.load.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_saves_cache_after_build(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_cache.save.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_skips_unchanged_static_template(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = False
        mock_cache.needs_rebuild.return_value = False
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_engine_cls.return_value.render.assert_not_called()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_always_rebuilds_dynamic_template(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = True
        mock_cache.needs_rebuild.return_value = False
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_engine_cls.return_value.render.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_updates_cache_after_rendering_static_template(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = False
        mock_cache.needs_rebuild.return_value = True
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_cache.update.assert_called_once_with("index.html", "<h1>Static</h1>")

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_does_not_update_cache_for_dynamic_template(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = True
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_cache.update.assert_not_called()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_does_not_update_cache_for_skipped_template(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = False
        mock_cache.needs_rebuild.return_value = False
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_cache.update.assert_not_called()


class TestSummary:
    @patch(f"{TEST_PATH}.time")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_reports_total_files(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_time,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            template_files=["index.html", "about.html"],
        )
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_time.perf_counter.return_value = 0.0
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_any_call("Total files: 2")

    @patch(f"{TEST_PATH}.time")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_reports_total_components(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_time,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            template_files=["index.html"],
            component_files=["Navbar.html", "Footer.html"],
        )
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_time.perf_counter.return_value = 0.0
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_any_call("Total components: 2")

    @patch(f"{TEST_PATH}.time")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_reports_built_and_cached_files(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_time,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            template_files=["index.html", "about.html", "contact.html"],
        )
        mock_cache = _setup_cache(mock_cache_cls)
        mock_cache.has_dynamic_constructs.return_value = False
        mock_cache.needs_rebuild.side_effect = [True, False, True]
        mock_config_cls.load.return_value = _default_config()
        mock_time.perf_counter.return_value = 0.0
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_any_call("Built: 2")
        mock_success.assert_any_call("Cached: 1")

    @patch(f"{TEST_PATH}.time")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Static</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_reports_timing(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_time,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_time.perf_counter.side_effect = [0.0, 0.0, 0.05, 0.05, 0.15, 0.20]
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_any_call("Parsing time: 0.050s")
        mock_success.assert_any_call("Rendering time: 0.100s")
        mock_success.assert_any_call("Total time: 0.200s")


class TestSyntaxHighlighting:
    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open)
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_passes_render_markdown_to_parser(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_highlighter_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(syntax=SyntaxConfig())
        mock_highlighter = mock_highlighter_cls.return_value
        mock_highlighter.get_stylesheet.return_value = ""
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_parser_cls.assert_called_once_with(
            content_dir="/project/content",
            render_markdown=mock_highlighter.render_markdown,
        )

    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open)
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_writes_stylesheet_to_output_dir(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_highlighter_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(syntax=SyntaxConfig())
        mock_highlighter = mock_highlighter_cls.return_value
        mock_highlighter.get_stylesheet.return_value = ".highlight { color: red; }"
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_os.path.join.assert_any_call("/project/output", "syntax.css")

    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open)
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_highlighter_with_config_themes(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_highlighter_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        config = _default_config(
            syntax=SyntaxConfig(enabled=True, theme_light="tango", theme_dark="dracula")
        )
        mock_config_cls.load.return_value = config
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_highlighter_cls.return_value.get_stylesheet.return_value = ""
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_highlighter_cls.assert_called_once_with(
            theme_light="tango",
            theme_dark="dracula",
        )

    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_skips_highlighting_when_disabled(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_highlighter_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(
            syntax=SyntaxConfig(enabled=False)
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_highlighter_cls.assert_not_called()

    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_does_not_pass_render_markdown_when_disabled(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_highlighter_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(
            syntax=SyntaxConfig(enabled=False)
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_parser_cls.assert_called_once_with(
            content_dir="/project/content",
            render_markdown=None,
        )
