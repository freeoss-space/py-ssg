# Task 6: Built-in Jinja2 Content Filters


**What it is**

Register a set of content-aware Jinja2 filters globally in `HtmlTemplateEngine`:

| Filter | Signature | Behaviour |
|--------|-----------|-----------|
| `sort_by_date` | `content\|sort_by_date` | Sort list newest-first by `timestamp` |
| `sort_by_date_asc` | `content\|sort_by_date_asc` | Oldest-first |
| `filter_by_tag` | `content\|filter_by_tag("python")` | Keep posts that have the tag |
| `filter_by_author` | `content\|filter_by_author("Alice")` | Keep posts by that author name |
| `reject_drafts` | `content\|reject_drafts` | Remove draft posts |

**Why it's a good improvement**

The `content` list currently arrives in an undefined OS order. Every template author needs to sort it. Providing canonical filters eliminates copy-paste Jinja2 idioms and makes templates readable.

**Implementation plan**

In `pyssg/modules/html.py`, before constructing the `Environment`:

```python
def _build_env() -> Environment:
    env = Environment(loader=BaseLoader(), autoescape=False)
    env.filters["sort_by_date"] = lambda lst: sorted(
        lst, key=lambda p: p.timestamp or "", reverse=True
    )
    env.filters["sort_by_date_asc"] = lambda lst: sorted(
        lst, key=lambda p: p.timestamp or ""
    )
    env.filters["filter_by_tag"] = lambda lst, tag: [
        p for p in lst if tag in p.tags
    ]
    env.filters["filter_by_author"] = lambda lst, name: [
        p for p in lst if p.author.name == name
    ]
    env.filters["reject_drafts"] = lambda lst: [p for p in lst if not p.draft]
    return env
```

Example template usage:

```html
{% for post in content|sort_by_date|filter_by_tag("python") %}
  <article>{{ post.title }}</article>
{% endfor %}
```

**Possible downsides**

- Filter names could collide with user-defined Jinja2 filters registered via build hooks. Document precedence clearly (build-hook filters registered last win).

**Confidence: 96%** — Pure utility with zero complexity; every template will benefit.
