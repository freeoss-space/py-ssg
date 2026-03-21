"""Build engine: processes HTML files and copies static assets to output/."""

from __future__ import annotations

import shutil
from pathlib import Path

from py_ssg.template import render

OUTPUT_DIR = "output"
IGNORE_DIRS = {"output", ".venv", "__pycache__", "node_modules", ".git"}


def build(project_dir: Path) -> list[Path]:
    """Build the static site from project_dir into output/.

    Returns a list of output files created.
    """
    output_dir = project_dir / OUTPUT_DIR
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    created: list[Path] = []

    for source_file in _walk_source_files(project_dir):
        rel = source_file.relative_to(project_dir)
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)

        if source_file.suffix == ".html":
            html = source_file.read_text()
            rendered = render(html, project_dir)
            dest.write_text(rendered)
        else:
            shutil.copy2(source_file, dest)

        created.append(dest)

    return created


def _walk_source_files(project_dir: Path) -> list[Path]:
    """Collect all source files, skipping ignored directories."""
    files: list[Path] = []
    for item in sorted(project_dir.rglob("*")):
        if item.is_dir():
            continue
        # Skip files inside ignored directories
        parts = item.relative_to(project_dir).parts
        if any(part in IGNORE_DIRS for part in parts):
            continue
        # Skip component partials (they get inlined)
        if parts[0] == "components":
            continue
        files.append(item)
    return files
