import re
from datetime import datetime
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.config import SiteConfig

_FILENAME_STRIP_RE = re.compile(r"[^\w\s-]")
_FILENAME_SPACE_RE = re.compile(r"[\s-]+")


def _slugify_filename(title: str) -> str:
    lowered = title.strip().lower()
    stripped = _FILENAME_STRIP_RE.sub("", lowered)
    normalized = _FILENAME_SPACE_RE.sub("_", stripped).strip("_")
    return normalized or "untitled"


class NewCommand(BaseCommand):
    def __init__(
        self,
        title: str,
        sub_folder: str | None = None,
        *,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        super().__init__(verbose=verbose, dry_run=dry_run)
        self.title = title
        self.sub_folder = sub_folder

    def _resolve_sub_folder(self, config: SiteConfig) -> str:
        if self.sub_folder is not None:
            return self.sub_folder.strip("/\\")
        return config.new_content_subfolder.strip("/\\")

    def _target_file(self, project_dir: Path, config: SiteConfig) -> Path:
        content_dir = project_dir / "content"
        sub_folder = self._resolve_sub_folder(config)
        if sub_folder == "":
            target_dir = content_dir
        else:
            target_dir = content_dir / Path(sub_folder)
        return target_dir / f"{_slugify_filename(self.title)}.md"

    def _file_contents(self) -> str:
        timestamp = datetime.now().date().isoformat()
        return f'---\ntitle: "{self.title}"\ntimestamp: "{timestamp}"\n---\n\n'

    def execute(self) -> None:
        project_dir = Path.cwd()
        config = SiteConfig.load(project_dir)
        target_file = self._target_file(project_dir, config)

        if target_file.exists():
            self._warning(f"Content file already exists: {target_file}")
            return

        if self._dry_run:
            self._info(f"Dry run: would create content file {target_file}")
            return

        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(self._file_contents(), encoding="utf-8")
        self._success(f"Created content file: {target_file}")
