# py-ssg Improvement Ideas

## Step 1 — 30 Candidate Ideas (one-liners)

1. Auto-generate `sitemap.xml` from content files at build time.
2. Built-in `draft: true` frontmatter support to skip posts during build.
3. Recursive content directory scanning (`content/blog/`, `content/docs/`, …).
4. Pagination support: split long content lists across multiple output pages.
5. WebSocket live-reload: push a reload signal to the browser instead of just rebuilding.
6. Built-in Jinja2 filters for sorting and filtering content (`sort_by_date`, `filter_by_tag`, …).
7. Built-in `static/` directory that is copied verbatim to `output/` on every build.
8. Per-post HTML file generation: produce one `output/<slug>.html` per markdown file automatically.
9. Atom feed support in addition to RSS 2.0.
10. Extend the file watcher to also watch `py-ssg.toml` and `pyssg_build.py`.
11. Debounce watcher events to avoid multiple redundant rebuilds per save.
12. Cache parsed markdown output (SHA-256 per file) for true incremental builds.
13. Richer error reporting: catch template/component errors and show filename + snippet, not raw tracebacks.
14. Sort the `content` list by `timestamp` by default (currently undefined `os.listdir` order).
15. `--open` flag for `py-ssg serve` to auto-open the browser.
16. `py-ssg clean` command: delete `output/` and `.pyssg_cache.json`.
17. Validate `py-ssg.toml` on load (required fields, valid Pygments theme names, URL format).
18. `py-ssg new <filename>` command: scaffold a markdown file with pre-filled YAML frontmatter.
19. Component slot/children support: allow components to wrap child content.
20. Expose a `tags` mapping (`{tag: [posts]}`) as a built-in template context variable.
21. `max_items` option per RSS feed to limit how many entries are emitted.
22. `--quiet` / `--verbose` CLI flags to control build output verbosity.
23. `extra` table in `py-ssg.toml` for arbitrary user-defined template variables.
24. Allow `pyssg_build.py` to register custom Jinja2 filters and globals.
25. Multiple content directories in config (`content_dirs = ["content", "docs"]`).
26. Image optimization / copy pass for a dedicated `assets/` directory.
27. `py-ssg export` command: package the output directory into a `.zip` or `.tar.gz`.
28. Content "collections": named subsets of posts configured in `py-ssg.toml`.
29. Markdown shortcode system: custom `{{< shortcode >}}` syntax calling Python functions.
30. `--base-url` CLI override to set `site.url` at build time without editing the config.

---

## Step 2 — Critical Evaluation

| # | Idea | Verdict | Reason |
|---|------|---------|--------|
| 1 | Sitemap generation | ✅ **Keep** | SEO essential; every public site needs one. Zero new dependencies. |
| 2 | Draft support | ✅ **Keep** | Near-universal blogging feature. One frontmatter field, 3 lines of code, very high daily value. |
| 3 | Recursive content dirs | ✅ **Keep** | `os.listdir` currently misses `content/blog/*.md`. Fixing this is a correctness improvement, not just a feature. |
| 4 | Pagination | ❌ **Reject** | Requires generating multiple output files from one template — a fundamental architecture change. High complexity for unclear scope. |
| 5 | WebSocket live-reload | ✅ **Keep** | Full-page hard-reloads on every save are jarring. A tiny injected `<script>` + EventSource server endpoint delivers a professional dev experience with no new dependencies (just stdlib `http.server`). |
| 6 | Built-in Jinja2 content filters | ✅ **Keep** | Content ordering is currently undefined. Every blog template will need sorting. Shipping `sort_by_date`, `filter_by_tag` as global filters removes boilerplate from every user's template. |
| 7 | Static assets directory | ✅ **Keep** | CSS, fonts, images, favicons all need a home. Without a `static/` dir users must use `after_build` hooks just to copy a CSS file. Essential quality-of-life. |
| 8 | Per-post file generation | ❌ **Reject** | Requires a new concept (template-per-content-item or path config) that rewrites the entire build output model. Too architectural for this stage. |
| 9 | Atom feed | ❌ **Reject** | Atom is not meaningfully better for users than RSS 2.0 in practice. Doubles feed code for marginal gain. |
| 10 | Watch `py-ssg.toml` / `pyssg_build.py` | ✅ **Keep** | Editing config or build hooks today does not trigger a rebuild — a correctness bug. The fix is a one-liner (add two paths to the watcher list). |
| 11 | Watcher debouncing | ✅ **Keep** | Saving one file triggers several `FileModifiedEvent`s, causing 3–5 redundant full builds. A 300 ms debounce makes the dev loop feel responsive rather than stuttery. |
| 12 | Incremental markdown caching | ✅ **Keep** | Syntax highlighting is expensive. Caching the rendered HTML keyed on the source file's SHA-256 means a 200-post blog with only 1 changed file parses only 1 file. Real, measurable speedup. |
| 13 | Richer build error reporting | ✅ **Keep** | A Jinja2 `TemplateSyntaxError` currently prints a raw Python traceback. Catching it and printing `ERROR in templates/index.html line 7: unexpected end of block tag` is the difference between a great and a frustrating dev tool. |
| 14 | Sort `content` by timestamp by default | ✅ **Keep** | The `content` list is in `os.listdir` order today, which is filesystem-dependent and unpredictable. Sorting newest-first by default matches every user's expectation for a blog. |
| 15 | `--open` flag | ❌ **Reject** | Minor convenience. Easy to implement but doesn't solve a real pain point. A one-liner users can add as a shell alias. |
| 16 | `py-ssg clean` command | ✅ **Keep** | Stale output files from deleted templates or renamed posts accumulate silently. A `clean` command is the standard fix and keeps the tool set complete. |
| 17 | Config validation | ✅ **Keep** | Invalid Pygments theme names cause cryptic Pygments exceptions at parse time. Catching config problems early with friendly messages ("Unknown syntax theme 'monoke', did you mean 'monokai'?") saves significant debugging time. |
| 18 | `py-ssg new` command | ✅ **Keep** | Scaffolding a correctly-dated, properly-structured frontmatter stub is a small but daily workflow improvement. Reduces copy-paste errors. |
| 19 | Component children/slots | ❌ **Reject** | Requires switching from self-closing XML syntax to open/close tag pairs, touching the parser, template engine, and documentation. Correct but very large scope. |
| 20 | `tags` mapping in template context | ✅ **Keep** | Building a tag index in Jinja2 requires `{% set ns = namespace(map={}) %}` hacks. A pre-computed `tags` dict (`{"python": [post1, post2]}`) makes tag pages trivial to implement. |
| 21 | `max_items` per feed | ✅ **Keep** | Feeds with hundreds of items are slow for RSS readers and waste bandwidth. A simple integer config option costs almost nothing to implement. |
| 22 | `--quiet` / `--verbose` flags | ❌ **Reject** | Rich output is a feature, not a problem. Adding flags adds CLI surface area with minimal benefit. |
| 23 | `extra` table in config | ✅ **Keep** | Users need a way to put `analytics_id`, `twitter_handle`, `locale`, etc. into templates without modifying Python. An `[py-ssg.extra]` TOML table forwarded as `site.extra` is the clean solution. |
| 24 | Custom Jinja2 filters via build script | ✅ **Keep** | Power users who want `{{ post.title | slugify }}` or `{{ post.timestamp | human_date }}` currently can't add filters. Exposing the `Environment` through `BuildContext` unlocks this without changing the core. |
| 25 | Multiple content directories | ❌ **Reject** | Edge case. The `static/` dir (idea 7) and subdirectory scanning (idea 3) cover most real use cases. |
| 26 | Image optimization | ❌ **Reject** | Requires Pillow or an external tool. Out of scope; an `after_build` hook already solves this. |
| 27 | `py-ssg export` | ❌ **Reject** | `zip output/` is a one-liner in every shell. Not a compelling reason to add a command. |
| 28 | Content collections | ❌ **Reject** | Addressed adequately by `filter_by_tag` filter (idea 6) and the `tags` context (idea 20). |
| 29 | Markdown shortcodes | ❌ **Reject** | Complex to implement correctly; already partially covered by the component system and build hooks. |
| 30 | `--base-url` CLI override | ✅ **Keep** | CI/CD pipelines often build to a different path (GitHub Pages sub-path vs. production root). A `--base-url` flag makes `py-ssg build --base-url /my-blog` work without editing `py-ssg.toml`. |

---

## Step 3 — Detailed Plans for Surviving Ideas

---

### 1. Auto-generate `sitemap.xml`

**What it is**

After the template rendering phase, py-ssg generates a `sitemap.xml` using the XML Sitemap 0.9 protocol. Every markdown content item contributes a `<url>` entry whose `<loc>` is derived from the site URL and the post slug (filename without `.md`). Templates can optionally opt in with a `sitemap: true` frontmatter field; posts with `draft: true` (see idea 2) are excluded automatically. The feature is enabled by default when `site.url` is set, and can be turned off with `sitemap = false` in `py-ssg.toml`.

**Why it's a good improvement**

A sitemap is the baseline for Google/Bing search indexing. Every serious static site needs one. Generating it automatically from the same metadata already in memory (filenames, timestamps) adds zero overhead.

**Implementation plan**

Add a `SitemapGenerator` class in a new `pyssg/modules/sitemap.py`:

```python
from xml.etree.ElementTree import Element, SubElement, tostring
from pyssg.modules.markdown import MarkdownCollection

class SitemapGenerator:
    def __init__(self, site_url: str):
        self.site_url = site_url.rstrip("/")

    def generate(self, collection: MarkdownCollection) -> str:
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for item in collection:
            # skip drafts automatically
            if getattr(item.custom_fields, "draft", False):
                continue
            url_el = SubElement(urlset, "url")
            slug = item.filename.removesuffix(".md")
            SubElement(url_el, "loc").text = f"{self.site_url}/{slug}"
            if item.timestamp:
                SubElement(url_el, "lastmod").text = item.timestamp
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(urlset, encoding="unicode")
```

Call it in `BuildCommand.execute()` after RSS generation, writing to `output/sitemap.xml`. Add a `sitemap: bool = True` field to `SiteConfig`.

**Possible downsides**

- Sites without `site.url` set will generate sitemaps with relative `<loc>` values, which is invalid per the spec. Guard with a check and emit a warning.

**Confidence: 95%** — Standard, well-defined format; zero new dependencies; trivially extensible.

---

### 2. Draft Post Support

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

---

### 3. Recursive Content Directory Scanning

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

---

### 5. WebSocket Live-Reload

**What it is**

After a rebuild completes, the dev server sends a reload signal to all connected browsers. A small `<script>` snippet is injected into every served `.html` response that opens a Server-Sent Events (SSE) connection. When the connection receives a `"reload"` message the script calls `location.reload()`.

SSE is chosen over WebSockets because it uses stdlib `http.server` with no extra thread management and a single persistent GET connection per browser tab.

**Why it's a good improvement**

Currently, developers must manually refresh the browser after every change. Live-reload is the industry standard for static site dev servers (Eleventy, Hugo, Vite, Jekyll all have it). It eliminates the most repetitive action in the edit→save→view loop.

**Implementation plan**

Add an SSE endpoint in `Server`:

```python
class Server:
    def __init__(self, directory, port):
        ...
        self._reload_clients: list = []

    def notify_reload(self) -> None:
        for q in list(self._reload_clients):
            q.put("reload")

    # In the request handler:
    def do_GET(self):
        if self.path == "/__reload__":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            q = queue.Queue()
            self.server._reload_clients.append(q)
            try:
                while True:
                    msg = q.get()
                    self.wfile.write(f"data: {msg}\n\n".encode())
                    self.wfile.flush()
            except Exception:
                self.server._reload_clients.remove(q)
            return
        # inject snippet before </body>
        ...
```

Injected snippet (appended to every `.html` response):

```html
<script>
  new EventSource("/__reload__").onmessage = () => location.reload();
</script>
```

Call `server.notify_reload()` at the end of `ServeCommand._rebuild()`.

**Possible downsides**

- The snippet pollutes production builds if users accidentally build with serve-mode artifacts. The snippet should only be injected by the server at serve time, never written to disk.
- Concurrent SSE client management needs thread safety (use `threading.Lock` around `_reload_clients`).

**Confidence: 88%** — Major DX win; SSE is simpler than WebSockets; no new dependencies needed.

---

### 6. Built-in Jinja2 Content Filters

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

---

### 7. Built-in Static Assets Directory

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

---

### 10. Watch `py-ssg.toml` and `pyssg_build.py`

**What it is**

The `ServeCommand` currently watches `content/`, `templates/`, and `components/`. Changing `py-ssg.toml` (e.g., toggling syntax highlighting, adding a feed) or editing `pyssg_build.py` does not trigger a rebuild — a silent bug. The fix adds the config file and build script file to the watched paths.

**Why it's a good improvement**

This is a correctness fix. Users who edit `py-ssg.toml` during development currently see stale output and may not realise the server didn't pick up the change. The fix is a one-liner.

**Implementation plan**

In `ServeCommand.execute()`:

```python
watch_files = [
    project_dir / "content",
    project_dir / "templates",
    project_dir / "components",
]
# Also watch individual files
for f in ["py-ssg.toml", "pyssg_build.py"]:
    p = project_dir / f
    if p.exists():
        watch_files.append(p)
```

The `Watcher` already supports individual file paths via `watchdog`'s `schedule` call with a non-recursive watch.

**Possible downsides**

- `watchdog` emits events for the parent directory when watching a file on some platforms. Use `recursive=False` and filter by filename in the handler.

**Confidence: 99%** — Pure correctness fix. Zero downside.

---

### 11. Watcher Debouncing

**What it is**

Most editors write a file in two events: a truncation followed by a content write, sometimes also firing a `modified` and a `moved` event. Without debouncing, a single save triggers 2–4 `_rebuild()` calls within milliseconds. Adding a 300 ms debounce collapses these into one rebuild.

**Why it's a good improvement**

Multiple near-simultaneous rebuilds cause race conditions (two processes writing to the same output file), wasted CPU, and confusing terminal output with interleaved log lines.

**Implementation plan**

```python
import threading

class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change, debounce_seconds=0.3):
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._on_change)
            self._timer.start()
```

**Possible downsides**

- The 300 ms delay means the rebuild starts slightly later after a save. This is imperceptible to humans and a fair trade for correctness.

**Confidence: 97%** — Standard pattern; solves a real race condition with trivial code.

---

### 12. Incremental Markdown Caching

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

---

### 13. Richer Build Error Reporting

**What it is**

Replace raw Python tracebacks for template/component errors with structured, user-friendly messages that identify the problematic file, the line number, and the error message. Jinja2 already provides `TemplateSyntaxError` and `TemplateError` with filename and line number metadata.

**Why it's a good improvement**

A new user who makes a typo in a template today sees:

```
jinja2.exceptions.TemplateSyntaxError: unexpected char '%' at 42
```

With proper error reporting they see:

```
✗ Syntax error in templates/index.html (line 42):
  unexpected char '%'
```

This is the difference between a beginner giving up and figuring it out in 30 seconds.

**Implementation plan**

Wrap the render step in `BuildCommand.execute()`:

```python
try:
    rendered = engine.render(template, context={"content": list(collection)})
except TemplateSyntaxError as e:
    self._error(f"Syntax error in templates/{filename} (line {e.lineno}):\n  {e.message}")
    continue
except TemplateError as e:
    self._error(f"Render error in templates/{filename}:\n  {e.message}")
    continue
```

Add a similar try/except in `HtmlTemplateEngine._get_component()` with component filename context.

**Possible downsides**

- Swallowing errors and `continue`-ing means a broken template doesn't abort the build. This is arguably the right behaviour for `serve` mode but wrong for `build` mode. Use `--strict` flag to control.

**Confidence: 94%** — Pure DX improvement; Jinja2's error objects already carry all the needed metadata.

---

### 14. Sort `content` by Timestamp by Default

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

---

### 16. `py-ssg clean` Command

**What it is**

`py-ssg clean` deletes the `output/` directory and the `.pyssg_cache.json` file. Useful when: a template file was deleted (stale output file remains), a post was renamed (old slug file persists), or after switching between site configurations.

**Why it's a good improvement**

Without `clean`, stale files from deleted templates or renamed posts silently remain in `output/`. Users discover this only when they deploy and see old pages still live. A clean command is the standard solution and rounds out the toolset (`init`, `build`, `serve`, `clean`).

**Implementation plan**

Add a `CleanCommand` in `pyssg/commands/clean.py`:

```python
class CleanCommand(BaseCommand):
    def execute(self) -> None:
        project_dir = Path.cwd()
        output_dir = project_dir / "output"
        cache_path = project_dir / ".pyssg_cache.json"
        if output_dir.exists():
            shutil.rmtree(output_dir)
            self._success("Removed output/")
        if cache_path.exists():
            cache_path.unlink()
            self._success("Removed .pyssg_cache.json")
```

Register in `main.py`:

```python
@app.command()
def clean() -> None:
    CleanCommand().execute()
```

Optionally add `--output-only` and `--cache-only` flags.

**Possible downsides**

- Accidental `py-ssg clean` in the wrong directory. The command should only operate in a directory that contains `py-ssg.toml` — add a guard check.

**Confidence: 96%** — Essential maintenance command; trivial to implement safely.

---

### 17. Config Validation on Load

**What it is**

When `py-ssg.toml` is loaded, validate known fields before the build starts. Specifically:
- Check that `syntax.theme_light` and `syntax.theme_dark` are valid Pygments style names.
- Check that `site.url` is a valid URL when feeds are configured.
- Check that feed `output` filenames don't conflict with template filenames.
- Emit a named `ConfigWarning` (not a crash) for non-critical issues.

**Why it's a good improvement**

Today, an invalid theme name like `"monoke"` causes Pygments to raise an exception deep in the build pipeline with a confusing traceback. Validation surfaces the error immediately with a helpful message like: `"Unknown Pygments theme 'monoke'. Valid themes include: monokai, friendly, …"`.

**Implementation plan**

Add a `validate()` method to `SiteConfig`:

```python
from pygments.styles import get_all_styles

def validate(self) -> list[str]:
    warnings = []
    valid_themes = set(get_all_styles())
    if self.syntax.enabled:
        for attr, name in [("theme_light", self.syntax.theme_light),
                           ("theme_dark", self.syntax.theme_dark)]:
            if name not in valid_themes:
                closest = difflib.get_close_matches(name, valid_themes, n=1)
                hint = f" Did you mean '{closest[0]}'?" if closest else ""
                warnings.append(f"Unknown syntax.{attr} '{name}'.{hint}")
    if self.feeds and not self.url:
        warnings.append("RSS feeds configured but site.url is empty — feed links will be broken.")
    return warnings
```

Call `config.validate()` in `BuildCommand.execute()` and print each warning with `self._warning(...)`.

**Possible downsides**

- Adds a `difflib` import (stdlib). The Pygments import for `get_all_styles` is already a dependency. No new dependencies.

**Confidence: 92%** — Significantly improves the new-user experience at essentially zero cost.

---

### 18. `py-ssg new` Command

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

---

### 20. `tags` Mapping in Template Context

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

---

### 21. `max_items` Per RSS Feed

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

---

### 23. `extra` Table in Config for User-Defined Template Variables

**What it is**

An `[py-ssg.extra]` TOML table whose key-value pairs are forwarded to all templates as `site.extra.<key>`. Users can store arbitrary site-level values (analytics IDs, social handles, locale, theme colour) without touching Python.

```toml
[py-ssg.extra]
analytics_id = "G-XXXXXXXXXX"
twitter = "@myhandle"
locale = "en-US"
```

Template usage:

```html
<meta name="twitter:site" content="{{ site.extra.twitter }}">
```

**Why it's a good improvement**

Every non-trivial site has site-wide variables that don't fit into `name`, `url`, or `description`. Today users must either hardcode these in templates or maintain a build hook that injects them. An `extra` dict is the clean, established solution (used by Hugo, MkDocs, Jekyll).

**Implementation plan**

Add `extra: SimpleNamespace` to `SiteConfig`:

```python
@dataclass
class SiteConfig:
    ...
    extra: SimpleNamespace = field(default_factory=SimpleNamespace)

    @classmethod
    def from_dict(cls, data: dict) -> SiteConfig:
        extra_data = data.get("extra", {})
        extra = SimpleNamespace(**extra_data)
        return cls(..., extra=extra)
```

**Possible downsides**

- Key names in `extra` could shadow built-in `SiteConfig` attribute names if the user accesses `site` as a dict. Since we use `SimpleNamespace` on a sub-object, there is no collision.

**Confidence: 94%** — Zero complexity; eliminates a daily workaround for every advanced user.

---

### 24. Custom Jinja2 Filters via Build Script

**What it is**

Expose the `jinja2.Environment` object through `BuildContext`, allowing `pyssg_build.py` to register custom filters and global functions before templates are rendered.

```python
# pyssg_build.py
def before_build(context):
    context.jinja_env.filters["slugify"] = lambda s: s.lower().replace(" ", "-")
    context.jinja_env.globals["current_year"] = datetime.now().year
```

Template usage:

```html
<a href="/{{ post.title|slugify }}">{{ post.title }}</a>
<footer>© {{ current_year }}</footer>
```

**Why it's a good improvement**

Power users who need custom template logic currently have no clean hook to register Jinja2 filters. They must fork the project or use ugly workarounds. Exposing `jinja_env` through the build context unlocks this without any architecture change — the `Environment` already exists.

**Implementation plan**

Add `jinja_env: Environment` to `BuildContext`:

```python
@dataclass
class BuildContext:
    ...
    jinja_env: Environment
```

Pass the `HtmlTemplateEngine`'s environment instance into `BuildContext` before `before_build` is called. In `HtmlTemplateEngine`, expose `self.env` as a public attribute.

Call `build_script.before_build(context)` *after* the engine is constructed so the environment is available.

**Possible downsides**

- Users overwriting built-in filters (like `sort_by_date`) could break their own templates. Document the precedence rules.
- Exposing the `Environment` is a semi-stable API; changes to `HtmlTemplateEngine` internals could break build scripts. Mark it as the public API and commit to it.

**Confidence: 88%** — Major power-user unlock; the plumbing is already there; just needs to be exposed.

---

### 30. `--base-url` CLI Override

**What it is**

`py-ssg build --base-url https://staging.example.com` overrides `site.url` for that build run without modifying `py-ssg.toml`. This is essential for CI/CD pipelines that build to different environments (GitHub Pages sub-path, Netlify preview URLs, staging, production).

**Why it's a good improvement**

Today a CI pipeline deploying to GitHub Pages (`https://user.github.io/repo/`) must either maintain separate `py-ssg.toml` files or use `sed` to patch the URL. An override flag is the clean solution used by virtually all SSG tools.

**Implementation plan**

```python
@app.command()
def build(base_url: str | None = typer.Option(default=None)) -> None:
    BuildCommand(base_url=base_url).execute()
```

```python
class BuildCommand(BaseCommand):
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url

    def execute(self) -> None:
        ...
        config = SiteConfig.load(project_dir)
        if self._base_url:
            config.url = self._base_url
        ...
```

**Possible downsides**

- The flag only affects `site.url`; any config values derived from the URL at load time (e.g., feed links computed on init) must be re-derived after the override. Since `RssFeedGenerator` reads `config.url` at call time, this is already handled correctly.

**Confidence: 91%** — One-liner addition to the CLI that solves a concrete DevOps pain point.

---

## Summary of Surviving Ideas

| # | Idea | Confidence |
|---|------|-----------|
| 1 | Auto-generate `sitemap.xml` | 95% |
| 2 | Draft post support (`draft: true`) | 97% |
| 3 | Recursive content directory scanning | 90% |
| 5 | WebSocket / SSE live-reload in dev server | 88% |
| 6 | Built-in Jinja2 content filters | 96% |
| 7 | Built-in `static/` assets directory | 98% |
| 10 | Watch `py-ssg.toml` and `pyssg_build.py` | 99% |
| 11 | Watcher debouncing (300 ms) | 97% |
| 12 | Incremental markdown content caching | 85% |
| 13 | Richer build error reporting | 94% |
| 14 | Sort `content` by timestamp by default | 99% |
| 16 | `py-ssg clean` command | 96% |
| 17 | Config validation on load | 92% |
| 18 | `py-ssg new <title>` scaffolding command | 93% |
| 20 | `tags` mapping in template context | 95% |
| 21 | `max_items` per RSS feed | 99% |
| 23 | `[py-ssg.extra]` user-defined template variables | 94% |
| 24 | Custom Jinja2 filters via build script | 88% |
| 30 | `--base-url` CLI build override | 91% |
