"""Development server with live reload."""

from __future__ import annotations

import http.server
import socketserver
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from py_ssg.builder import OUTPUT_DIR, build

LIVE_RELOAD_SCRIPT = """
<script>
(function() {
  let lastCheck = Date.now();
  setInterval(async () => {
    try {
      const res = await fetch('/__reload__');
      const data = await res.json();
      if (data.ts > lastCheck) {
        lastCheck = data.ts;
        location.reload();
      }
    } catch {}
  }, 500);
})();
</script>
"""

_reload_ts: float = 0.0


class _ReloadHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that injects live-reload script and serves a reload timestamp."""

    def do_GET(self) -> None:
        if self.path == "/__reload__":
            import json
            import time

            body = json.dumps({"ts": _reload_ts or time.time()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self) -> None:
        if self.path.endswith(".html") or self.path.endswith("/") or "." not in self.path:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def copyfile(self, source: object, outputfile: object) -> None:
        import io

        content_type = self.headers.get("Content-Type", "")
        # Check if we sent an html content type in our response headers
        headers_buffer: list[bytes] = getattr(self, "_headers_buffer", [])
        if headers_buffer:
            header_str = b"".join(headers_buffer).decode(errors="ignore")
            if "text/html" in header_str:
                assert isinstance(source, io.BufferedIOBase)
                data = source.read()
                text = data.decode(errors="ignore")
                if "</body>" in text:
                    text = text.replace("</body>", LIVE_RELOAD_SCRIPT + "</body>")
                elif "</html>" in text:
                    text = text.replace("</html>", LIVE_RELOAD_SCRIPT + "</html>")
                else:
                    text += LIVE_RELOAD_SCRIPT
                encoded = text.encode()
                outputfile.write(encoded)  # type: ignore[union-attr]
                return
        assert not isinstance(content_type, int)
        super().copyfile(source, outputfile)  # type: ignore[arg-type]


class _RebuildHandler(FileSystemEventHandler):
    """Watch for file changes and trigger rebuilds."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def on_any_event(self, event: object) -> None:
        import time

        global _reload_ts
        src = getattr(event, "src_path", "")
        if isinstance(src, str) and OUTPUT_DIR in src:
            return
        try:
            build(self.project_dir)
            _reload_ts = time.time()
        except Exception as e:
            print(f"Build error: {e}")


def serve(project_dir: Path, port: int = 8000) -> None:
    """Build and serve the site with live reload."""
    import time

    global _reload_ts

    build(project_dir)
    _reload_ts = time.time()

    output_dir = project_dir / OUTPUT_DIR

    handler = type(
        "Handler",
        (_ReloadHandler,),
        {
            "__init__": lambda self, *a, **kw: _ReloadHandler.__init__(
                self, *a, directory=str(output_dir), **kw
            )
        },
    )

    observer = Observer()
    event_handler = _RebuildHandler(project_dir)
    observer.schedule(event_handler, str(project_dir), recursive=True)
    observer.start()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at http://localhost:{port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
        finally:
            observer.stop()
            observer.join()
