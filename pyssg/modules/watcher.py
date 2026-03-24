from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[], None]) -> None:
        self._on_change = on_change

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        self._on_change()


class Watcher:
    def __init__(self, directories: list[Path], on_change: Callable[[], None]) -> None:
        self._directories = directories
        self._on_change = on_change
        self._observer: BaseObserver | None = None

    def start(self) -> None:
        self._observer = Observer()
        handler = _ChangeHandler(on_change=self._on_change)
        for directory in self._directories:
            self._observer.schedule(handler, path=str(directory), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
