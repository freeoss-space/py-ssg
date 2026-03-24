import hashlib
import json
from pathlib import Path

from jinja2 import Environment, nodes

_jinja_env = Environment()

DYNAMIC_NODE_TYPES = (nodes.For, nodes.If, nodes.Macro, nodes.CallBlock)


class BuildCache:
    def __init__(self, cache_dir: Path, enabled: bool = True):
        self.cache_dir = cache_dir
        self.enabled = enabled
        self._entries: dict[str, str] = {}

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

    @staticmethod
    def create(cache_dir: Path) -> None:
        cache_path = cache_dir / ".pyssg_cache.json"
        with open(cache_path, "w") as f:
            f.write(json.dumps({}))

    def save(self) -> None:
        if not self.enabled:
            return
        cache_path = self.cache_dir / ".pyssg_cache.json"
        with open(cache_path, "w") as f:
            f.write(json.dumps(self._entries))

    def load(self) -> None:
        if not self.enabled:
            return
        cache_path = self.cache_dir / ".pyssg_cache.json"
        if not cache_path.exists():
            self.create(cache_dir=self.cache_dir)
        with open(cache_path) as f:
            self._entries = json.loads(f.read())
