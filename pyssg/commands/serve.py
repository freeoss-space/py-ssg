import time
from pathlib import Path

from pyssg.commands.base_command import BaseCommand
from pyssg.commands.build import BuildCommand, ProjectDirectory
from pyssg.modules.config import SiteConfig
from pyssg.modules.server import Server
from pyssg.modules.watcher import Watcher


class ServeCommand(BaseCommand):
    def __init__(
        self,
        port: int | None = None,
        *,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> None:
        super().__init__(verbose=verbose, dry_run=dry_run)
        self._port = port

    def execute(self) -> None:
        project_dir = Path.cwd()

        config = SiteConfig.load(project_dir)
        port = self._port if self._port is not None else config.server.port

        self._info("Running initial build")
        self._rebuild()
        directories = [
            project_dir / ProjectDirectory.CONTENT,
            project_dir / ProjectDirectory.TEMPLATES,
            project_dir / ProjectDirectory.COMPONENTS,
        ]
        static_dir = project_dir / config.static_dir
        if static_dir.exists():
            directories.append(static_dir)
        self._detail(
            f"Watch directories: {', '.join(str(directory) for directory in directories)}"
        )

        if self._dry_run:
            self._success(f"Dry run complete: would serve at http://localhost:{port}")
            self._info("Dry run: watcher was not started")
            return

        server = Server(directory=project_dir / ProjectDirectory.OUTPUT, port=port)
        server.start()
        self._success(f"Serving at http://localhost:{port}")

        watcher = Watcher(
            directories=directories,
            on_change=self._rebuild,
        )
        watcher.start()
        self._info("Watching for changes. Press Ctrl+C to stop")

        try:
            self._wait_forever()
        except KeyboardInterrupt:
            self._info("Shutting down")
            server.stop()
            watcher.stop()

    def _rebuild(self) -> None:
        try:
            build = BuildCommand(verbose=self._verbose, dry_run=self._dry_run)
            build.execute()
        except Exception as e:
            self._error(f"Build failed during rebuild: {e}")

    def _wait_forever(self) -> None:
        while True:
            time.sleep(1)
