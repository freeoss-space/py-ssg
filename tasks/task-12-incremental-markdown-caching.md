# Task 12: Incremental Markdown Caching


**What it is**

The existing `BuildCache` only caches templates (by SHA-256 of the template source). Parsing markdown — especially with Pygments syntax highlighting — is the most expensive step. Extending the cache to store rendered HTML per markdown file means unchanged posts are not re-parsed on every build.

Cache key: `SHA-256(raw_markdown_content + syntax_config_repr + toc_config_repr)`
Cache value: serialised `MarkdownContent` fields stored in `.pyssg_cache.json` under a `"content"` key.

**Why it's a good improvement**

A blog with 100 posts and syntax highlighting enabled takes seconds to parse. With content caching, only the 1–2 changed files are re-parsed. This transforms the dev loop from "wait 3 seconds" to "wait 0.1 seconds".

**Implementation plan**

Extend `BuildCache` with content cache methods:

```python
class BuildCache:
    def __init__(self, ...):
        ...
        self._content_entries: dict[str, dict] = {}

    def get_content(self, filename: str, raw: str, config_key: str) -> dict | None:
        key = self.compute_hash(raw + config_key)
        entry = self._content_entries.get(filename)
        if entry and entry.get("hash") == key:
            return entry.get("data")
        return None

    def set_content(self, filename: str, raw: str, config_key: str, data: dict) -> None:
        key = self.compute_hash(raw + config_key)
        self._content_entries[filename] = {"hash": key, "data": data}
```

In `MarkdownContent`, add `to_dict()` / `from_dict()` serialisation methods. In `MarkdownParser._parse_sequential/_parse_parallel`, check the cache before parsing.

**Possible downsides**

- `.pyssg_cache.json` grows with a serialised copy of all rendered HTML. For a site with large posts this could be 10–50 MB. Consider a separate `.pyssg_content_cache.json` file.
- Parallel parsing with `ProcessPoolExecutor` makes per-file cache checking harder (workers don't share the cache object). The cache check must happen before dispatching to workers.

**Confidence: 85%** — Real performance win; the serialisation overhead is manageable.
