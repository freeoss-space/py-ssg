from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from pyssg.commands.new import NewCommand
from pyssg.modules.config import SiteConfig

TEST_PATH = "pyssg.commands.new"


@patch(f"{TEST_PATH}.datetime")
def test_execute_creates_new_content_file_in_sub_folder(
    mock_datetime: MagicMock, tmp_path: Path
) -> None:
    mock_datetime.now.return_value = datetime(2025, 1, 15, 12, 30, 0)
    (tmp_path / "content").mkdir()
    command = NewCommand(title="Post Title", sub_folder="blog")

    with patch(f"{TEST_PATH}.Path.cwd", return_value=tmp_path):
        command.execute()

    created = tmp_path / "content" / "blog" / "post_title.md"
    assert created.is_file()
    assert created.read_text(encoding="utf-8") == (
        '---\ntitle: "Post Title"\ntimestamp: "2025-01-15"\n---\n\n'
    )


@patch(f"{TEST_PATH}.datetime")
@patch(f"{TEST_PATH}.SiteConfig")
def test_execute_uses_default_sub_folder_from_config(
    mock_config_cls: MagicMock,
    mock_datetime: MagicMock,
    tmp_path: Path,
) -> None:
    mock_datetime.now.return_value = datetime(2025, 1, 15, 12, 30, 0)
    (tmp_path / "content").mkdir()
    mock_config_cls.load.return_value = SiteConfig(new_content_subfolder="notes")
    command = NewCommand(title="Post Title")

    with patch(f"{TEST_PATH}.Path.cwd", return_value=tmp_path):
        command.execute()

    assert (tmp_path / "content" / "notes" / "post_title.md").is_file()


@patch(f"{TEST_PATH}.datetime")
def test_execute_dry_run_does_not_write_file(
    mock_datetime: MagicMock, tmp_path: Path
) -> None:
    mock_datetime.now.return_value = datetime(2025, 1, 15, 12, 30, 0)
    (tmp_path / "content").mkdir()
    command = NewCommand(title="Post Title", sub_folder="blog", dry_run=True)

    with patch(f"{TEST_PATH}.Path.cwd", return_value=tmp_path):
        command.execute()

    assert not (tmp_path / "content" / "blog" / "post_title.md").exists()


@patch.object(NewCommand, "_warning")
def test_execute_warns_and_skips_when_file_exists(
    mock_warning: MagicMock, tmp_path: Path
) -> None:
    content_dir = tmp_path / "content" / "blog"
    content_dir.mkdir(parents=True)
    existing = content_dir / "post_title.md"
    existing.write_text("existing", encoding="utf-8")
    command = NewCommand(title="Post Title", sub_folder="blog")

    with patch(f"{TEST_PATH}.Path.cwd", return_value=tmp_path):
        command.execute()

    mock_warning.assert_called_once_with(f"Content file already exists: {existing}")
    assert existing.read_text(encoding="utf-8") == "existing"
