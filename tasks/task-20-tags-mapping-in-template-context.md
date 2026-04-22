# Task 20: `tags` Mapping in Template Context


**What it is**

In addition to `content`, templates receive a `tags` context variable: a `dict[str, list[MarkdownContent]]` mapping each unique tag to the list of posts that have it, pre-sorted newest-first.

```jinja2
{% for tag, posts in tags|dictsort %}
  <section>
    <h2>{{ tag }}</h2>
    {% for post in posts %}
      <a href="/{{ post.filename | replace('.md', '') }}">{{ post.title }}</a>
    {% endfor %}
  </section>
{% endfor %}
```

**Why it's a good improvement**

Building a tag index in pure Jinja2 today requires a `namespace` hack and is practically impossible to sort. The pre-computed mapping makes tag pages, tag clouds, and related-posts sections trivially simple.

**Implementation plan**

In `BuildCommand.execute()`, before rendering:

```python
from collections import defaultdict

tag_map: dict[str, list] = defaultdict(list)
for post in sorted_content:
    for tag in post.tags:
        tag_map[tag].append(post)

rendered = engine.render(template, context={
    "content": sorted_content,
    "tags": dict(tag_map),
})
```

**Possible downsides**

- Large sites with many tags produce a large `tags` dict, but it is the same data as `content` just re-indexed — no extra memory beyond the references.

**Confidence: 95%** — Zero complexity; transforms a common template pain point into a one-liner.
