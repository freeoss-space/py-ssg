"""Tests for the build engine."""

from pathlib import Path

from py_ssg.builder import build


def test_build_creates_output(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<h1>Hello</h1>")
    files = build(tmp_path)
    assert len(files) == 1
    assert (tmp_path / "output" / "index.html").read_text() == "<h1>Hello</h1>"


def test_build_resolves_partials(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "footer.html").write_text("<footer>Footer</footer>")
    (tmp_path / "index.html").write_text('<partial src="components/footer.html" />')

    build(tmp_path)
    assert (tmp_path / "output" / "index.html").read_text() == "<footer>Footer</footer>"


def test_build_copies_static_assets(tmp_path: Path) -> None:
    (tmp_path / "style.css").write_text("body { color: red; }")
    build(tmp_path)
    assert (tmp_path / "output" / "style.css").read_text() == "body { color: red; }"


def test_build_excludes_components_dir(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "nav.html").write_text("<nav>Nav</nav>")
    (tmp_path / "index.html").write_text("<h1>Hi</h1>")

    build(tmp_path)
    assert not (tmp_path / "output" / "components").exists()


def test_build_cleans_output(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "old.html").write_text("old")

    (tmp_path / "index.html").write_text("<h1>New</h1>")
    build(tmp_path)
    assert not (output_dir / "old.html").exists()
    assert (output_dir / "index.html").exists()


def test_build_preserves_subdirectories(tmp_path: Path) -> None:
    blog_dir = tmp_path / "blog"
    blog_dir.mkdir()
    (blog_dir / "post.html").write_text("<h1>Post</h1>")

    build(tmp_path)
    assert (tmp_path / "output" / "blog" / "post.html").read_text() == "<h1>Post</h1>"
