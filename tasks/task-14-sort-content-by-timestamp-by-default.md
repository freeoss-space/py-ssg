# Task 14: Sort `content` by Timestamp by Default


**What it is**

The `content` list passed to templates is currently in `os.listdir` order — filesystem-dependent, non-deterministic across platforms, and almost never what the template author wants. Sort it newest-first by `timestamp` by default (posts without a timestamp sort to the end).

**Why it's a good improvement**

This is a correctness fix. Every blog template will have `{% for post in content %}` and expects newest posts first. Filesystem order makes output non-reproducible and silently wrong.

**Implementation plan**

In `BuildCommand.execute()`, after `collection` is populated:

```python
sorted_content = sorted(
    list(collection),
    key=lambda p: p.timestamp or "",
    reverse=True,
)
rendered = engine.render(template, context={"content": sorted_content})
```

Add a `content_sort: str = "date_desc"` option to `SiteConfig` (`"date_desc"`, `"date_asc"`, `"filename"`, `"none"`) for users who want a different default.

**Possible downsides**

- Changes existing behaviour. Users who relied on filesystem order (unlikely) will see reordering.

**Confidence: 99%** — The current behaviour is a bug; this is the fix.
