# Task 7: Built-in Static Assets Directory


**What it is**

If a `static/` directory exists at the project root, its contents are copied to `output/static/` (or directly to `output/` if `static_dir_output = "root"` in config) on every build. This replaces the common `after_build` hook pattern of calling `shutil.copytree`.

**Why it's a good improvement**

Fonts, favicons, images, global CSS files, and JavaScript all need to live somewhere. Without `static/`, users are forced to either put assets inside `templates/` (polluting the template namespace) or write a build hook for every project. A `static/` convention is used by Hugo, Eleventy, Next.js, and Jekyll — users will expect it.

**Implementation plan**

In `BuildCommand.execute()`, add after template rendering:

```python
static_dir = project_dir / "static"
if static_dir.exists():
    dest = output_dir / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(static_dir, dest)
    self._info(f"Copied static assets → output/static/")
```

Add a `static_dir: str = "static"` config option to `SiteConfig` for projects that want a different name or to merge into output root.

**Possible downsides**

- Deleting and re-copying on every build is slightly wasteful for large asset directories. A hash-based copy-only-if-changed approach would be better long-term, but `shutil.copytree` is sufficient for v1.
- The `output/static/` path must be reflected in template `href` attributes (`href="/static/style.css"`). Document this clearly.

**Confidence: 98%** — Solves a concrete daily pain point; trivial to implement.
