import logging
import os
import shutil
from importlib.resources import files
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.cache import BuildCache
from pyssg.modules.config import CONFIG_FILENAME

CURRENT_FOLDER_NAME = "."
logger = logging.getLogger(__name__)


class InitCommand(BaseCommand):
    def __init__(
        self,
        folder_name: str,
        *,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        super().__init__(verbose=verbose, dry_run=dry_run)
        self.folder_name = folder_name

    def _create_folder(self) -> bool:
        new_folder = Path.cwd() / self.folder_name
        if not os.path.exists(new_folder):
            if self._dry_run:
                self._info(f"Dry run: would create folder {new_folder}")
                return True
            os.mkdir(new_folder)
            self._info(f"Created folder: {self.folder_name}")
            return True
        self._warning(f"Folder already exists: {self.folder_name}")
        return False

    def _init_structure(self, folder: Path) -> None:
        if os.path.isfile(folder / CONFIG_FILENAME):
            self._error("Configuration files already exist!")
            return

        if self._dry_run:
            self._info(f"Dry run: would create project structure in {folder}")
            self._detail(f"Would create: {folder / 'content'}")
            self._detail(f"Would create: {folder / 'templates'}")
            self._detail(f"Would create: {folder / 'components'}")
            self._detail(f"Would create: {folder / 'output'}")
            self._detail(f"Would copy: {folder / CONFIG_FILENAME}")
            self._detail(f"Would create cache in: {folder}")
            self._success(f"Dry run complete: would initialize structure in {folder}")
            return

        os.mkdir(folder / "content")
        os.mkdir(folder / "templates")
        os.mkdir(folder / "components")
        os.mkdir(folder / "output")

        shutil.copy2(
            Path(str(files("pyssg") / "templates" / CONFIG_FILENAME)),
            folder / CONFIG_FILENAME,
        )
        BuildCache.create(cache_dir=folder)
        self._success(f"Initialized structure in: {folder}")

    def execute(self) -> None:
        if self.folder_name == CURRENT_FOLDER_NAME:
            project_path = Path.cwd()
        else:
            created_folder = self._create_folder()
            if not created_folder:
                return
            project_path = Path.cwd() / self.folder_name
        self._info(f"Initializing structure in: {project_path}")
        self._init_structure(folder=project_path)
