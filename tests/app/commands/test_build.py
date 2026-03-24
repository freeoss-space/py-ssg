from unittest.mock import MagicMock, mock_open, patch

from pyssg.commands.build import BuildCommand
from pyssg.modules.markdown import MarkdownCollection, MarkdownContent

TEST_POST = MarkdownContent(filename="post.md", html="<p>Hi</p>", title="Post")

TEST_PATH = "pyssg.commands.build"


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


class TestExecute:
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_parses_markdown_from_content_dir(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os
    ):
        _setup_path_and_os(mock_path, mock_os)
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_parser_cls.assert_called_once_with(content_dir="/project/content")
        mock_parser_cls.return_value.parse.assert_called_once()

    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_info_message(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os
    ):
        _setup_path_and_os(mock_path, mock_os)
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with (
            patch.object(command, "_info") as mock_info,
            patch.object(command, "_success"),
        ):
            command.execute()

        mock_info.assert_any_call("Parsing markdown files...")

    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_template_engine_with_components(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os
    ):
        _setup_path_and_os(
            mock_path, mock_os, component_files=["Navbar.html", "Footer.html"]
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_engine_cls.assert_called_once_with(
            templates_dir="/project/templates",
            components_dir="/project/components",
            component_names=["Navbar", "Footer"],
        )

    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_discovers_only_html_components(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os
    ):
        _setup_path_and_os(
            mock_path,
            mock_os,
            component_files=["Navbar.html", "README.md", "styles.css"],
        )
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        call_kwargs = mock_engine_cls.call_args[1]
        assert call_kwargs["component_names"] == ["Navbar"]

    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_renders_each_template_file(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os, mock_file
    ):
        _setup_path_and_os(
            mock_path, mock_os, template_files=["index.html", "about.html", "style.css"]
        )
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

    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_passes_content_as_context(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os, mock_file
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
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

    @patch(f"{TEST_PATH}.open")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_writes_rendered_output_to_output_dir(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os, mock_file
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
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

    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_creates_output_directory(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os, mock_file
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with patch.object(command, "_info"), patch.object(command, "_success"):
            command.execute()

        mock_os.makedirs.assert_called_once_with("/project/output", exist_ok=True)

    @patch(f"{TEST_PATH}.open", new_callable=mock_open, read_data="<h1>Template</h1>")
    @patch(f"{TEST_PATH}.os")
    @patch(f"{TEST_PATH}.HtmlTemplateEngine")
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_success_message(
        self, mock_path, mock_parser_cls, mock_engine_cls, mock_os, mock_file
    ):
        _setup_path_and_os(mock_path, mock_os, template_files=["index.html"])
        mock_parser_cls.return_value.parse.return_value = MarkdownCollection()
        mock_engine_cls.return_value.render.return_value = "<h1>Rendered</h1>"
        command = BuildCommand()

        with (
            patch.object(command, "_info"),
            patch.object(command, "_success") as mock_success,
        ):
            command.execute()

        mock_success.assert_called_once_with("Build complete!")
