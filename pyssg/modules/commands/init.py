import logging
import os
import shutil
from importlib.resources import files
from pathlib import Path

from pyssg.modules.commands.base_command import BaseCommand

CURRENT_FOLDER_NAME = "."
logger = logging.getLogger(__name__)


class InitCommand(BaseCommand):
    def __init__(self, folder_name: str):
        self.folder_name = folder_name

    def _create_folder(self) -> None:
        new_folder = Path.cwd() / self.folder_name
        if not os.path.exists(new_folder):
            os.mkdir(new_folder)
            logger.info(f"Created folder: {self.folder_name}")
            return
        logger.warning(f"Folder already exists: {self.folder_name}")

    def _init_structure(self, folder: Path) -> None:
        if os.path.isfile(folder / "py-ssg.toml"):
            logger.warning("Config file already exists: py-ssg.toml")
            return

        os.mkdir(folder / "content")
        os.mkdir(folder / "templates")
        os.mkdir(folder / "output")

        shutil.copy2(
            Path(str(files("pyssg") / "templates" / "py-ssg.toml")),
            folder / "py-ssg.toml",
        )
        logger.info(f"Initialized structure in: {folder}")

    def execute(self) -> None:
        if self.folder_name == CURRENT_FOLDER_NAME:
            project_path = Path.cwd()
        else:
            self._create_folder()
            project_path = Path.cwd() / self.folder_name
        self._init_structure(folder=project_path)
