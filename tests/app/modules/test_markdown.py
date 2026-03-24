from pathlib import Path
from types import SimpleNamespace
from unittest.mock import mock_open, patch

from pyssg.modules.markdown import (
    ContentAuthor,
    MarkdownCollection,
    MarkdownContent,
    MarkdownParser,
    TocGenerator,
)

TEST_PATH = "pyssg.modules.markdown"


class TestContentAuthor:
    def test_default_values(self):
        author = ContentAuthor()

        assert author.name == ""
        assert author.email == ""
        assert author.avatar == ""
        assert author.url == ""

    def test_from_post_extracts_author_fields(self):
        post = SimpleNamespace(
            get=lambda key, default="": {
                "author": "Jane",
                "author_email": "jane@example.com",
                "author_avatar": "avatar.png",
                "author_url": "https://example.com",
            }.get(key, default)
        )

        author = ContentAuthor.from_post(post)

        assert author.name == "Jane"
        assert author.email == "jane@example.com"
        assert author.avatar == "avatar.png"
        assert author.url == "https://example.com"

    def test_from_post_with_no_author_fields(self):
        post = SimpleNamespace(get=lambda key, default="": default)

        author = ContentAuthor.from_post(post)

        assert author == ContentAuthor()


class TestMarkdownContent:
    def test_default_values(self):
        content = MarkdownContent(filename="test.md", html="<p>Hello</p>")

        assert content.filename == "test.md"
        assert content.html == "<p>Hello</p>"
        assert content.title == ""
        assert content.timestamp == ""
        assert content.tags == []
        assert content.author == ContentAuthor()

    def test_tags_default_is_independent_per_instance(self):
        a = MarkdownContent(filename="a.md", html="<p>a</p>")
        b = MarkdownContent(filename="b.md", html="<p>b</p>")
        a.tags.append("python")

        assert b.tags == []

    def test_from_raw_parses_markdown(self):
        content = MarkdownContent.from_raw("test.md", "# Hello\n\nWorld")

        assert "<h1>Hello</h1>" in content.html
        assert "<p>World</p>" in content.html
        assert content.filename == "test.md"

    def test_from_raw_parses_frontmatter(self):
        raw = '---\ntitle: My Post\ntimestamp: "2025-01-15"\ntags:\n  - python\n---\n\nBody'

        content = MarkdownContent.from_raw("post.md", raw)

        assert content.title == "My Post"
        assert content.timestamp == "2025-01-15"
        assert content.tags == ["python"]
        assert "<p>Body</p>" in content.html

    def test_from_raw_parses_author(self):
        raw = "---\nauthor: Jane\nauthor_email: jane@example.com\n---\n\nHi"

        content = MarkdownContent.from_raw("post.md", raw)

        assert content.author.name == "Jane"
        assert content.author.email == "jane@example.com"

    def test_from_raw_puts_unknown_fields_in_custom_fields(self):
        raw = "---\ntitle: Post\nslug: my-post\ndraft: true\n---\n\nContent"

        content = MarkdownContent.from_raw("post.md", raw)

        assert content.title == "Post"
        assert content.custom_fields.slug == "my-post"
        assert content.custom_fields.draft is True

    def test_from_raw_with_no_frontmatter(self):
        content = MarkdownContent.from_raw("post.md", "Just plain markdown")

        assert content.title == ""
        assert content.tags == []
        assert "<p>Just plain markdown</p>" in content.html


class TestMarkdownCollection:
    def test_empty_collection(self):
        collection = MarkdownCollection()

        assert len(collection) == 0

    def test_len(self):
        collection = MarkdownCollection()
        collection.add(MarkdownContent(filename="a.md", html="<p>a</p>"))

        assert len(collection) == 1

    def test_contains(self):
        collection = MarkdownCollection()
        collection.add(MarkdownContent(filename="a.md", html="<p>a</p>"))

        assert "a.md" in collection
        assert "b.md" not in collection

    def test_getitem(self):
        content = MarkdownContent(filename="a.md", html="<p>a</p>")
        collection = MarkdownCollection()
        collection.add(content)

        assert collection["a.md"] is content

    def test_iter_yields_content(self):
        content_a = MarkdownContent(filename="a.md", html="<p>a</p>")
        content_b = MarkdownContent(filename="b.md", html="<p>b</p>")
        collection = MarkdownCollection()
        collection.add(content_a)
        collection.add(content_b)

        assert list(collection) == [content_a, content_b]


class TestCustomRenderer:
    def test_from_raw_uses_custom_render_markdown(self):
        custom_render = lambda text: f"<custom>{text}</custom>"
        content = MarkdownContent.from_raw(
            "test.md", "Hello", render_markdown=custom_render
        )

        assert content.html == "<custom>Hello</custom>"

    def test_from_raw_defaults_to_mistune_html(self):
        content = MarkdownContent.from_raw("test.md", "**bold**")

        assert "<strong>bold</strong>" in content.html

    @patch(f"{TEST_PATH}.open", mock_open(read_data="# Hello"))
    @patch(f"{TEST_PATH}.os")
    def test_parser_passes_render_markdown_to_from_raw(self, mock_os):
        custom_render = lambda text: "<custom>rendered</custom>"
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(
            content_dir=Path("/fake/content"), render_markdown=custom_render
        )

        result = parser.parse()

        assert result["post.md"].html == "<custom>rendered</custom>"


class TestParse:
    @patch(f"{TEST_PATH}.os")
    def test_returns_empty_collection_when_no_markdown_files(self, mock_os):
        mock_os.listdir.return_value = ["image.png", "notes.txt"]
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert isinstance(result, MarkdownCollection)
        assert len(result) == 0

    @patch(f"{TEST_PATH}.open", mock_open(read_data="# Hello\n\nWorld"))
    @patch(f"{TEST_PATH}.os")
    def test_parses_single_markdown_file(self, mock_os):
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert "post.md" in result
        assert isinstance(result["post.md"], MarkdownContent)
        assert "<h1>Hello</h1>" in result["post.md"].html

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


class TestParseFrontmatter:
    @patch(f"{TEST_PATH}.os")
    def test_parses_frontmatter_fields(self, mock_os):
        md_content = """---
title: My Post
timestamp: "2025-01-15"
tags:
  - python
  - ssg
author: John Doe
author_email: john@example.com
author_avatar: https://example.com/avatar.png
author_url: https://example.com
---

# Hello World
"""
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        with patch(f"{TEST_PATH}.open", mock_open(read_data=md_content)):
            result = parser.parse()

        post = result["post.md"]
        assert post.title == "My Post"
        assert post.timestamp == "2025-01-15"
        assert post.tags == ["python", "ssg"]
        assert post.author.name == "John Doe"
        assert post.author.email == "john@example.com"
        assert post.author.avatar == "https://example.com/avatar.png"
        assert post.author.url == "https://example.com"
        assert "<h1>Hello World</h1>" in post.html

    @patch(f"{TEST_PATH}.os")
    def test_parses_custom_fields(self, mock_os):
        md_content = """---
title: My Post
slug: my-post
draft: true
---

Content here.
"""
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        with patch(f"{TEST_PATH}.open", mock_open(read_data=md_content)):
            result = parser.parse()

        post = result["post.md"]
        assert post.title == "My Post"
        assert post.custom_fields.slug == "my-post"
        assert post.custom_fields.draft is True

    @patch(f"{TEST_PATH}.open", mock_open(read_data="Just plain markdown"))
    @patch(f"{TEST_PATH}.os")
    def test_no_frontmatter_returns_defaults(self, mock_os):
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        post = result["post.md"]
        assert post.title == ""
        assert post.timestamp == ""
        assert post.tags == []
        assert "<p>Just plain markdown</p>" in post.html


class TestTocGenerator:
    def test_extracts_headings_from_markdown(self):
        md = "# Title\n\n## Section 1\n\n## Section 2\n"
        gen = TocGenerator(max_depth=3)

        toc = gen.generate(md)

        assert '<nav class="toc">' in toc
        assert "Title" in toc
        assert "Section 1" in toc
        assert "Section 2" in toc

    def test_generates_nested_list(self):
        md = "# Title\n\n## Sub\n\n### Deep\n"
        gen = TocGenerator(max_depth=3)

        toc = gen.generate(md)

        assert "<ul>" in toc
        assert "<li>" in toc
        assert "Title" in toc
        assert "Sub" in toc
        assert "Deep" in toc

    def test_respects_max_depth(self):
        md = "# H1\n\n## H2\n\n### H3\n\n#### H4\n"
        gen = TocGenerator(max_depth=2)

        toc = gen.generate(md)

        assert "H1" in toc
        assert "H2" in toc
        assert "H3" not in toc
        assert "H4" not in toc

    def test_returns_empty_string_when_no_headings(self):
        md = "Just a paragraph.\n"
        gen = TocGenerator(max_depth=3)

        toc = gen.generate(md)

        assert toc == ""

    def test_generates_anchor_links(self):
        md = "## My Section\n"
        gen = TocGenerator(max_depth=3)

        toc = gen.generate(md)

        assert 'href="#my-section"' in toc

    def test_anchor_handles_special_characters(self):
        md = "## Hello, World! (Test)\n"
        gen = TocGenerator(max_depth=3)

        toc = gen.generate(md)

        assert 'href="#hello-world-test"' in toc

    def test_default_max_depth_is_three(self):
        gen = TocGenerator()

        assert gen.max_depth == 3


class TestMarkdownContentToc:
    def test_toc_field_defaults_to_empty_string(self):
        content = MarkdownContent(filename="test.md", html="<p>Hi</p>")

        assert content.toc == ""

    def test_from_raw_generates_toc_when_generator_provided(self):
        raw = "---\ntitle: Post\n---\n\n## Intro\n\n## Body\n"
        gen = TocGenerator(max_depth=3)

        content = MarkdownContent.from_raw("post.md", raw, toc_generator=gen)

        assert "Intro" in content.toc
        assert "Body" in content.toc

    def test_from_raw_no_toc_without_generator(self):
        raw = "## Heading\n\nParagraph\n"

        content = MarkdownContent.from_raw("post.md", raw)

        assert content.toc == ""


class TestMarkdownParserToc:
    @patch(f"{TEST_PATH}.open", mock_open(read_data="## Hello\n\nWorld"))
    @patch(f"{TEST_PATH}.os")
    def test_parser_passes_toc_generator(self, mock_os):
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        gen = TocGenerator(max_depth=3)
        parser = MarkdownParser(content_dir=Path("/fake/content"), toc_generator=gen)

        result = parser.parse()

        assert "Hello" in result["post.md"].toc

    @patch(f"{TEST_PATH}.open", mock_open(read_data="## Hello\n\nWorld"))
    @patch(f"{TEST_PATH}.os")
    def test_parser_no_toc_by_default(self, mock_os):
        mock_os.listdir.return_value = ["post.md"]
        mock_os.path.join.return_value = "/fake/content/post.md"
        parser = MarkdownParser(content_dir=Path("/fake/content"))

        result = parser.parse()

        assert result["post.md"].toc == ""
