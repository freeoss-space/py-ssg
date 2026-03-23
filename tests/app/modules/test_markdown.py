from pathlib import Path
from unittest.mock import mock_open, patch

from pyssg.modules.markdown import MarkdownParser

TEST_PATH = "pyssg.modules.markdown"


class TestParse:
    @patch(f"{TEST_PATH}.os")
    def test_returns_empty_dict_when_no_markdown_files(self, mock_os):
        mock_os.listdir.return_value = ["image.png", "notes.txt"]
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert result == {}

    @patch(f"{TEST_PATH}.open", mock_open(read_data="# Hello\n\nWorld"))
    @patch(f"{TEST_PATH}.os")
    def test_parses_single_markdown_file(self, mock_os):
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert "post.md" in result
        assert "<h1>Hello</h1>" in result["post.md"]
        assert "<p>World</p>" in result["post.md"]

    @patch(f"{TEST_PATH}.open", mock_open(read_data="**bold**"))
    @patch(f"{TEST_PATH}.os")
    def test_parses_multiple_markdown_files(self, mock_os):
        mock_os.listdir.return_value = ["a.md", "b.md", "skip.txt"]
        mock_os.path.join.side_effect = lambda d, f: f"/fake/content/{f}"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert len(result) == 2
        assert "a.md" in result
        assert "b.md" in result
        assert "skip.txt" not in result
