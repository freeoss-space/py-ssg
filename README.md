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

### `py-ssg init [folder_name]`

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

### `py-ssg build`

Builds the site. Reads markdown from `content/`, renders templates from `templates/`, resolves components from `components/`, and writes the result to `output/`.

The build reports:
- Total files, built files, and cached files
- Component count
- RSS feeds generated
- Parsing, rendering, and total time

### `py-ssg serve [--port PORT]`

Runs an initial build, starts a local HTTP server, and watches for changes. Automatically rebuilds when files in `content/`, `templates/`, or `components/` change.

```bash
py-ssg serve              # Default port 8000
py-ssg serve --port 3000  # Custom port
```

Press `Ctrl+C` for graceful shutdown.

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

When using `static_dir_output = "root"`, avoid filename collisions with generated pages and assets such as `index.html`, `feed.xml`, and `syntax.css` unless you intentionally want the static file to take precedence.

## Markdown Content

Place `.md` files in the `content/` directory. Each file uses YAML frontmatter for metadata.

### Frontmatter Fields

```yaml
---
title: My Post Title
timestamp: "2025-01-15"
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
| `timestamp` | string | Publication date (ISO format) |
| `tags` | list | List of tag strings |
| `author` | string | Author name |
| `author_email` | string | Author email |
| `author_avatar` | string | Author avatar URL |
| `author_url` | string | Author website URL |

**Custom fields:** Any additional YAML keys become accessible via `post.custom_fields`. For example, adding `slug: my-custom-slug` and `draft: true` to frontmatter makes them available as `post.custom_fields.slug` and `post.custom_fields.draft`.

### Parsed Content Object

Each markdown file becomes a `MarkdownContent` object available in templates:

| Property | Description |
|----------|-------------|
| `post.filename` | Path relative to `content/` (e.g., `hello-world.md` or `blog/2025/hello-world.md`) |
| `post.html` | Rendered HTML content |
| `post.title` | Title from frontmatter |
| `post.timestamp` | Timestamp string from frontmatter |
| `post.tags` | List of tag strings |
| `post.author.name` | Author name |
| `post.author.email` | Author email |
| `post.author.avatar` | Author avatar URL |
| `post.author.url` | Author URL |
| `post.custom_fields` | Namespace with any extra frontmatter fields |
| `post.toc` | Generated table of contents HTML (if enabled) |

## Templates

Templates are Jinja2 HTML files in the `templates/` directory.

- Standard page templates such as `index.html` and `about.html` are rendered and written to `output/` with the same filename.
- Render-only templates ending in `*.tmpl.html` are available as template source files, but are never copied to or rendered directly into `output/`.
- The `*.tmpl.html` rule also applies inside nested directories under `templates/`.

### Template Context

All templates receive:

| Variable | Description |
|----------|-------------|
| `site` | Site configuration object (`site.name`, `site.url`, `site.description`, `site.authors`, `site.feeds`) |
| `content` | List of all `MarkdownContent` objects, sorted by `site.content_sort` (default: newest `timestamp` first, undated posts last) |

### Built-in Helpers

Templates also have these built-in globals and filters:

| Helper | Type | Description |
|--------|------|-------------|
| `post_url(post)` | global | Returns the canonical URL for a content item, such as `/blog/hello-world/` |
| `is_blog_post(post)` | global | Returns `true` when the content file lives under `content/blog/` |
| `slug` | filter | Slugifies text by lowercasing it, removing special characters, and replacing spaces with hyphens |
| `date_format` | filter | Formats ISO date or datetime strings with `strftime` syntax, for example `{{ post.timestamp\|date_format('%Y-%m-%d') }}` |
| `excerpt` | filter | Strips HTML, normalizes whitespace, and truncates text with `...` |

### Example Template

```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ site.name }}</title>
  <link rel="stylesheet" href="syntax.css">
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

### Component Rules

- Components support self-closing syntax such as `<Name />` and open/close syntax such as `<Card>...</Card>`
- Component filenames are **case-sensitive** and must match the tag name exactly
- Components can contain full Jinja2 syntax (conditionals, loops, etc.)
- Components can nest other components, up to **10 levels deep**
- Child content is exposed to the component template through `{{ children }}`
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
<link rel="stylesheet" href="syntax.css">
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

Feed items include title, link (derived from filename slug), description (full HTML), publication date (RFC 2822), and author. Items are sorted newest-first. When `tags` is specified, only posts with at least one matching tag are included.

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

See `pyssg_build.example.py` in the repository for a complete example.

## Build Caching

When `cache = true` (default), py-ssg tracks SHA256 hashes of template files and skips rendering unchanged templates. Templates containing dynamic Jinja2 constructs (`for`, `if`, `macro`, `callblock`) are always rebuilt regardless of cache state.

Cache is stored in `.pyssg_cache.json` at the project root.

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
