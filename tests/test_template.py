"""Tests for the template engine."""

from pathlib import Path

from py_ssg.template import interpolate, parse_attributes, render, resolve_partials


def test_parse_attributes_simple() -> None:
    attrs = parse_attributes(' isActive=true name="hello"')
    assert attrs == {"isActive": "true", "name": "hello"}


def test_parse_attributes_empty() -> None:
    assert parse_attributes("") == {}


def test_interpolate_with_value() -> None:
    result = interpolate("class={{ cls || default }}", {"cls": "active"})
    assert result == "class=active"


def test_interpolate_with_default() -> None:
    result = interpolate("class={{ cls || default }}", {})
    assert result == "class=default"


def test_interpolate_no_default_no_value() -> None:
    result = interpolate("class={{ cls }}", {})
    assert result == "class="


def test_resolve_partials(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "nav.html").write_text('<nav class="{{ active || false }}">Nav</nav>')

    html = '<partial src="components/nav.html" active=true />'
    result = resolve_partials(html, tmp_path)
    assert result == '<nav class="true">Nav</nav>'


def test_render_full_page(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "header.html").write_text("<header>{{ title || My Site }}</header>")

    page = (
        "<!DOCTYPE html><html><body>"
        '<partial src="components/header.html" title="Hello" />'
        "</body></html>"
    )
    result = render(page, tmp_path)
    assert result == "<!DOCTYPE html><html><body><header>Hello</header></body></html>"


def test_nested_partials(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "inner.html").write_text("<span>inner</span>")
    (comp_dir / "outer.html").write_text('<div><partial src="components/inner.html" /></div>')

    html = '<partial src="components/outer.html" />'
    result = render(html, tmp_path)
    assert result == "<div><span>inner</span></div>"


def test_missing_partial_raises(tmp_path: Path) -> None:
    import pytest

    html = '<partial src="components/missing.html" />'
    with pytest.raises(FileNotFoundError):
        render(html, tmp_path)


def test_multiple_partials(tmp_path: Path) -> None:
    comp_dir = tmp_path / "components"
    comp_dir.mkdir()
    (comp_dir / "a.html").write_text("<a>A</a>")
    (comp_dir / "b.html").write_text("<b>B</b>")

    html = '<partial src="components/a.html" /><partial src="components/b.html" />'
    result = render(html, tmp_path)
    assert result == "<a>A</a><b>B</b>"
