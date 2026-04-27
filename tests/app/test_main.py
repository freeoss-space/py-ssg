from unittest.mock import patch

from typer.testing import CliRunner

from pyssg.main import app

TEST_PATH = "pyssg.main"

runner = CliRunner()


@patch(f"{TEST_PATH}.BuildCommand")
def test_build_passes_verbose_and_dry_run_to_command(mock_build_cls) -> None:
    result = runner.invoke(app, ["build", "--verbose", "--dry-run"])

    assert result.exit_code == 0
    mock_build_cls.assert_called_once_with(verbose=True, dry_run=True)
    mock_build_cls.return_value.execute.assert_called_once_with()


@patch(f"{TEST_PATH}.InitCommand")
def test_init_passes_verbose_and_dry_run_to_command(mock_init_cls) -> None:
    result = runner.invoke(app, ["init", "demo", "--verbose", "--dry-run"])

    assert result.exit_code == 0
    mock_init_cls.assert_called_once_with(
        folder_name="demo",
        verbose=True,
        dry_run=True,
    )
    mock_init_cls.return_value.execute.assert_called_once_with()


@patch(f"{TEST_PATH}.ServeCommand")
def test_serve_passes_port_verbose_and_dry_run_to_command(mock_serve_cls) -> None:
    result = runner.invoke(app, ["serve", "--port", "9000", "--verbose", "--dry-run"])

    assert result.exit_code == 0
    mock_serve_cls.assert_called_once_with(port=9000, verbose=True, dry_run=True)
    mock_serve_cls.return_value.execute.assert_called_once_with()


@patch(f"{TEST_PATH}.NewCommand")
def test_new_passes_title_sub_folder_verbose_and_dry_run_to_command(
    mock_new_cls,
) -> None:
    result = runner.invoke(
        app,
        ["new", "--sub-folder", "blog", "Post Title", "--verbose", "--dry-run"],
    )

    assert result.exit_code == 0
    mock_new_cls.assert_called_once_with(
        title="Post Title",
        sub_folder="blog",
        verbose=True,
        dry_run=True,
    )
    mock_new_cls.return_value.execute.assert_called_once_with()
