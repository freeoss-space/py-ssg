"""
Example build script for py-ssg.

Place a file named `pyssg_build.py` in your project root to hook into
the build pipeline. Define any of the functions below to run custom
logic at each stage.

The `context` argument (BuildContext) exposes:
    - context.config        SiteConfig loaded from py-ssg.toml
    - context.cache         BuildCache instance
    - context.project_dir   Path to the project root
    - context.templates_dir Path to the templates/ directory
    - context.components_dir Path to the components/ directory
    - context.output_dir    Path to the output/ directory
    - context.content       MarkdownCollection (None before parsing)
"""


def before_build(context):
    """Called before the build starts, after config and cache are loaded.

    Useful for modifying config, setting up external resources, or
    generating content files before the build begins.
    """
    print(f"Starting build for: {context.config.name}")


def before_markdown_parsing(context):
    """Called before markdown files are parsed.

    Useful for dynamically creating or modifying markdown files in the
    content/ directory before they are read and parsed.
    """
    print(f"Parsing markdown from: {context.project_dir / 'content'}")


def before_component_parsing(context):
    """Called after markdown parsing and before template rendering.

    context.content is available here with all parsed markdown entries.
    Useful for inspecting or modifying the parsed content before
    templates are rendered.
    """
    if context.content:
        print(f"Parsed {len(context.content)} content entries")


def after_build(context):
    """Called after the build completes (templates rendered, cache saved).

    Useful for post-processing output files, generating sitemaps,
    copying static assets, or notifying external services.
    """
    print(f"Build complete. Output at: {context.output_dir}")
