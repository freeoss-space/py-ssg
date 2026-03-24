import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread


class Server:
    def __init__(self, directory: Path, port: int = 8000) -> None:
        self._directory = directory
        self._port = port
        self._http_server: HTTPServer | None = None

    def start(self) -> None:
        handler = functools.partial(
            SimpleHTTPRequestHandler, directory=str(self._directory)
        )
        self._http_server = HTTPServer(("", self._port), handler)
        thread = Thread(target=self._http_server.serve_forever)
        thread.daemon = True
        thread.start()

    def stop(self) -> None:
        if self._http_server:
            self._http_server.shutdown()
