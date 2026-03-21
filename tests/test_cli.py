"""Tests for the CLI."""

from pathlib import Path

from click.testing import CliRunner

from py_ssg.cli import main


def test_init_command(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "testsite"
    result = runner.invoke(main, ["init", str(target)])
    assert result.exit_code == 0
    assert (target / "index.html").exists()


def test_build_command(tmp_path: Path) -> None:
    runner = CliRunner()
    (tmp_path / "index.html").write_text("<h1>Test</h1>")
    result = runner.invoke(main, ["build", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Built" in result.output
    assert (tmp_path / "output" / "index.html").exists()


def test_init_dot(tmp_path: Path, monkeypatch: object) -> None:
    """Test `py-ssg init .` initializes in current directory."""
    import os

    assert isinstance(monkeypatch, object)
    os.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["init", "."])
    assert result.exit_code == 0
    assert (tmp_path / "index.html").exists()
