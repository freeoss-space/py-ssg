import hashlib
import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import mock_open, patch

from pyssg.modules.cache import BuildCache, CachedContentEntry

TEST_PATH = "pyssg.modules.cache"


class TestHasDynamicConstructs:
    def test_detects_for_loop(self):
        template = "{% for item in items %}<p>{{ item }}</p>{% endfor %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_detects_if_conditional(self):
        template = "{% if show %}<p>Visible</p>{% endif %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_detects_macro(self):
        template = "{% macro greeting(name) %}Hello {{ name }}{% endmacro %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_detects_call_block(self):
        template = "{% call box() %}content{% endcall %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_static_template_returns_false(self):
        template = "<h1>Hello World</h1>"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is False

    def test_template_with_only_variables_returns_false(self):
        template = "<h1>{{ title }}</h1><p>{{ body }}</p>"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is False

    def test_detects_nested_for_inside_if(self):
        template = "{% if items %}{% for i in items %}{{ i }}{% endfor %}{% endif %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_detects_elif(self):
        template = "{% if a %}A{% elif b %}B{% endif %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_detects_else(self):
        template = "{% if a %}A{% else %}B{% endif %}"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is True

    def test_plain_html_returns_false(self):
        template = "<html><body><p>Static page</p></body></html>"
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.has_dynamic_constructs(template) is False


class TestComputeHash:
    def test_returns_sha256_hex_digest(self):
        content = "<h1>Hello</h1>"
        cache = BuildCache(cache_dir=Path("/project"))
        expected = hashlib.sha256(content.encode()).hexdigest()

        assert cache.compute_hash(content) == expected

    def test_different_content_produces_different_hash(self):
        cache = BuildCache(cache_dir=Path("/project"))
        hash1 = cache.compute_hash("<h1>Hello</h1>")
        hash2 = cache.compute_hash("<h1>World</h1>")

        assert hash1 != hash2

    def test_same_content_produces_same_hash(self):
        cache = BuildCache(cache_dir=Path("/project"))
        hash1 = cache.compute_hash("<h1>Hello</h1>")
        hash2 = cache.compute_hash("<h1>Hello</h1>")

        assert hash1 == hash2

    def test_content_hash_distinguishes_ambiguous_raw_and_config_pairs(self):
        cache = BuildCache(cache_dir=Path("/project"))

        hash1 = cache._compute_content_hash("ab", "c")
        hash2 = cache._compute_content_hash("a", "bc")

        assert hash1 != hash2


class TestNeedsRebuild:
    def test_returns_true_for_new_file(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.needs_rebuild("index.html", "<h1>Hello</h1>") is True

    def test_returns_false_for_unchanged_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        content = "<h1>Hello</h1>"
        cache.update("index.html", content)

        assert cache.needs_rebuild("index.html", content) is False

    def test_returns_true_for_changed_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache.update("index.html", "<h1>Hello</h1>")

        assert cache.needs_rebuild("index.html", "<h1>Changed</h1>") is True


class TestUpdate:
    def test_stores_hash_for_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        content = "<h1>Hello</h1>"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()

        cache.update("index.html", content)

        assert cache._entries["index.html"] == expected_hash

    def test_overwrites_existing_entry(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache.update("index.html", "<h1>Old</h1>")
        cache.update("index.html", "<h1>New</h1>")
        expected_hash = hashlib.sha256("<h1>New</h1>".encode()).hexdigest()

        assert cache._entries["index.html"] == expected_hash


class TestCreate:
    def test_creates_empty_cache_file(self):
        m = mock_open()
        with patch(f"{TEST_PATH}.open", m):
            BuildCache.create(cache_dir=Path("/project"))

        m.assert_called_once_with(Path("/project/.pyssg_cache.json"), "w")
        written = m().write.call_args[0][0]
        assert json.loads(written) == {"templates": {}, "content": {}}


class TestCacheFileHelpers:
    def test_cache_path_uses_project_cache_filename(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache._cache_path() == Path("/project/.pyssg_cache.json")

    def test_ensure_cache_file_returns_existing_path_without_creating(self):
        cache = BuildCache(cache_dir=Path("/project"))

        with (
            patch(f"{TEST_PATH}.Path.exists", return_value=True),
            patch.object(BuildCache, "create") as mock_create,
        ):
            cache_path = cache._ensure_cache_file()

        assert cache_path == Path("/project/.pyssg_cache.json")
        mock_create.assert_not_called()

    def test_ensure_cache_file_creates_missing_file(self):
        cache = BuildCache(cache_dir=Path("/project"))

        with (
            patch(f"{TEST_PATH}.Path.exists", return_value=False),
            patch.object(BuildCache, "create") as mock_create,
        ):
            cache_path = cache._ensure_cache_file()

        assert cache_path == Path("/project/.pyssg_cache.json")
        mock_create.assert_called_once_with(cache_dir=Path("/project"))

    def test_read_cache_data_reads_json_from_cache_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache_data = {"templates": {"index.html": "abc"}, "content": {}}

        with (
            patch.object(
                BuildCache,
                "_ensure_cache_file",
                return_value=Path("/project/.pyssg_cache.json"),
            ),
            patch(f"{TEST_PATH}.open", mock_open(read_data=json.dumps(cache_data))),
        ):
            result = cache._read_cache_data()

        assert result == cache_data


class TestSave:
    def test_writes_cache_to_json_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache.update("index.html", "<h1>Hello</h1>")

        m = mock_open()
        with patch(f"{TEST_PATH}.open", m):
            cache.save()

        m.assert_called_once_with(Path("/project/.pyssg_cache.json"), "w")
        written = m().write.call_args[0][0]
        data = json.loads(written)
        assert "index.html" in data["templates"]

    def test_writes_content_cache_to_json_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache.set_content(
            "post.md",
            "# Hello",
            '{"syntax":{},"toc":{}}',
            {
                "filename": "post.md",
                "html": "<h1>Hello</h1>",
                "title": "",
                "timestamp": "",
                "tags": [],
                "author": {"name": "", "email": "", "avatar": "", "url": ""},
                "custom_fields": {},
                "toc": "",
            },
        )

        m = mock_open()
        with patch(f"{TEST_PATH}.open", m):
            cache.save()

        written = m().write.call_args[0][0]
        data = json.loads(written)
        assert data["content"]["post.md"]["data"]["html"] == "<h1>Hello</h1>"


class TestLoad:
    def test_reset_entries_clears_template_and_content_entries(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache._entries["index.html"] = "abc"
        cache._content_entries["post.md"] = CachedContentEntry(
            hash_value="abc123",
            data={"html": "<p>Body</p>"},
        )

        cache._reset_entries()

        assert cache._entries == {}
        assert cache._content_entries == {}

    def test_is_structured_cache_data_detects_templates_key(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache._is_structured_cache_data({"templates": {}}) is True

    def test_is_structured_cache_data_detects_content_key(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache._is_structured_cache_data({"content": {}}) is True

    def test_is_structured_cache_data_returns_false_for_legacy_shape(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache._is_structured_cache_data({"index.html": "abc123"}) is False

    def test_load_template_entries_ignores_invalid_items(self):
        cache = BuildCache(cache_dir=Path("/project"))

        cache._load_template_entries(
            cast(dict[str, Any], {"index.html": "abc123", "about.html": 1, 2: "skip"})
        )

        assert cache._entries == {"index.html": "abc123"}

    def test_load_content_entries_ignores_invalid_items(self):
        cache = BuildCache(cache_dir=Path("/project"))

        cache._load_content_entries(
            cast(
                dict[str, Any],
                {
                    "post.md": {"hash": "abc123", "data": {"html": "<p>Body</p>"}},
                    "bad.md": {"hash": 1, "data": {}},
                    "skip.md": "invalid",
                    2: {"hash": "def456", "data": {}},
                },
            )
        )

        assert list(cache._content_entries) == ["post.md"]
        assert cache._content_entries["post.md"].hash_value == "abc123"

    def test_load_entries_resets_existing_state_before_loading_structured_data(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache._entries["stale.html"] = "stale"
        cache._content_entries["stale.md"] = CachedContentEntry(
            hash_value="stale",
            data={"html": "<p>Stale</p>"},
        )

        cache._load_entries({"templates": {"index.html": "abc123"}, "content": {}})

        assert cache._entries == {"index.html": "abc123"}
        assert cache._content_entries == {}

    def test_load_entries_resets_existing_state_before_loading_legacy_data(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache._entries["stale.html"] = "stale"
        cache._content_entries["stale.md"] = CachedContentEntry(
            hash_value="stale",
            data={"html": "<p>Stale</p>"},
        )

        cache._load_entries({"index.html": "abc123"})

        assert cache._entries == {"index.html": "abc123"}
        assert cache._content_entries == {}

    def test_load_entries_ignores_non_dict_data(self):
        cache = BuildCache(cache_dir=Path("/project"))
        cache._entries["stale.html"] = "stale"
        cache._content_entries["stale.md"] = CachedContentEntry(
            hash_value="stale",
            data={"html": "<p>Stale</p>"},
        )

        cache._load_entries(["not", "a", "dict"])

        assert cache._entries == {}
        assert cache._content_entries == {}

    def test_loads_template_cache_from_structured_json_file(self):
        expected_hash = hashlib.sha256("<h1>Hello</h1>".encode()).hexdigest()
        cache_data = json.dumps(
            {"templates": {"index.html": expected_hash}, "content": {}}
        )
        cache = BuildCache(cache_dir=Path("/project"))

        with patch(f"{TEST_PATH}.open", mock_open(read_data=cache_data)):
            cache.load()

        assert cache._entries["index.html"] == expected_hash

    def test_loads_content_cache_from_structured_json_file(self):
        cache_data = json.dumps(
            {
                "templates": {},
                "content": {
                    "post.md": {
                        "hash": "abc123",
                        "data": {
                            "filename": "post.md",
                            "html": "<p>Body</p>",
                            "title": "Post",
                            "timestamp": "",
                            "tags": ["python"],
                            "author": {
                                "name": "Jane",
                                "email": "",
                                "avatar": "",
                                "url": "",
                            },
                            "custom_fields": {"draft": True},
                            "toc": "",
                        },
                    }
                },
            }
        )
        cache = BuildCache(cache_dir=Path("/project"))

        with patch(f"{TEST_PATH}.open", mock_open(read_data=cache_data)):
            cache.load()

        assert cache._content_entries["post.md"].hash_value == "abc123"
        assert cache._content_entries["post.md"].data["title"] == "Post"

    def test_loads_legacy_template_cache_json_file(self):
        expected_hash = hashlib.sha256("<h1>Hello</h1>".encode()).hexdigest()
        cache_data = json.dumps({"index.html": expected_hash})
        cache = BuildCache(cache_dir=Path("/project"))

        with patch(f"{TEST_PATH}.open", mock_open(read_data=cache_data)):
            cache.load()

        assert cache._entries["index.html"] == expected_hash

    def test_creates_cache_file_when_missing(self):
        cache = BuildCache(cache_dir=Path("/project"))

        with (
            patch(f"{TEST_PATH}.Path.exists", return_value=False),
            patch.object(BuildCache, "create") as mock_create,
            patch(f"{TEST_PATH}.open", mock_open(read_data="{}")),
        ):
            cache.load()

        mock_create.assert_called_once_with(cache_dir=Path("/project"))
        assert cache._entries == {}


class TestContentCache:
    def test_get_content_returns_none_for_new_file(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.get_content("post.md", "# Hello", '{"syntax":{},"toc":{}}') is None

    def test_get_content_returns_data_for_unchanged_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        data = {
            "filename": "post.md",
            "html": "<p>Hello</p>",
            "title": "",
            "timestamp": "",
            "tags": [],
            "author": {"name": "", "email": "", "avatar": "", "url": ""},
            "custom_fields": {},
            "toc": "",
        }

        cache.set_content("post.md", "# Hello", '{"syntax":{},"toc":{}}', data)

        assert cache.get_content("post.md", "# Hello", '{"syntax":{},"toc":{}}') == data

    def test_get_content_returns_none_for_changed_file(self):
        cache = BuildCache(cache_dir=Path("/project"))
        data = {
            "filename": "post.md",
            "html": "<p>Hello</p>",
            "title": "",
            "timestamp": "",
            "tags": [],
            "author": {"name": "", "email": "", "avatar": "", "url": ""},
            "custom_fields": {},
            "toc": "",
        }

        cache.set_content("post.md", "# Hello", '{"syntax":{},"toc":{}}', data)

        assert (
            cache.get_content("post.md", "# Changed", '{"syntax":{},"toc":{}}') is None
        )

    def test_get_content_rejects_ambiguous_concat_pair_with_different_inputs(self):
        cache = BuildCache(cache_dir=Path("/project"))
        data = {
            "filename": "post.md",
            "html": "<p>Hello</p>",
            "title": "",
            "timestamp": "",
            "tags": [],
            "author": {"name": "", "email": "", "avatar": "", "url": ""},
            "custom_fields": {},
            "toc": "",
        }

        cache.set_content("post.md", "ab", "c", data)

        assert cache.get_content("post.md", "a", "bc") is None


class TestEnabled:
    def test_needs_rebuild_always_true_when_disabled(self):
        cache = BuildCache(cache_dir=Path("/project"), enabled=False)
        cache._entries["index.html"] = cache.compute_hash("<h1>Hello</h1>")

        assert cache.needs_rebuild("index.html", "<h1>Hello</h1>") is True

    def test_update_is_noop_when_disabled(self):
        cache = BuildCache(cache_dir=Path("/project"), enabled=False)

        cache.update("index.html", "<h1>Hello</h1>")

        assert cache._entries == {}

    def test_save_is_noop_when_disabled(self):
        cache = BuildCache(cache_dir=Path("/project"), enabled=False)

        m = mock_open()
        with patch(f"{TEST_PATH}.open", m):
            cache.save()

        m.assert_not_called()

    def test_load_is_noop_when_disabled(self):
        cache = BuildCache(cache_dir=Path("/project"), enabled=False)

        m = mock_open()
        with patch(f"{TEST_PATH}.open", m):
            cache.load()

        m.assert_not_called()
        assert cache._entries == {}

    def test_enabled_by_default(self):
        cache = BuildCache(cache_dir=Path("/project"))

        assert cache.enabled is True
