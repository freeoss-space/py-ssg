from pathlib import Path
from unittest.mock import MagicMock, patch

from pyssg.commands.serve import ServeCommand
from pyssg.modules.config import ServerConfig, SiteConfig

TEST_PATH = "pyssg.commands.serve"


def _default_config(**overrides):
    return SiteConfig(
        server=overrides.get("server", ServerConfig()),
    )


class TestInit:
    def test_stores_port(self):
        command = ServeCommand(port=9000)
        assert command._port == 9000

    def test_default_port_is_none(self):
        command = ServeCommand()
        assert command._port is None


class TestExecute:
    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.Watcher")
    @patch(f"{TEST_PATH}.Server")
    @patch(f"{TEST_PATH}.BuildCommand")
    @patch(f"{TEST_PATH}.Path")
    def test_runs_initial_build(
        self,
        mock_path,
        mock_build_cls,
        mock_server_cls,
        mock_watcher_cls,
        mock_config_cls,
    ):
        mock_path.cwd.return_value = Path("/project")
        mock_config_cls.load.return_value = _default_config()
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_watcher = MagicMock()
        mock_watcher_cls.return_value = mock_watcher
        command = ServeCommand(port=8000)

        with patch.object(command, "_wait_forever", side_effect=KeyboardInterrupt):
            command.execute()

        mock_build_cls.return_value.execute.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.Watcher")
    @patch(f"{TEST_PATH}.Server")
    @patch(f"{TEST_PATH}.BuildCommand")
    @patch(f"{TEST_PATH}.Path")
    def test_starts_server_with_cli_port_override(
        self,
        mock_path,
        mock_build_cls,
        mock_server_cls,
        mock_watcher_cls,
        mock_config_cls,
    ):
        mock_path.cwd.return_value = Path("/project")
        mock_config_cls.load.return_value = _default_config(
            server=ServerConfig(port=3000)
        )
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_watcher = MagicMock()
        mock_watcher_cls.return_value = mock_watcher
        command = ServeCommand(port=9000)

        with patch.object(command, "_wait_forever", side_effect=KeyboardInterrupt):
            command.execute()

        mock_server_cls.assert_called_once_with(
            directory=Path("/project/output"), port=9000
        )

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.Watcher")
    @patch(f"{TEST_PATH}.Server")
    @patch(f"{TEST_PATH}.BuildCommand")
    @patch(f"{TEST_PATH}.Path")
    def test_uses_config_port_when_no_cli_port(
        self,
        mock_path,
        mock_build_cls,
        mock_server_cls,
        mock_watcher_cls,
        mock_config_cls,
    ):
        mock_path.cwd.return_value = Path("/project")
        mock_config_cls.load.return_value = _default_config(
            server=ServerConfig(port=3000)
        )
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_watcher = MagicMock()
        mock_watcher_cls.return_value = mock_watcher
        command = ServeCommand()

        with patch.object(command, "_wait_forever", side_effect=KeyboardInterrupt):
            command.execute()

        mock_server_cls.assert_called_once_with(
            directory=Path("/project/output"), port=3000
        )

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.Watcher")
    @patch(f"{TEST_PATH}.Server")
    @patch(f"{TEST_PATH}.BuildCommand")
    @patch(f"{TEST_PATH}.Path")
    def test_starts_watcher_on_source_directories(
        self,
        mock_path,
        mock_build_cls,
        mock_server_cls,
        mock_watcher_cls,
        mock_config_cls,
    ):
        mock_path.cwd.return_value = Path("/project")
        mock_config_cls.load.return_value = _default_config()
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_watcher = MagicMock()
        mock_watcher_cls.return_value = mock_watcher
        command = ServeCommand(port=8000)

        with patch.object(command, "_wait_forever", side_effect=KeyboardInterrupt):
            command.execute()

        watcher_call = mock_watcher_cls.call_args
        directories = watcher_call.kwargs["directories"]
        assert Path("/project/content") in directories
        assert Path("/project/templates") in directories
        assert Path("/project/components") in directories
        mock_watcher.start.assert_called_once()

    @patch(f"{TEST_PATH}.SiteConfig")
    @patch(f"{TEST_PATH}.Watcher")
    @patch(f"{TEST_PATH}.Server")
    @patch(f"{TEST_PATH}.BuildCommand")
    @patch(f"{TEST_PATH}.Path")
    def test_stops_server_and_watcher_on_keyboard_interrupt(
        self,
        mock_path,
        mock_build_cls,
        mock_server_cls,
        mock_watcher_cls,
        mock_config_cls,
    ):
        mock_path.cwd.return_value = Path("/project")
        mock_config_cls.load.return_value = _default_config()
        mock_server = MagicMock()
        mock_server_cls.return_value = mock_server
        mock_watcher = MagicMock()
        mock_watcher_cls.return_value = mock_watcher
        command = ServeCommand(port=8000)

        with patch.object(command, "_wait_forever", side_effect=KeyboardInterrupt):
            command.execute()

        mock_server.stop.assert_called_once()
        mock_watcher.stop.assert_called_once()


class TestRebuild:
    @patch(f"{TEST_PATH}.BuildCommand")
    def test_executes_build_command(self, mock_build_cls):
        command = ServeCommand(port=8000)

        command._rebuild()

        mock_build_cls.return_value.execute.assert_called_once()

    @patch(f"{TEST_PATH}.BuildCommand")
    def test_catches_exceptions_during_rebuild(self, mock_build_cls):
        mock_build_cls.return_value.execute.side_effect = Exception("build error")
        command = ServeCommand(port=8000)

        command._rebuild()
