import hashlib
import json
from pathlib import Path
from unittest.mock import mock_open, patch

from pyssg.modules.cache import BuildCache

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
        assert json.loads(written) == {}


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
        assert "index.html" in data


class TestLoad:
    def test_loads_cache_from_json_file(self):
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
