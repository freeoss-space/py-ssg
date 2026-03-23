from unittest.mock import patch

from pyssg.commands.build import BuildCommand

TEST_PATH = "pyssg.commands.build"


class TestExecute:
    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_parses_markdown_from_content_dir(self, mock_path, mock_parser_cls):
        mock_path.cwd.return_value.__truediv__ = lambda self, x: f"/project/{x}"
        mock_parser_cls.return_value.parse.return_value = {"post.md": "<h1>Hello</h1>"}
        command = BuildCommand()

        with patch.object(command, "_info"):
            command.execute()

        mock_parser_cls.assert_called_once_with(content_dir="/project/content")
        mock_parser_cls.return_value.parse.assert_called_once()

    @patch(f"{TEST_PATH}.MarkdownParser")
    @patch(f"{TEST_PATH}.Path")
    def test_outputs_info_message(self, mock_path, mock_parser_cls):
        mock_path.cwd.return_value.__truediv__ = lambda self, x: f"/project/{x}"
        mock_parser_cls.return_value.parse.return_value = {}
        command = BuildCommand()

        with patch.object(command, "_info") as mock_info:
            command.execute()

        mock_info.assert_called_once_with("Parsing markdown files...")
