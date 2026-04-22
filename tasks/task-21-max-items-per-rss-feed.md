# Task 21: `max_items` Per RSS Feed


**What it is**

Add an optional `max_items` integer field to each `[[py-ssg.feeds]]` config block. When set, only the `max_items` most recent posts are included in that feed.

```toml
[[py-ssg.feeds]]
title = "My Blog"
output = "feed.xml"
max_items = 20
```

**Why it's a good improvement**

RSS readers download the full feed XML on every poll. A site with 500 posts generates a 500-item feed that is slow to download and parse. `max_items = 20` is the standard for feed readers. Without this option, feeds grow without bound forever.

**Implementation plan**

Add `max_items: int | None = None` to `FeedConfig.from_dict`. In `RssFeedGenerator._filter_items`:

```python
def _filter_items(self, collection, feed) -> list:
    items = list(collection)
    if feed.tags:
        tag_set = set(feed.tags)
        items = [item for item in items if tag_set.intersection(item.tags)]
    items.sort(key=lambda x: x.timestamp, reverse=True)
    if feed.max_items is not None:
        items = items[:feed.max_items]
    return items
```

**Possible downsides**

- None. Purely additive; defaults to current behaviour (no limit) when omitted.

**Confidence: 99%** — One-liner fix for a real-world issue; zero risk.
