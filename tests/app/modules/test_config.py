from pathlib import Path
from unittest.mock import mock_open, patch

from pyssg.modules.config import AuthorConfig, FeedConfig, SiteConfig

TEST_PATH = "pyssg.modules.config"


class TestAuthorConfig:
    def test_default_values(self):
        author = AuthorConfig()

        assert author.name == ""
        assert author.email == ""

    def test_from_dict(self):
        author = AuthorConfig.from_dict({"name": "Jane", "email": "jane@example.com"})

        assert author.name == "Jane"
        assert author.email == "jane@example.com"

    def test_from_dict_defaults(self):
        author = AuthorConfig.from_dict({})

        assert author.name == ""
        assert author.email == ""


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


class TestSiteConfig:
    def test_default_values(self):
        config = SiteConfig()

        assert config.name == ""
        assert config.url == ""
        assert config.description == ""
        assert config.authors == []
        assert config.feeds == []
        assert config.cache is True

    def test_from_dict_full(self):
        data = {
            "name": "My Blog",
            "url": "https://example.com",
            "description": "A blog",
            "cache": False,
            "authors": [{"name": "Jane", "email": "jane@example.com"}],
            "feeds": [{"title": "Feed", "output": "feed.xml"}],
        }

        config = SiteConfig.from_dict(data)

        assert config.name == "My Blog"
        assert config.url == "https://example.com"
        assert config.description == "A blog"
        assert config.cache is False
        assert len(config.authors) == 1
        assert config.authors[0].name == "Jane"
        assert config.authors[0].email == "jane@example.com"
        assert len(config.feeds) == 1
        assert config.feeds[0].title == "Feed"

    def test_from_dict_defaults(self):
        config = SiteConfig.from_dict({})

        assert config.name == ""
        assert config.url == ""
        assert config.description == ""
        assert config.authors == []
        assert config.feeds == []
        assert config.cache is True

    def test_from_dict_cache_defaults_to_true(self):
        config = SiteConfig.from_dict({"name": "Blog"})

        assert config.cache is True

    def test_from_dict_cache_can_be_disabled(self):
        config = SiteConfig.from_dict({"cache": False})

        assert config.cache is False

    def test_from_dict_multiple_authors(self):
        data = {
            "authors": [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        }

        config = SiteConfig.from_dict(data)

        assert len(config.authors) == 2
        assert config.authors[0].name == "Alice"
        assert config.authors[1].name == "Bob"

    def test_from_dict_multiple_feeds(self):
        data = {
            "feeds": [
                {"title": "All", "output": "all.xml"},
                {"title": "Tech", "output": "tech.xml", "tags": ["tech"]},
            ]
        }

        config = SiteConfig.from_dict(data)

        assert len(config.feeds) == 2
        assert config.feeds[0].title == "All"
        assert config.feeds[1].tags == ["tech"]


class TestSiteConfigLoad:
    def test_loads_from_toml_file(self):
        toml_content = b"""
[py-ssg]
name = "My Blog"
url = "https://example.com"
description = "A blog"
cache = true

[[py-ssg.authors]]
name = "Jane"
email = "jane@example.com"

[[py-ssg.feeds]]
title = "Feed"
output = "feed.xml"
"""
        with (
            patch(f"{TEST_PATH}.Path.exists", return_value=True),
            patch(f"{TEST_PATH}.open", mock_open(read_data=toml_content)),
        ):
            config = SiteConfig.load(Path("/project"))

        assert config.name == "My Blog"
        assert config.url == "https://example.com"
        assert config.description == "A blog"
        assert config.cache is True
        assert len(config.authors) == 1
        assert config.authors[0].name == "Jane"
        assert len(config.feeds) == 1
        assert config.feeds[0].title == "Feed"

    def test_returns_defaults_when_file_missing(self):
        with patch(f"{TEST_PATH}.Path.exists", return_value=False):
            config = SiteConfig.load(Path("/project"))

        assert config == SiteConfig()

    def test_loads_cache_disabled(self):
        toml_content = b"""
[py-ssg]
name = "Blog"
cache = false
"""
        with (
            patch(f"{TEST_PATH}.Path.exists", return_value=True),
            patch(f"{TEST_PATH}.open", mock_open(read_data=toml_content)),
        ):
            config = SiteConfig.load(Path("/project"))

        assert config.cache is False
