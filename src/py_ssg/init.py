"""Initialize a new py-ssg project with scaffold files."""

from __future__ import annotations

from pathlib import Path

NAVBAR_HTML = """\
<nav>
  <a href="/">Home</a>
  <a href="/blog">Blog</a>
</nav>
"""

INDEX_HTML = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>My Site</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <partial src="components/navbar.html" />
    <main>
      <h1>Welcome to My Site</h1>
      <p>Edit index.html to get started.</p>
    </main>
  </body>
</html>
"""

STYLE_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; line-height: 1.6; }
body { max-width: 800px; margin: auto; padding: 2rem; }
nav { display: flex; gap: 1rem; margin-bottom: 2rem; }
nav a { text-decoration: none; color: #333; }
nav a:hover { text-decoration: underline; }
h1 { margin-bottom: 1rem; }
"""


def init_project(target: Path) -> None:
    """Create a new py-ssg project scaffold at target."""
    target.mkdir(parents=True, exist_ok=True)

    components = target / "components"
    components.mkdir(exist_ok=True)

    (components / "navbar.html").write_text(NAVBAR_HTML)
    (target / "index.html").write_text(INDEX_HTML)
    (target / "style.css").write_text(STYLE_CSS)

    print(f"Initialized py-ssg project in {target.resolve()}")
