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
    def __init__(self, folder_name: str):
        self.folder_name = folder_name

    def _create_folder(self) -> bool:
        new_folder = Path.cwd() / self.folder_name
        if not os.path.exists(new_folder):
            os.mkdir(new_folder)
            self._info(f"Created folder: {self.folder_name}")
            return True
        self._warning(f"Folder already exists: {self.folder_name}")
        return False

    def _init_structure(self, folder: Path) -> None:
        if os.path.isfile(folder / CONFIG_FILENAME):
            self._error("Configuration files already exist!")
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
