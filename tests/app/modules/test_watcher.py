from pathlib import Path
from unittest.mock import MagicMock, patch

from pyssg.modules.watcher import Watcher

TEST_PATH = "pyssg.modules.watcher"


class TestInit:
    def test_stores_directories(self):
        dirs = [Path("/content"), Path("/templates")]
        watcher = Watcher(directories=dirs, on_change=lambda: None)
        assert watcher._directories == dirs

    def test_stores_callback(self):
        callback = MagicMock()
        watcher = Watcher(directories=[Path("/content")], on_change=callback)
        assert watcher._on_change is callback


class TestStart:
    @patch(f"{TEST_PATH}.Observer")
    def test_creates_observer(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        watcher = Watcher(directories=[Path("/content")], on_change=lambda: None)

        watcher.start()

        mock_observer_cls.assert_called_once()

    @patch(f"{TEST_PATH}.Observer")
    def test_schedules_each_directory(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        dirs = [Path("/content"), Path("/templates"), Path("/components")]
        watcher = Watcher(directories=dirs, on_change=lambda: None)

        watcher.start()

        assert mock_observer.schedule.call_count == 3

    @patch(f"{TEST_PATH}.Observer")
    def test_schedules_with_recursive_flag(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        watcher = Watcher(directories=[Path("/content")], on_change=lambda: None)

        watcher.start()

        schedule_call = mock_observer.schedule.call_args
        assert schedule_call.kwargs["recursive"] is True

    @patch(f"{TEST_PATH}.Observer")
    def test_starts_observer(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        watcher = Watcher(directories=[Path("/content")], on_change=lambda: None)

        watcher.start()

        mock_observer.start.assert_called_once()


class TestStop:
    @patch(f"{TEST_PATH}.Observer")
    def test_stops_observer(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        watcher = Watcher(directories=[Path("/content")], on_change=lambda: None)

        watcher.start()
        watcher.stop()

        mock_observer.stop.assert_called_once()

    @patch(f"{TEST_PATH}.Observer")
    def test_joins_observer(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        watcher = Watcher(directories=[Path("/content")], on_change=lambda: None)

        watcher.start()
        watcher.stop()

        mock_observer.join.assert_called_once()


class TestOnChangeHandler:
    @patch(f"{TEST_PATH}.Observer")
    def test_callback_invoked_on_file_event(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        callback = MagicMock()
        watcher = Watcher(directories=[Path("/content")], on_change=callback)

        watcher.start()

        handler = mock_observer.schedule.call_args.args[0]
        event = MagicMock()
        event.is_directory = False
        handler.on_any_event(event)

        callback.assert_called_once()

    @patch(f"{TEST_PATH}.Observer")
    def test_callback_not_invoked_on_directory_event(self, mock_observer_cls):
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer
        callback = MagicMock()
        watcher = Watcher(directories=[Path("/content")], on_change=callback)

        watcher.start()

        handler = mock_observer.schedule.call_args.args[0]
        event = MagicMock()
        event.is_directory = True
        handler.on_any_event(event)

        callback.assert_not_called()
