"""CLI entry point for py-ssg."""

from __future__ import annotations

from pathlib import Path

import click


@click.group()
def main() -> None:
    """py-ssg: A simple static site generator with HTML partials."""


@main.command()
@click.argument("directory", default=".")
def init(directory: str) -> None:
    """Initialize a new py-ssg project."""
    from py_ssg.init import init_project

    init_project(Path(directory))


@main.command()
@click.option("--dir", "directory", default=".", help="Project directory")
def build(directory: str) -> None:
    """Build the static site into output/."""
    from py_ssg.builder import build as do_build

    project_dir = Path(directory).resolve()
    files = do_build(project_dir)
    click.echo(f"Built {len(files)} file(s) into output/")


@main.command()
@click.option("--dir", "directory", default=".", help="Project directory")
@click.option("--port", default=8000, help="Port to serve on")
def serve(directory: str, port: int) -> None:
    """Serve the site with live reload."""
    from py_ssg.server import serve as do_serve

    project_dir = Path(directory).resolve()
    do_serve(project_dir, port)
