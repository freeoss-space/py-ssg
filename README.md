# py-ssg

A fast, extensible static site generator built with Python 3.14+.

py-ssg converts Markdown files with YAML frontmatter into a complete static website using Jinja2 templates and a custom component system. It includes syntax highlighting, table of contents generation, RSS feeds, build caching, parallel processing, and a live-reloading development server.

## Installation

Requires Python 3.14 or later.

```bash
pip install py-ssg
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install py-ssg
```

## Quick Start

```bash
# Create a new project
py-ssg init my-blog
cd my-blog

# Add content
echo '---
title: Hello World
timestamp: "2025-01-15"
tags:
  - intro
---

# Hello World

This is my first post.' > content/hello-world.md

# Create a template
echo '<html>
<body>
{% for post in content %}
<article>
  <h1>{{ post.title }}</h1>
  {{ post.html }}
</article>
{% endfor %}
</body>
</html>' > templates/index.html

# Build and serve
py-ssg serve
```

Your site is now live at `http://localhost:8000`.

## Commands

### `py-ssg init [folder_name] [--verbose] [--dry-run]`

Scaffolds a new project. If `folder_name` is omitted, initializes in the current directory.

Creates the following structure:

```
my-blog/
├── content/        # Markdown files
├── templates/      # Jinja2 HTML templates
├── components/     # Reusable HTML components
├── output/         # Generated site (build output)
└── py-ssg.toml     # Configuration file
```

Notes:

- If the target folder already exists, initialization stops with a warning.
- If `py-ssg.toml` already exists in the target, initialization stops and does not overwrite the project.
- `--dry-run` prints the planned filesystem changes without creating files or folders.

### `py-ssg build [--verbose] [--dry-run]`

Builds the site. Reads markdown from `content/`, renders templates from `templates/`, resolves components from `components/`, and writes the result to `output/`.

The build reports:
- Total files, built files, and cached files
- Component count
- RSS feeds generated
- Parsing, rendering, and total time

Behavior notes:

- `--dry-run` skips build hooks and does not write output files, feeds, cache updates, or copied assets.
- Markdown parsing still runs during `--dry-run`, so you can preview what would build.
- Static assets are copied after template rendering, so colliding static files win.

### `py-ssg serve [--port PORT] [--verbose] [--dry-run]`

Runs an initial build, starts a local HTTP server, and watches for changes. Automatically rebuilds when files in `content/`, `templates/`, `components/`, or the configured static directory change.

```bash
py-ssg serve              # Default port 8000
py-ssg serve --port 3000  # Custom port
```

Press `Ctrl+C` for graceful shutdown.

Behavior notes:

- If `--port` is omitted, py-ssg uses `py-ssg.server.port` from config.
- `--dry-run` performs the initial build preview and prints the URL it would serve, but does not start the server or watcher.

### `py-ssg new [--sub-folder SUB_FOLDER] [--verbose] [--dry-run] "Post Title"`

Creates a new markdown file inside `content/` with starter frontmatter.

```bash
py-ssg new "Post Title"
py-ssg new --sub-folder blog "Post Title"
```

Examples:

- `py-ssg new "Post Title"` creates `content/post_title.md`
- `py-ssg new --sub-folder blog "Post Title"` creates `content/blog/post_title.md`

The generated file includes:

```yaml
---
title: "Post Title"
timestamp: "2025-01-15"
---
```

Behavior notes:

- Filenames are generated from the title, lowercased and normalized with underscores. For example, `"Hello World"` becomes `hello_world.md`.
- `--sub-folder blog/2025` creates nested folders as needed under `content/`.
- If `--sub-folder` is omitted, py-ssg uses `new_content_subfolder` from config.
- If the target file already exists, the command stops with a warning.
- `--dry-run` prints the target path without writing the file.

## Project Structure

```
my-blog/
├── content/            # Markdown files with YAML frontmatter
│   ├── hello-world.md
│   └── about.md
├── templates/          # Jinja2 HTML templates
│   ├── index.html
│   └── about.html
├── components/         # Reusable HTML components
│   ├── Navbar.html
│   ├── Footer.html
│   └── Alert.html
├── static/             # Optional static assets copied on build
│   ├── favicon.ico
│   └── styles.css
├── output/             # Generated site
│   ├── index.html
│   ├── about.html
│   ├── static/
│   │   ├── favicon.ico
│   │   └── styles.css
│   ├── syntax.css
│   └── feed.xml
├── py-ssg.toml         # Configuration
├── pyssg_build.py      # Optional build hooks
└── .pyssg_cache.json   # Build cache (auto-generated)
```

## Configuration

All configuration lives in `py-ssg.toml`:

```toml
[py-ssg]
name = "Blog Name"
url = "https://yourblog.dev"
description = "My blog"
cache = true                    # Enable incremental build caching
static_dir = "static"           # Source directory for copied assets
static_dir_output = "static"    # "static" -> output/static, "root" -> output/
content_sort = "date_desc"      # "date_desc", "date_asc", "filename", or "none"
new_content_subfolder = ""      # Default sub-folder for `py-ssg new`

[py-ssg.server]
port = 8000                     # Dev server port

[py-ssg.syntax]
enabled = true                  # Syntax highlighting for code blocks
theme_light = "friendly"        # Pygments theme for light mode
theme_dark = "monokai"          # Pygments theme for dark mode

[py-ssg.toc]
enabled = false                 # Table of contents generation
max_depth = 3                   # Max heading depth to include

[[py-ssg.authors]]
name = "Your Name"
email = "your@email.com"

[[py-ssg.feeds]]
title = "Blog Name"
description = "My blog feed"
output = "feed.xml"

# Tag-filtered feed
[[py-ssg.feeds]]
title = "Blog Name - Tech"
description = "Tech posts only"
output = "tech.xml"
tags = ["tech"]
```

All configuration is accessible in templates via the `{{ site }}` variable (e.g., `{{ site.name }}`, `{{ site.url }}`).

## Static Assets

If your project has a `static/` directory, py-ssg copies it on every build after template rendering.

- `static_dir = "static"` copies `static/` to `output/static/`
- `static_dir_output = "root"` merges the directory directly into `output/`. Because static assets are copied after rendering, files in `static/` with the same relative path as generated output files overwrite the generated files.
- Set `static_dir` to another directory name, such as `public`, if you prefer a different source path

With the default layout, reference assets from templates with paths like `/static/styles.css` or `/static/favicon.ico`.

Use `{{ asset_url(...) }}` for local CSS, JS, images, and `syntax.css` so rebuilt assets get a new query-string version and browsers fetch the latest file instead of serving a stale cached copy.

When using `static_dir_output = "root"`, avoid filename collisions with generated pages and assets such as `index.html`, `feed.xml`, and `syntax.css` unless you intentionally want the static file to take precedence.

## Markdown Content

Place `.md` files in the `content/` directory. Each file uses YAML frontmatter for metadata.

### Frontmatter Fields

```yaml
---
title: My Post Title
timestamp: "2025-01-15"
# `date` is also accepted as an alias for `timestamp`
tags:
  - python
  - tutorial
author: Jane Doe
author_email: jane@example.com
author_avatar: https://example.com/avatar.png
author_url: https://example.com
---
```

**Built-in fields:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Post title |
| `timestamp` | string | Publication date (ISO format). `date` is accepted as an alias |
| `tags` | list | List of tag strings |
| `author` | string | Author name |
| `author_email` | string | Author email |
| `author_avatar` | string | Author avatar URL |
| `author_url` | string | Author website URL |
| `slug` | string | Optional slug metadata |
| `summary` | string | Optional short summary |
| `subtitle` | string | Optional subtitle |
| `draft` | boolean | Optional draft flag |
| `template` | string | Optional content page template path, usually a `*.tmpl.html` file under `templates/` |

**Custom fields:** Any additional YAML keys beyond the built-in fields become accessible via `post.custom_fields`. For example, adding `series: python-notes` and `reading_time: 4` makes them available as `post.custom_fields.series` and `post.custom_fields.reading_time`.

### Parsed Content Object

Each markdown file becomes a `MarkdownContent` object available in templates:

| Property | Description |
|----------|-------------|
| `post.filename` | Path relative to `content/` (e.g., `hello-world.md` or `blog/2025/hello-world.md`) |
| `post.html` | Rendered HTML content |
| `post.title` | Title from frontmatter |
| `post.timestamp` | Timestamp string from frontmatter (`date` aliases to this field) |
| `post.slug` | Built-in slug field |
| `post.summary` | Built-in summary field |
| `post.subtitle` | Built-in subtitle field |
| `post.draft` | Built-in draft flag |
| `post.tags` | List of tag strings |
| `post.author.name` | Author name |
| `post.author.email` | Author email |
| `post.author.avatar` | Author avatar URL |
| `post.author.url` | Author URL |
| `post.custom_fields` | Namespace with any extra frontmatter fields |
| `post.toc` | Generated table of contents HTML (if enabled) |

### Content Routing

Content routes are derived from the markdown filename relative to `content/`.

- `content/post.md` becomes `post.url == "/post/"`
- `content/blog/hello-world.md` becomes `post.url == "/blog/hello-world/"`
- Content pages generated from frontmatter templates and RSS feed links both use this same canonical route

### Content-Generated Pages

Markdown files can generate their own standalone output pages without `pyssg_build.py` by setting `template` in frontmatter:

```yaml
---
title: Hello World
template: blog/post.tmpl.html
---
```

With `content/blog/hello-world.md`, py-ssg renders `templates/blog/post.tmpl.html` and writes:

```text
output/blog/hello-world/index.html
```

These content-page templates receive:

- `site`
- `content`
- `tags`
- `post`

Quirks:

- Content-page outputs always follow the canonical route from `post.url`.
- Content-page rendering is currently not template-cached; these pages rebuild every time.
- If `template` points to a normal `.html` page template instead of `*.tmpl.html`, py-ssg warns because that template will also render as its own standalone page.

## Templates

Templates are Jinja2 HTML files in the `templates/` directory.

- Standard page templates such as `index.html` and `about.html` are rendered and written to `output/` with the same filename.
- Nested page templates such as `templates/blog/index.html` are rendered by default to matching nested output paths like `output/blog/index.html`.
- Render-only templates ending in `*.tmpl.html` are available as template source files, but are never copied to or rendered directly into `output/`.
- The `*.tmpl.html` rule also applies inside nested directories under `templates/`.
- If a frontmatter `template` points at a normal `.html` file instead of `*.tmpl.html`, py-ssg warns because that file will also render as its own standalone page.

### Template Context

All templates receive:

| Variable | Description |
|----------|-------------|
| `site` | Site configuration object (`site.name`, `site.url`, `site.description`, `site.authors`, `site.feeds`) |
| `content` | List of all `MarkdownContent` objects, sorted by `site.content_sort` (default: newest `timestamp` first, undated posts last) |
| `tags` | Mapping of tag name to tuple of matching content items |

### Built-in Helpers

Templates also have these built-in globals and filters:

| Helper | Type | Description |
|--------|------|-------------|
| `post_url(post)` | global | Returns the canonical URL for a content item, such as `/blog/hello-world/` |
| `is_blog_post(post)` | global | Returns `true` when the content file lives under `content/blog/` |
| `asset_url(path)` | global | Appends a build version query string to local output assets such as `/static/styles.css` or `syntax.css` |
| `slug` | filter | Slugifies text by lowercasing it, removing special characters, and replacing spaces with hyphens |
| `date_format` | filter | Formats ISO date or datetime strings with `strftime` syntax, for example `{{ post.timestamp\|date_format('%Y-%m-%d') }}` |
| `excerpt` | filter | Strips HTML, normalizes whitespace, and truncates text with `...` |

### Example Template

```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ site.name }}</title>
  <link rel="stylesheet" href="{{ asset_url('syntax.css') }}">
  <link rel="stylesheet" href="{{ asset_url('/static/styles.css') }}">
</head>
<body>
  <Navbar homeClass="active" />

  <h1>{{ site.name }}</h1>
  <p>{{ site.description }}</p>

  {% for post in content %}
  <article>
    <h2>{{ post.title }}</h2>
    <time>{{ post.timestamp }}</time>
    <span>By {{ post.author.name }}</span>
    {% for tag in post.tags %}
      <span class="tag">{{ tag }}</span>
    {% endfor %}
    {{ post.html }}
    {% if post.toc %}
      <aside>{{ post.toc }}</aside>
    {% endif %}
  </article>
  {% endfor %}

  <Footer />
</body>
</html>
```

Standard Jinja2 features are fully supported: `{% for %}`, `{% if %}`, `{% macro %}`, `{{ variable }}`, filters, etc.

Template note:

- Jinja autoescaping is disabled. Rendered markdown and component output are inserted as plain HTML, so escaping and trust boundaries are your responsibility.

## Components

Components are reusable HTML snippets stored as `.html` files in the `components/` directory. They are automatically discovered at build time.

### Creating a Component

Create a file in `components/` — the filename (without `.html`) becomes the tag name:

**`components/Navbar.html`**
```html
<nav>
  <a href="/" class="{{ homeClass }}">Home</a>
  <a href="/about" class="{{ aboutClass }}">About</a>
</nav>
```

### Using Components

Components support both self-closing tags and open/close tags with child content. Attributes are passed as Jinja2 variables to the component.

```html
<Navbar homeClass="active" aboutClass="" />
```

Renders to:

```html
<nav>
  <a href="/" class="active">Home</a>
  <a href="/about" class="">About</a>
</nav>
```

When a component uses open/close tags, the inner HTML is available inside the component template as `{{ children }}`:

```html
<Card>
  <p>Hello</p>
</Card>
```

**`components/Card.html`**
```html
<div class="card">
  {{ children }}
</div>
```

Nested component directories are also supported. A file such as `components/blog/Card.html` is available as `<blog.Card />`.

### Component Rules

- Components support self-closing syntax such as `<Name />` and open/close syntax such as `<Card>...</Card>`
- Component filenames are **case-sensitive** and must match the tag name exactly
- Components can contain full Jinja2 syntax (conditionals, loops, etc.)
- Components can nest other components, up to **10 levels deep**
- Child content is exposed to the component template through `{{ children }}`
- Components inherit the parent template context, including `site`, `content`, `tags`, `post`, and any other variables already in scope
- Component attributes override parent context variables with the same name
- Attribute values are parsed as literal strings from the rendered HTML; quoted HTML-rich values are supported
- Unknown tags are left untouched in the output

### Example: Conditional Component

**`components/Alert.html`**
```html
<div class="alert alert-{{ type }}">
  {% if title %}<strong>{{ title }}</strong>{% endif %}
  <p>{{ message }}</p>
</div>
```

Usage:
```html
<Alert type="warning" title="Heads up" message="This is a warning." />
```

## Syntax Highlighting

When enabled in configuration, fenced code blocks in markdown are highlighted using [Pygments](https://pygments.org/).

````markdown
```python
def hello():
    print("Hello, world!")
```
````

The build generates an `output/syntax.css` file with dual-theme support using `@media (prefers-color-scheme)`. Link it in your templates:

```html
<link rel="stylesheet" href="{{ asset_url('syntax.css') }}">
```

Any language supported by Pygments can be used. If a language is not recognized, the block falls back to plain text. You can use any valid [Pygments style name](https://pygments.org/styles/) for `theme_light` and `theme_dark`.

## Table of Contents

When enabled, a table of contents is automatically generated from headings in each markdown file.

```toml
[py-ssg.toc]
enabled = true
max_depth = 3    # Include h1 through h3
```

The TOC is available as `post.toc` in templates and renders as:

```html
<nav class="toc">
  <ul>
    <li><a href="#introduction">Introduction</a>
      <ul>
        <li><a href="#getting-started">Getting Started</a></li>
      </ul>
    </li>
  </ul>
</nav>
```

Heading IDs are slugified: lowercased, special characters removed, spaces replaced with hyphens.

## RSS Feeds

Configure one or more RSS feeds in `py-ssg.toml`. Each feed generates an RSS 2.0 XML file in the output directory.

```toml
[[py-ssg.feeds]]
title = "My Blog"
description = "All posts"
output = "feed.xml"

[[py-ssg.feeds]]
title = "Python Posts"
description = "Python-tagged posts only"
output = "python.xml"
tags = ["python"]
```

Feed items include title, link (derived from `post.url`), description (full HTML), publication date (RFC 2822), and author. Items are sorted newest-first. When `tags` is specified, only posts with at least one matching tag are included.

Notes:

- Feed links and template-facing URLs use the same canonical route logic.
- If `site.url` is empty, feed links become relative-looking values rooted at `/`.

## Build Hooks

Create a `pyssg_build.py` file in your project root to hook into the build pipeline. Define any of these functions:

```python
def before_build(context):
    """After config and cache are loaded, before anything else."""
    print(f"Building: {context.config.name}")

def before_markdown_parsing(context):
    """Before markdown files are read and parsed.

    Good for dynamically creating or modifying files in content/.
    """
    pass

def before_component_parsing(context):
    """After markdown parsing, before template rendering.

    context.content is available with all parsed entries.
    """
    print(f"Parsed {len(context.content)} entries")

def after_build(context):
    """After the full build completes.

    Good for post-processing and sitemaps.
    """
    pass
```

### Build Context

The `context` argument (`BuildContext`) provides:

| Property | Type | Description |
|----------|------|-------------|
| `context.config` | `SiteConfig` | Loaded configuration |
| `context.cache` | `BuildCache` | Build cache instance |
| `context.project_dir` | `Path` | Project root |
| `context.templates_dir` | `Path` | Path to `templates/` |
| `context.components_dir` | `Path` | Path to `components/` |
| `context.output_dir` | `Path` | Path to `output/` |
| `context.content` | `MarkdownCollection` | Parsed content (`None` before `before_component_parsing`) |

See [pyssg_build.example.py](/Users/lucasqueiroz/Documents/projects/freeoss-space/py-ssg/pyssg_build.example.py:1) for a complete example.

## Build Caching

When `cache = true` (default), py-ssg stores cache data in `.pyssg_cache.json`.

What is cached:

- Parsed markdown content, keyed by the raw file contents plus syntax and TOC configuration
- Static page templates whose source text has not changed

What is not cached:

- Templates containing dynamic Jinja2 constructs such as `for`, `if`, `macro`, or `callblock`
- Content-generated pages from frontmatter `template`

Notes:

- Disabling cache with `cache = false` turns off both template and markdown-content cache usage.
- Cache keys are based on source content, not dependency tracking between templates and content. If a static template reads `content`, the template cache still only considers the template file itself.

## Performance

- **Parallel markdown parsing**: Uses `ProcessPoolExecutor` with one worker per CPU core. Each worker initializes syntax highlighting and TOC generation once, then processes multiple files.
- **Component caching**: Parsed component templates are cached in memory during a build.
- **Incremental builds**: Only changed templates are re-rendered (see Build Caching).

## Dependencies

| Package | Purpose |
|---------|---------|
| [Jinja2](https://jinja.palletsprojects.com/) | Template engine |
| [mistune](https://mistune.lepture.com/) | Markdown parser |
| [Pygments](https://pygments.org/) | Syntax highlighting |
| [python-frontmatter](https://python-frontmatter.readthedocs.io/) | YAML frontmatter parsing |
| [PyYAML](https://pyyaml.org/) | YAML support |
| [Rich](https://rich.readthedocs.io/) | Terminal output formatting |
| [Typer](https://typer.tiangolo.com/) | CLI framework |
| [watchdog](https://python-watchdog.readthedocs.io/) | File system monitoring |

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
pytest

# Lint
ruff check .
```
