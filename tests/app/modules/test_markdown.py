import json
from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pyssg.modules.cache import BuildCache
from pyssg.modules.markdown import (
    ContentAuthor,
    MarkdownCollection,
    MarkdownContent,
    MarkdownParser,
    ParallelParseConfig,
    PendingParseItem,
    TocGenerator,
)


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

    def test_to_dict_round_trips_with_from_dict(self):
        author = ContentAuthor(
            name="Jane",
            email="jane@example.com",
            avatar="avatar.png",
            url="https://example.com",
        )

        assert ContentAuthor.from_dict(author.to_dict()) == author


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

    def test_to_dict_round_trips_with_from_dict(self):
        content = MarkdownContent(
            filename="post.md",
            html="<p>Hello</p>",
            title="Post",
            timestamp="2025-01-15",
            tags=["python"],
            author=ContentAuthor(name="Jane", email="jane@example.com"),
            custom_fields=SimpleNamespace(slug="post", draft=True),
            toc="<nav>...</nav>",
        )

        restored = MarkdownContent.from_dict(content.to_dict())

        assert restored == content

    def test_to_dict_normalizes_non_json_custom_fields(self):
        content = MarkdownContent(
            filename="post.md",
            html="<p>Hello</p>",
            custom_fields=SimpleNamespace(
                published_on=date(2025, 1, 15),
                updated_at=datetime(2025, 1, 15, 12, 30, 45),
                metadata={
                    "reviewed_on": date(2025, 1, 16),
                    "history": [datetime(2025, 1, 17, 8, 0, 0)],
                },
            ),
        )

        data = content.to_dict()

        assert data["custom_fields"] == {
            "published_on": "2025-01-15",
            "updated_at": "2025-01-15 12:30:45",
            "metadata": {
                "reviewed_on": "2025-01-16",
                "history": ["2025-01-17 08:00:00"],
            },
        }
        json.dumps(data)


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

    def test_parser_passes_render_markdown_to_from_raw(self, tmp_path):
        custom_render = lambda text: "<custom>rendered</custom>"
        (tmp_path / "post.md").write_text("# Hello")
        parser = MarkdownParser(content_dir=tmp_path, render_markdown=custom_render)

        result = parser.parse()

        assert result["post.md"].html == "<custom>rendered</custom>"


class TestParse:
    def test_returns_empty_collection_when_no_markdown_files(self, tmp_path):
        (tmp_path / "image.png").write_text("png")
        (tmp_path / "notes.txt").write_text("notes")
        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        assert isinstance(result, MarkdownCollection)
        assert len(result) == 0

    def test_parses_single_markdown_file(self, tmp_path):
        (tmp_path / "post.md").write_text("# Hello\n\nWorld")
        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        assert "post.md" in result
        assert isinstance(result["post.md"], MarkdownContent)
        assert "<h1>Hello</h1>" in result["post.md"].html

    def test_parses_multiple_markdown_files(self, tmp_path):
        (tmp_path / "a.md").write_text("**bold**")
        (tmp_path / "b.md").write_text("**bold**")
        (tmp_path / "skip.txt").write_text("skip")
        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        assert len(result) == 2
        assert "a.md" in result
        assert "b.md" in result
        assert "skip.txt" not in result

    def test_parses_markdown_files_recursively_with_relative_filenames(self, tmp_path):
        (tmp_path / "blog" / "2025").mkdir(parents=True)
        (tmp_path / "docs").mkdir()
        (tmp_path / "blog" / "2025" / "post.md").write_text("# Blog")
        (tmp_path / "docs" / "api.md").write_text("# API")

        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        assert len(result) == 2
        assert "blog/2025/post.md" in result
        assert "docs/api.md" in result
        assert result["blog/2025/post.md"].filename == "blog/2025/post.md"
        assert result["docs/api.md"].filename == "docs/api.md"

    @patch("pyssg.modules.markdown.MarkdownContent.from_raw")
    def test_uses_cached_content_in_sequential_mode(
        self, mock_from_raw: MagicMock, tmp_path
    ):
        raw = "# Hello\n\nWorld"
        (tmp_path / "post.md").write_text(raw)
        cache = BuildCache(cache_dir=tmp_path)
        cached_content = MarkdownContent(
            filename="post.md",
            html="<p>cached</p>",
            title="Cached",
        )
        config_key = json.dumps(
            {"syntax": {}, "toc": {}}, sort_keys=True, separators=(",", ":")
        )
        cache.set_content("post.md", raw, config_key, cached_content.to_dict())
        parser = MarkdownParser(content_dir=tmp_path, cache=cache)

        result = parser.parse()

        mock_from_raw.assert_not_called()
        assert result["post.md"] == cached_content

    @patch("pyssg.modules.markdown.ProcessPoolExecutor")
    def test_parallel_mode_only_dispatches_uncached_files(
        self, mock_executor_cls: MagicMock, tmp_path
    ):
        raw_a = "# Cached"
        raw_b = "# Fresh"
        (tmp_path / "a.md").write_text(raw_a)
        (tmp_path / "b.md").write_text(raw_b)
        cache = BuildCache(cache_dir=tmp_path)
        cached_content = MarkdownContent(filename="a.md", html="<p>cached</p>")
        config_key = json.dumps(
            {
                "syntax": {"enabled": False},
                "toc": {"enabled": False},
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        cache.set_content("a.md", raw_a, config_key, cached_content.to_dict())
        fresh_content = MarkdownContent(filename="b.md", html="<p>fresh</p>")
        mock_executor = mock_executor_cls.return_value.__enter__.return_value
        mock_executor.map.return_value = [fresh_content]
        parser = MarkdownParser(content_dir=tmp_path, cache=cache)

        result = parser.parse(
            workers=2,
            syntax_config={"enabled": False},
            toc_config={"enabled": False},
        )

        mock_executor.map.assert_called_once_with(
            mock_executor.map.call_args.args[0],
            [("b.md", raw_b)],
            chunksize=64,
        )
        assert list(result) == [cached_content, fresh_content]
        assert cache.get_content("b.md", raw_b, config_key) == fresh_content.to_dict()


class TestParallelHelpers:
    def test_build_parallel_config_uses_defaults(self, tmp_path):
        parser = MarkdownParser(content_dir=tmp_path)

        config = parser._build_parallel_config(None, None)

        assert config == ParallelParseConfig(
            syntax_enabled=False,
            theme_light="friendly",
            theme_dark="monokai",
            toc_enabled=False,
            toc_max_depth=3,
        )

    def test_build_parallel_config_uses_provided_values(self, tmp_path):
        parser = MarkdownParser(content_dir=tmp_path)

        config = parser._build_parallel_config(
            {"enabled": True, "theme_light": "tango", "theme_dark": "dracula"},
            {"enabled": True, "max_depth": 5},
        )

        assert config == ParallelParseConfig(
            syntax_enabled=True,
            theme_light="tango",
            theme_dark="dracula",
            toc_enabled=True,
            toc_max_depth=5,
        )

    def test_partition_cached_items_splits_cached_and_pending(self, tmp_path):
        raw_a = "# Cached"
        raw_b = "# Fresh"
        cache = BuildCache(cache_dir=tmp_path)
        parser = MarkdownParser(content_dir=tmp_path, cache=cache)
        config_key = json.dumps(
            {"syntax": {}, "toc": {}}, sort_keys=True, separators=(",", ":")
        )
        cached_content = MarkdownContent(filename="a.md", html="<p>cached</p>")
        cache.set_content("a.md", raw_a, config_key, cached_content.to_dict())

        results, pending_items = parser._partition_cached_items(
            [("a.md", raw_a), ("b.md", raw_b)],
            config_key,
        )

        assert results == {0: cached_content}
        assert pending_items == [PendingParseItem(index=1, filename="b.md", raw=raw_b)]

    def test_worker_items_extract_filename_and_raw(self, tmp_path):
        parser = MarkdownParser(content_dir=tmp_path)
        pending_items = [
            PendingParseItem(index=1, filename="b.md", raw="# Fresh"),
            PendingParseItem(index=2, filename="c.md", raw="# New"),
        ]

        assert parser._worker_items(pending_items) == [
            ("b.md", "# Fresh"),
            ("c.md", "# New"),
        ]

    def test_store_parsed_results_preserves_index_and_updates_cache(self, tmp_path):
        cache = BuildCache(cache_dir=tmp_path)
        parser = MarkdownParser(content_dir=tmp_path, cache=cache)
        config_key = json.dumps(
            {"syntax": {}, "toc": {}}, sort_keys=True, separators=(",", ":")
        )
        results: dict[int, MarkdownContent] = {}
        pending_items = [PendingParseItem(index=1, filename="b.md", raw="# Fresh")]
        parsed_contents = iter([MarkdownContent(filename="b.md", html="<p>fresh</p>")])

        parser._store_parsed_results(
            results,
            pending_items,
            parsed_contents,
            config_key,
        )

        assert results == {1: MarkdownContent(filename="b.md", html="<p>fresh</p>")}
        assert (
            cache.get_content("b.md", "# Fresh", config_key)
            == MarkdownContent(filename="b.md", html="<p>fresh</p>").to_dict()
        )

    def test_build_collection_from_results_restores_original_order(self, tmp_path):
        parser = MarkdownParser(content_dir=tmp_path)
        results = {
            0: MarkdownContent(filename="a.md", html="<p>a</p>"),
            1: MarkdownContent(filename="b.md", html="<p>b</p>"),
        }

        collection = parser._build_collection_from_results(2, results)

        assert list(collection) == [results[0], results[1]]


class TestParseFrontmatter:
    def test_parses_frontmatter_fields(self, tmp_path):
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
        (tmp_path / "post.md").write_text(md_content)
        parser = MarkdownParser(content_dir=tmp_path)

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

    def test_parses_custom_fields(self, tmp_path):
        md_content = """---
title: My Post
slug: my-post
draft: true
---

Content here.
"""
        (tmp_path / "post.md").write_text(md_content)
        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        post = result["post.md"]
        assert post.title == "My Post"
        assert post.custom_fields.slug == "my-post"
        assert post.custom_fields.draft is True

    def test_no_frontmatter_returns_defaults(self, tmp_path):
        (tmp_path / "post.md").write_text("Just plain markdown")
        parser = MarkdownParser(content_dir=tmp_path)

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
    def test_parser_passes_toc_generator(self, tmp_path):
        (tmp_path / "post.md").write_text("## Hello\n\nWorld")
        gen = TocGenerator(max_depth=3)
        parser = MarkdownParser(content_dir=tmp_path, toc_generator=gen)

        result = parser.parse()

        assert "Hello" in result["post.md"].toc

    def test_parser_no_toc_by_default(self, tmp_path):
        (tmp_path / "post.md").write_text("## Hello\n\nWorld")
        parser = MarkdownParser(content_dir=tmp_path)

        result = parser.parse()

        assert result["post.md"].toc == ""
