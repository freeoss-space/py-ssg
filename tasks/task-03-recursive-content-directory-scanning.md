# Task 3: Recursive Content Directory Scanning


**What it is**

Replace the flat `os.listdir` in `MarkdownParser._read_files` with `Path.rglob("*.md")`, allowing content to be organised in subdirectories (`content/blog/2025/post.md`, `content/docs/api.md`). The `filename` field on each item becomes the relative path from `content/` (e.g. `blog/2025/post.md`), preserving uniqueness.

**Why it's a good improvement**

Any project with more than ~20 posts needs to organise content into folders. Currently, all files must be flat in `content/`, making large projects unmaintainable. This is a correctness gap, not a luxury feature.

**Implementation plan**

```python
def _read_files(self) -> list[tuple[str, str]]:
    items = []
    for filepath in sorted(Path(self.content_dir).rglob("*.md")):
        rel = filepath.relative_to(self.content_dir)
        with open(filepath) as f:
            raw = f.read()
        items.append((str(rel), raw))
    return items
```

The `filename` field changes from `"post.md"` to `"blog/post.md"`. The slug in RSS and sitemap becomes `blog/post`, which maps naturally to a directory-based URL structure.

**Possible downsides**

- Breaking change for users who reference `post.filename` directly and expect a flat name. Mitigate with a clear migration note.
- Template authors relying on the slug for links must now handle the subdirectory path.

**Confidence: 90%** — High value, well-understood change. The slug semantics shift is a one-time migration.
