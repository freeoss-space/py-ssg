"""Tests for project initialization."""

from pathlib import Path

from py_ssg.init import init_project


def test_init_creates_structure(tmp_path: Path) -> None:
    target = tmp_path / "mysite"
    init_project(target)

    assert (target / "index.html").exists()
    assert (target / "style.css").exists()
    assert (target / "components" / "navbar.html").exists()


def test_init_in_existing_dir(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    init_project(tmp_path)
    assert (tmp_path / "index.html").exists()


def test_init_index_has_partial(tmp_path: Path) -> None:
    init_project(tmp_path)
    content = (tmp_path / "index.html").read_text()
    assert "<partial" in content
    assert 'src="components/navbar.html"' in content
