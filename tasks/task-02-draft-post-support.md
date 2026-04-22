# Task 2: Draft Post Support


**What it is**

A post with `draft: true` in its YAML frontmatter is silently excluded from the `content` list passed to templates, from RSS feeds, and from the sitemap. A `--drafts` flag on `py-ssg build` / `py-ssg serve` re-enables them for local preview.

**Why it's a good improvement**

Working on a half-finished post while the live site rebuilds is a very common real-world workflow. Today users must delete or move the file. This feature matches the behaviour of Hugo, Eleventy, and Jekyll.

**Implementation plan**

In `MarkdownContent.from_raw`, promote `draft` from a custom field to a first-class boolean field:

```python
@dataclass
class MarkdownContent:
    ...
    draft: bool = False

    @classmethod
    def from_raw(cls, filename, raw, ...) -> MarkdownContent:
        ...
        return cls(
            ...
            draft=bool(post.get("draft", False)),
        )
```

In `BuildCommand.execute()`, after parsing, filter the list passed to templates:

```python
visible_content = [c for c in collection if not c.draft or include_drafts]
rendered = engine.render(template, context={"content": visible_content})
```

Add `include_drafts: bool = False` to `BuildContext` and pass it through from a `--drafts` CLI flag.

**Possible downsides**

- `draft` was previously accessible via `post.custom_fields.draft`; this is a minor breaking change. Document it clearly.

**Confidence: 97%** — Universally expected feature with a trivial, contained implementation.
