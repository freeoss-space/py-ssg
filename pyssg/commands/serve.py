import time
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.commands.build import BuildCommand
from pyssg.modules.config import SiteConfig
from pyssg.modules.server import Server
from pyssg.modules.watcher import Watcher


class ServeCommand(BaseCommand):
    def __init__(self, port: int | None = None) -> None:
        self._port = port

    def execute(self) -> None:
        project_dir = Path.cwd()

        config = SiteConfig.load(project_dir)
        port = self._port if self._port is not None else config.server.port

        self._info("Running initial build...")
        self._rebuild()

        server = Server(directory=project_dir / "output", port=port)
        server.start()
        self._success(f"Serving on http://localhost:{port}")

        watcher = Watcher(
            directories=[
                project_dir / "content",
                project_dir / "templates",
                project_dir / "components",
            ],
            on_change=self._rebuild,
        )
        watcher.start()
        self._info("Watching for changes... (press Ctrl+C to stop)")

        try:
            self._wait_forever()
        except KeyboardInterrupt:
            self._info("Shutting down...")
            server.stop()
            watcher.stop()

    def _rebuild(self) -> None:
        try:
            build = BuildCommand()
            build.execute()
        except Exception as e:
            self._error(f"Build failed: {e}")

    def _wait_forever(self) -> None:
        while True:
            time.sleep(1)
