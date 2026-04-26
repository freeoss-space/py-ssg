from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from pyssg.commands.build import BuildCommand, BuildPaths
from pyssg.modules.build_script import BuildContext
from pyssg.modules.config import FeedConfig, SiteConfig, SyntaxConfig, TocConfig
from pyssg.modules.markdown import MarkdownCollection, MarkdownContent

TEST_POST = MarkdownContent(filename="post.md", html="<p>Hi</p>", title="Post")

TEST_PATH = "pyssg.commands.build"


def _default_config(**overrides):
    syntax = overrides.get("syntax", SyntaxConfig(enabled=False))
    toc = overrides.get("toc", TocConfig(enabled=False))
    return SiteConfig(
        name=overrides.get("name", ""),
        url=overrides.get("url", ""),
        description=overrides.get("description", ""),
        static_dir=overrides.get("static_dir", "static"),
        static_dir_output=overrides.get("static_dir_output", "static"),
        cache=overrides.get("cache", True),
        syntax=syntax,
        toc=toc,
    )


def _setup_path_and_os(
    mock_path,
    mock_os,
    template_files=None,
    component_files=None,
    template_dirs=None,
    component_subdirs=None,
):
    """Common setup for path and os mocks."""
    mock_path.side_effect = Path
    mock_path.cwd.return_value.__truediv__ = lambda self, x: f"/project/{x}"
    template_files = template_files or []
    component_files = component_files or []
    template_dirs = template_dirs or []
    component_subdirs = component_subdirs or {}

    all_template_entries = template_dirs + template_files

    def listdir_side_effect(path):
        if str(path) == "/project/templates":
            return all_template_entries
        return []

    def isdir_side_effect(path):
        for d in template_dirs:
            if str(path) == f"/project/templates/{d}":
                return True
        return False

    mock_os.listdir.side_effect = listdir_side_effect
    mock_os.path.join.side_effect = lambda d, f: f"{d}/{f}"
    mock_os.path.exists.return_value = False
    mock_os.path.isdir.side_effect = isdir_side_effect

    walk_data = [
        ("/project/components", list(component_subdirs.keys()), component_files)
    ]
    for subdir, files in component_subdirs.items():
        walk_data.append((f"/project/components/{subdir}", [], files))
    mock_os.walk.return_value = walk_data


def _setup_cache(mock_cache_cls):
    """Common setup for cache mock - always rebuilds by default."""
    mock_cache = mock_cache_cls.return_value
    mock_cache.has_dynamic_constructs.return_value = False
    mock_cache.needs_rebuild.return_value = True
    return mock_cache


class TestExecute:
    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_parser_cls.assert_called_once_with(
            content_dir="/project/content",
            render_markdown=None,
            toc_generator=None,
        )
        mock_parser_cls.return_value.parse.assert_called_once()

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_copies_template_subdirectories_to_output(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(
            mock_path, mock_os, template_dirs=["assets"], template_files=["index.html"]
        )
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.copytree.assert_called_once_with(
            "/project/templates/assets", "/project/output/assets"
        )

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_removes_existing_output_subdir_before_copying(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_dirs=["assets"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_os.path.exists.return_value = True
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.rmtree.assert_called_once_with("/project/output/assets")
        mock_shutil.copytree.assert_called_once_with(
            "/project/templates/assets", "/project/output/assets"
        )

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_does_not_copy_html_files_as_directories(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.copytree.assert_not_called()

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_copies_static_directory_to_output_static(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_os.path.isdir.side_effect = lambda path: str(path) == "/project/static"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        assert mock_shutil.copytree.call_args_list[-1].args == (
            "/project/static",
            Path("/project/output/static"),
        )
        assert mock_shutil.copytree.call_args_list[-1].kwargs == {
            "dirs_exist_ok": False
        }

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_allows_existing_output_static_when_copying(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_os.path.isdir.side_effect = lambda path: str(path) == "/project/static"
        mock_os.path.exists.side_effect = lambda path: (
            str(path) == "/project/output/static"
        )
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.rmtree.assert_not_called()
        assert mock_shutil.copytree.call_args_list[-1].args == (
            "/project/static",
            Path("/project/output/static"),
        )
        assert mock_shutil.copytree.call_args_list[-1].kwargs == {"dirs_exist_ok": True}

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_copies_static_directory_to_output_root_when_configured(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(static_dir_output="root")
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_os.path.isdir.side_effect = lambda path: str(path) == "/project/static"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.copytree.assert_called_once_with(
            "/project/static", Path("/project/output"), dirs_exist_ok=False
        )

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_allows_existing_output_root_when_copying(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(static_dir_output="root")
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_os.path.isdir.side_effect = lambda path: str(path) == "/project/static"
        mock_os.path.exists.side_effect = lambda path: str(path) == "/project/output"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_shutil.copytree.assert_called_once_with(
            "/project/static", Path("/project/output"), dirs_exist_ok=True
        )

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.shutil")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_info_message_when_static_assets_are_copied(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_shutil,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_os.path.isdir.side_effect = lambda path: str(path) == "/project/static"
        command = BuildCommand()

        with (
            patch.object(command, "_info") as mock_info,
            patch.object(command, "_success"),
        ):
            command.execute()

        mock_info.assert_any_call("Copied static assets -> output/static/")

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_config_cls.load.assert_called_once()

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_discovers_subfolder_components_with_dot_syntax(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            component_subdirs={"UI": ["Card.html", "Button.html"]},
        )
        _setup_cache(mock_cache_cls)
        config = _default_config()
        mock_config_cls.load.return_value = config
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_engine_cls.call_args[1]
        assert "UI.Card" in call_kwargs["component_names"]
        assert "UI.Button" in call_kwargs["component_names"]

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_discovers_mixed_flat_and_subfolder_components(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            component_files=["Navbar.html"],
            component_subdirs={"UI": ["Card.html"]},
        )
        _setup_cache(mock_cache_cls)
        config = _default_config()
        mock_config_cls.load.return_value = config
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_engine_cls.call_args[1]
        assert "Navbar" in call_kwargs["component_names"]
        assert "UI.Card" in call_kwargs["component_names"]

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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
    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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
    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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
    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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
            toc_generator=None,
        )

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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

    @patch(f"{TEST_PATH}.BuildScript")
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
        mock_script_cls,
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
            toc_generator=None,
        )


class TestTocBuild:
    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.TocGenerator")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_toc_generator_when_enabled(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_toc_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(
            toc=TocConfig(enabled=True, max_depth=2)
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_toc_cls.assert_called_once_with(max_depth=2)

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.TocGenerator")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_passes_toc_generator_to_parser(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_toc_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(
            toc=TocConfig(enabled=True, max_depth=3)
        )
        mock_toc_gen = mock_toc_cls.return_value
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs["toc_generator"] is mock_toc_gen

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.TocGenerator")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_no_toc_generator_when_disabled(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_toc_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config(
            toc=TocConfig(enabled=False)
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_toc_cls.assert_not_called()
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs["toc_generator"] is None


class TestBuildScript:
    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_loads_build_script_from_project_dir(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_script_cls.assert_called_once()

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_calls_before_build_hook(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_script.before_build.assert_called_once()
        ctx = mock_script.before_build.call_args[0][0]
        assert isinstance(ctx, BuildContext)

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_calls_before_markdown_parsing_hook(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_script.before_markdown_parsing.assert_called_once()
        ctx = mock_script.before_markdown_parsing.call_args[0][0]
        assert isinstance(ctx, BuildContext)

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_calls_before_component_parsing_hook(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_file,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_script.before_component_parsing.assert_called_once()
        ctx = mock_script.before_component_parsing.call_args[0][0]
        assert isinstance(ctx, BuildContext)
        assert ctx.content is not None

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_calls_after_build_hook(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_script.after_build.assert_called_once()
        ctx = mock_script.after_build.call_args[0][0]
        assert isinstance(ctx, BuildContext)

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_context_has_config_and_cache(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        mock_cache = _setup_cache(mock_cache_cls)
        config = _default_config(name="Test Site")
        mock_config_cls.load.return_value = config
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        ctx = mock_script.before_build.call_args[0][0]
        assert ctx.config is config
        assert ctx.cache is mock_cache

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_after_build_context_has_content(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        collection = MarkdownCollection()
        collection.add(TEST_POST)
        mock_parser_cls.return_value.parse.return_value = collection
        mock_script = mock_script_cls.return_value
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        ctx = mock_script.after_build.call_args[0][0]
        assert ctx.content is not None
        assert len(list(ctx.content)) == 1

    @patch(f"{TEST_PATH}.BuildScript")
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.BuildCache")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_before_build_content_is_none(
        self,
        mock_path,
        mock_parser_cls,
        mock_engine_cls,
        mock_os,
        mock_cache_cls,
        mock_config_cls,
        mock_script_cls,
    ):
        _setup_path_and_os(mock_path, mock_os)
        _setup_cache(mock_cache_cls)
        mock_config_cls.load.return_value = _default_config()
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_script = mock_script_cls.return_value
        captured_content = {}
        mock_script.before_build.side_effect = lambda ctx: captured_content.update(
            {"content": ctx.content}
        )
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        assert captured_content["content"] is None


class TestHelpers:
    @patch(f"{TEST_PATH}.Path")
    def test_build_paths_uses_project_directories(self, mock_path):
        mock_project_dir = Path("/project")
        mock_path.cwd.return_value = mock_project_dir
        command = BuildCommand()

        paths = command._build_paths()

        assert paths == BuildPaths(
            project_dir=mock_project_dir,
            templates_dir=Path("/project/templates"),
            components_dir=Path("/project/components"),
            output_dir=Path("/project/output"),
        )

    @patch(f"{TEST_PATH}.SyntaxHighlighter")
    def test_create_highlighter_returns_instance_when_enabled(
        self, mock_highlighter_cls
    ):
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

    def test_create_highlighter_returns_none_when_disabled(self):
        command = BuildCommand()

        highlighter = command._create_highlighter(
            _default_config(syntax=SyntaxConfig(enabled=False))
        )

        assert highlighter is None

    @patch(f"{TEST_PATH}.TocGenerator")
    def test_create_toc_generator_returns_instance_when_enabled(self, mock_toc_cls):
        config = _default_config(toc=TocConfig(enabled=True, max_depth=4))
        command = BuildCommand()

        toc_generator = command._create_toc_generator(config)

        assert toc_generator is mock_toc_cls.return_value
        mock_toc_cls.assert_called_once_with(max_depth=4)

    def test_create_toc_generator_returns_none_when_disabled(self):
        command = BuildCommand()

        toc_generator = command._create_toc_generator(
            _default_config(toc=TocConfig(enabled=False))
        )

        assert toc_generator is None

    @patch(f"{TEST_PATH}.open", new_callable=mock_open)
    @patch(f"{TEST_PATH}.RssFeedGenerator")
    def test_generate_feeds_writes_each_feed_and_returns_count(
        self,
        mock_generator_cls,
        mock_file,
    ):
        config = _default_config()
        config.feeds = [FeedConfig(title="Main"), FeedConfig(title="News")]
        collection = MarkdownCollection()
        collection.add(TEST_POST)
        mock_generator_cls.return_value.generate.return_value = [
            ("feed.xml", "<rss />"),
            ("news.xml", "<rss />"),
        ]
        command = BuildCommand()

        with patch.object(command, "_info") as mock_info:
            feed_count = command._generate_feeds(
                config=config,
                output_dir=Path("/project/output"),
                collection=collection,
            )

        assert feed_count == 2
        mock_info.assert_called_once_with("Generating RSS feeds...")
        mock_generator_cls.assert_called_once_with(config=config)
        assert [call.args for call in mock_file.call_args_list] == [
            ("/project/output/feed.xml", "w"),
            ("/project/output/news.xml", "w"),
        ]

    @patch(f"{TEST_PATH}.open", new_callable=mock_open)
    @patch(f"{TEST_PATH}.RssFeedGenerator")
    def test_generate_feeds_skips_generator_when_no_feeds_configured(
        self,
        mock_generator_cls,
        mock_file,
    ):
        config = _default_config()
        config.feeds = []
        command = BuildCommand()

        with patch.object(command, "_info") as mock_info:
            feed_count = command._generate_feeds(
                config=config,
                output_dir=Path("/project/output"),
                collection=MarkdownCollection(),
            )

        assert feed_count == 0
        mock_info.assert_not_called()
        mock_generator_cls.assert_not_called()
        mock_file.assert_not_called()
