from pathlib import Path
from unittest.mock import MagicMock, patch

from pyssg.modules.server import Server

TEST_PATH = "pyssg.modules.server"


class TestInit:
    def test_stores_port(self):
        server = Server(directory=Path("/output"), port=9000)
        assert server._port == 9000

    def test_stores_directory(self):
        server = Server(directory=Path("/output"), port=9000)
        assert server._directory == Path("/output")

    def test_default_port(self):
        server = Server(directory=Path("/output"))
        assert server._port == 8000


class TestStart:
    @patch(f"{TEST_PATH}.HTTPServer")
    @patch(f"{TEST_PATH}.Thread")
    def test_creates_http_server_with_port(self, mock_thread_cls, mock_http_server_cls):
        server = Server(directory=Path("/output"), port=9000)

        server.start()

        mock_http_server_cls.assert_called_once()
        address = mock_http_server_cls.call_args.args[0]
        assert address == ("", 9000)

    @patch(f"{TEST_PATH}.HTTPServer")
    @patch(f"{TEST_PATH}.Thread")
    def test_starts_server_in_daemon_thread(
        self, mock_thread_cls, mock_http_server_cls
    ):
        server = Server(directory=Path("/output"), port=8000)
        mock_thread = MagicMock()
        mock_thread_cls.return_value = mock_thread

        server.start()

        mock_thread_cls.assert_called_once()
        assert mock_thread.daemon is True
        mock_thread.start.assert_called_once()

    @patch(f"{TEST_PATH}.HTTPServer")
    @patch(f"{TEST_PATH}.Thread")
    def test_passes_handler_to_http_server(self, mock_thread_cls, mock_http_server_cls):
        server = Server(directory=Path("/output"), port=8000)

        server.start()

        handler = mock_http_server_cls.call_args.args[1]
        assert handler is not None


class TestStop:
    @patch(f"{TEST_PATH}.HTTPServer")
    @patch(f"{TEST_PATH}.Thread")
    def test_shuts_down_server(self, mock_thread_cls, mock_http_server_cls):
        server = Server(directory=Path("/output"), port=8000)
        mock_http_server = MagicMock()
        mock_http_server_cls.return_value = mock_http_server

        server.start()
        server.stop()

        mock_http_server.shutdown.assert_called_once()

    def test_stop_without_start_does_nothing(self):
        server = Server(directory=Path("/output"), port=8000)
        server.stop()
