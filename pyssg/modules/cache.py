import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, nodes

_jinja_env = Environment()

DYNAMIC_NODE_TYPES = (nodes.For, nodes.If, nodes.Macro, nodes.CallBlock)


type CachePayload = dict[str, object]


@dataclass
class CachedContentEntry:
    hash_value: str
    data: CachePayload

    def to_dict(self) -> dict[str, object]:
        return {"hash": self.hash_value, "data": self.data}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedContentEntry" | None:
        hash_value = data.get("hash")
        entry_data = data.get("data")
        if not isinstance(hash_value, str) or not isinstance(entry_data, dict):
            return None
        return cls(hash_value=hash_value, data=entry_data)


class BuildCache:
    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.cache_dir = cache_dir
        self.enabled = enabled
        self._entries: dict[str, str] = {}
        self._content_entries: dict[str, CachedContentEntry] = {}

    def has_dynamic_constructs(self, template: str) -> bool:
        ast = _jinja_env.parse(template)
        return self._walk(ast)

    def _walk(self, node: nodes.Node) -> bool:
        for child in node.iter_child_nodes():
            if isinstance(child, DYNAMIC_NODE_TYPES):
                return True
            if self._walk(child):
                return True
        return False

    def compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def needs_rebuild(self, filename: str, content: str) -> bool:
        if not self.enabled:
            return True
        current_hash = self.compute_hash(content)
        return self._entries.get(filename) != current_hash

    def update(self, filename: str, content: str) -> None:
        if not self.enabled:
            return
        self._entries[filename] = self.compute_hash(content)

    def _compute_content_hash(self, raw: str, config_key: str) -> str:
        return self.compute_hash(f"{raw}\0{config_key}")

    def get_content(
        self, filename: str, raw: str, config_key: str
    ) -> CachePayload | None:
        if not self.enabled:
            return None
        entry = self._content_entries.get(filename)
        if entry is None:
            return None
        expected_hash = self._compute_content_hash(raw, config_key)
        if entry.hash_value != expected_hash:
            return None
        return entry.data

    def set_content(
        self, filename: str, raw: str, config_key: str, data: Mapping[str, object]
    ) -> None:
        if not self.enabled:
            return
        entry_hash = self._compute_content_hash(raw, config_key)
        self._content_entries[filename] = CachedContentEntry(
            hash_value=entry_hash,
            data=dict(data),
        )

    def _cache_data(self) -> dict[str, object]:
        return {
            "templates": self._entries,
            "content": {
                filename: entry.to_dict()
                for filename, entry in self._content_entries.items()
            },
        }

    def _cache_path(self) -> Path:
        return self.cache_dir / ".pyssg_cache.json"

    def _ensure_cache_file(self) -> Path:
        cache_path = self._cache_path()
        if not cache_path.exists():
            self.create(cache_dir=self.cache_dir)
        return cache_path

    def _reset_entries(self) -> None:
        self._entries = {}
        self._content_entries = {}

    def _read_cache_data(self) -> object:
        cache_path = self._ensure_cache_file()
        with open(cache_path) as f:
            return json.loads(f.read())

    def _load_template_entries(self, data: dict[str, Any]) -> None:
        self._entries = {
            str(filename): str(entry_hash)
            for filename, entry_hash in data.items()
            if isinstance(filename, str) and isinstance(entry_hash, str)
        }

    def _load_content_entries(self, data: dict[str, Any]) -> None:
        for filename, entry in data.items():
            if not isinstance(filename, str) or not isinstance(entry, dict):
                continue
            parsed_entry = CachedContentEntry.from_dict(entry)
            if parsed_entry is not None:
                self._content_entries[filename] = parsed_entry

    def _is_structured_cache_data(self, data: dict[str, Any]) -> bool:
        templates = data.get("templates")
        content = data.get("content")
        return isinstance(templates, dict) or isinstance(content, dict)

    def _load_structured_entries(self, data: dict[str, Any]) -> None:
        templates = data.get("templates")
        if isinstance(templates, dict):
            self._load_template_entries(templates)
        content = data.get("content")
        if isinstance(content, dict):
            self._load_content_entries(content)

    def _load_entries(self, data: object) -> None:
        self._reset_entries()
        if not isinstance(data, dict):
            return
        cache_data = cast(dict[str, Any], data)
        if self._is_structured_cache_data(cache_data):
            self._load_structured_entries(cache_data)
            return
        self._load_template_entries(cache_data)

    @staticmethod
    def create(cache_dir: Path) -> None:
        cache_path = cache_dir / ".pyssg_cache.json"
        with open(cache_path, "w") as f:
            f.write(json.dumps({"templates": {}, "content": {}}))

    def save(self) -> None:
        if not self.enabled:
            return
        cache_path = self._cache_path()
        with open(cache_path, "w") as f:
            f.write(json.dumps(self._cache_data()))

    def load(self) -> None:
        if not self.enabled:
            return
        self._load_entries(self._read_cache_data())
