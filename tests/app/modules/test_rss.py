from pyssg.modules.markdown import ContentAuthor, MarkdownCollection, MarkdownContent
from pyssg.modules.rss import FeedConfig, RssFeedGenerator


def _make_content(
    filename="post.md",
    title="Test Post",
    timestamp="2025-01-15T12:00:00",
    tags=None,
    html="<p>Hello</p>",
    author_name="",
    author_email="",
):
    return MarkdownContent(
        filename=filename,
        html=html,
        title=title,
        timestamp=timestamp,
        tags=tags or [],
        author=ContentAuthor(name=author_name, email=author_email),
    )


def _make_collection(*items):
    col = MarkdownCollection()
    for item in items:
        col.add(item)
    return col


class TestFeedConfig:
    def test_from_dict_minimal(self):
        cfg = FeedConfig.from_dict({"title": "My Feed", "output": "feed.xml"})
        assert cfg.title == "My Feed"
        assert cfg.output == "feed.xml"
        assert cfg.tags is None

    def test_from_dict_with_tags(self):
        cfg = FeedConfig.from_dict(
            {"title": "Tech", "output": "tech.xml", "tags": ["tech", "code"]}
        )
        assert cfg.tags == ["tech", "code"]

    def test_from_dict_defaults(self):
        cfg = FeedConfig.from_dict({})
        assert cfg.title == ""
        assert cfg.output == "feed.xml"
        assert cfg.description == ""


class TestRssFeedGenerator:
    def test_generate_single_feed(self):
        feed = FeedConfig(title="Blog", output="feed.xml", description="A blog")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(_make_content())

        results = gen.generate(col)

        assert len(results) == 1
        filename, xml = results[0]
        assert filename == "feed.xml"
        assert '<?xml version="1.0"' in xml
        assert "<title>Blog</title>" in xml
        assert "<title>Test Post</title>" in xml
        assert "<link>https://example.com/post</link>" in xml

    def test_generate_multiple_feeds(self):
        feeds = [
            FeedConfig(title="All", output="all.xml"),
            FeedConfig(title="Tech", output="tech.xml", tags=["tech"]),
        ]
        gen = RssFeedGenerator(site_url="https://example.com", feeds=feeds)
        col = _make_collection(
            _make_content(filename="a.md", tags=["tech"]),
            _make_content(filename="b.md", tags=["life"]),
        )

        results = gen.generate(col)

        assert len(results) == 2
        all_xml = results[0][1]
        tech_xml = results[1][1]
        assert "a</link>" in all_xml
        assert "b</link>" in all_xml
        assert "a</link>" in tech_xml
        assert "b</link>" not in tech_xml

    def test_tag_filtering(self):
        feed = FeedConfig(title="Tech", output="tech.xml", tags=["tech"])
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(
            _make_content(filename="a.md", tags=["tech", "code"]),
            _make_content(filename="b.md", tags=["life"]),
            _make_content(filename="c.md", tags=["tech"]),
        )

        results = gen.generate(col)
        xml = results[0][1]

        assert "https://example.com/a</link>" in xml
        assert "https://example.com/c</link>" in xml
        assert "https://example.com/b</link>" not in xml

    def test_items_sorted_by_timestamp_descending(self):
        feed = FeedConfig(title="Blog", output="feed.xml")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(
            _make_content(filename="old.md", timestamp="2024-01-01T00:00:00"),
            _make_content(filename="new.md", timestamp="2025-06-01T00:00:00"),
            _make_content(filename="mid.md", timestamp="2024-06-01T00:00:00"),
        )

        results = gen.generate(col)
        xml = results[0][1]

        new_pos = xml.index("example.com/new")
        mid_pos = xml.index("example.com/mid")
        old_pos = xml.index("example.com/old")
        assert new_pos < mid_pos < old_pos

    def test_author_with_email(self):
        feed = FeedConfig(title="Blog", output="feed.xml")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(
            _make_content(author_name="Alice", author_email="alice@example.com")
        )

        results = gen.generate(col)
        xml = results[0][1]
        assert "alice@example.com (Alice)" in xml

    def test_author_without_email(self):
        feed = FeedConfig(title="Blog", output="feed.xml")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(_make_content(author_name="Alice"))

        results = gen.generate(col)
        xml = results[0][1]
        assert "<author>Alice</author>" in xml

    def test_pubdate_included(self):
        feed = FeedConfig(title="Blog", output="feed.xml")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection(_make_content(timestamp="2025-01-15T12:00:00"))

        results = gen.generate(col)
        xml = results[0][1]
        assert "<pubDate>" in xml

    def test_empty_collection(self):
        feed = FeedConfig(title="Blog", output="feed.xml", description="Empty")
        gen = RssFeedGenerator(site_url="https://example.com", feeds=[feed])
        col = _make_collection()

        results = gen.generate(col)
        xml = results[0][1]
        assert "<title>Blog</title>" in xml
        assert "<item>" not in xml

    def test_trailing_slash_stripped_from_url(self):
        feed = FeedConfig(title="Blog", output="feed.xml")
        gen = RssFeedGenerator(site_url="https://example.com/", feeds=[feed])
        col = _make_collection(_make_content())

        results = gen.generate(col)
        xml = results[0][1]
        assert "https://example.com/post</link>" in xml
        assert "example.com//post" not in xml
