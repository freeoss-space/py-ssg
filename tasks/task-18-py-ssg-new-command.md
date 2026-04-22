# Task 18: `py-ssg new` Command


**What it is**

`py-ssg new my-post-title` creates `content/my-post-title.md` with a pre-filled YAML frontmatter stub:

```markdown
---
title: My Post Title
timestamp: "2026-04-09"
tags: []
draft: true
---

Write your content here.
```

The filename is slugified from the title argument. The timestamp is today's date. The post starts as a draft.

**Why it's a good improvement**

Creating a new post today requires: open a terminal, `touch content/my-post.md`, open in editor, type out the frontmatter from memory (or copy-paste from another file), correct the date. `py-ssg new` reduces this to one command. It also prevents common mistakes like wrong date format or missing required fields.

**Implementation plan**

```python
@app.command()
def new(title: str = typer.Argument()) -> None:
    NewCommand(title=title).execute()
```

```python
class NewCommand(BaseCommand):
    def __init__(self, title: str):
        self.title = title

    def execute(self) -> None:
        slug = _slugify(self.title)  # reuse existing slugify from markdown.py
        today = date.today().isoformat()
        filename = f"{slug}.md"
        filepath = Path.cwd() / "content" / filename
        if filepath.exists():
            self._error(f"File already exists: content/{filename}")
            return
        content = f"""---
title: {self.title}
timestamp: "{today}"
tags: []
draft: true
---

Write your content here.
"""
        filepath.write_text(content)
        self._success(f"Created content/{filename}")
```

**Possible downsides**

- None significant. The command is purely additive.

**Confidence: 93%** — Small but genuinely useful quality-of-life improvement; zero risk.
