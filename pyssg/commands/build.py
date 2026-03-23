from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.modules.markdown import MarkdownParser


class BuildCommand(BaseCommand):
    def execute(self) -> None:
        project_dir = Path.cwd()
        self._info("Parsing markdown files...")
        parser = MarkdownParser(content_dir=project_dir / "content")
        parser.parse()
