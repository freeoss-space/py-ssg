# Task 5: WebSocket Live-Reload


**What it is**

After a rebuild completes, the dev server sends a reload signal to all connected browsers. A small `<script>` snippet is injected into every served `.html` response that opens a Server-Sent Events (SSE) connection. When the connection receives a `"reload"` message the script calls `location.reload()`.

SSE is chosen over WebSockets because it uses stdlib `http.server` with no extra thread management and a single persistent GET connection per browser tab.

**Why it's a good improvement**

Currently, developers must manually refresh the browser after every change. Live-reload is the industry standard for static site dev servers (Eleventy, Hugo, Vite, Jekyll all have it). It eliminates the most repetitive action in the edit→save→view loop.

**Implementation plan**

Add an SSE endpoint in `Server`:

```python
class Server:
    def __init__(self, directory, port):
        ...
        self._reload_clients: list = []

    def notify_reload(self) -> None:
        for q in list(self._reload_clients):
            q.put("reload")

    # In the request handler:
    def do_GET(self):
        if self.path == "/__reload__":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            q = queue.Queue()
            self.server._reload_clients.append(q)
            try:
                while True:
                    msg = q.get()
                    self.wfile.write(f"data: {msg}\n\n".encode())
                    self.wfile.flush()
            except Exception:
                self.server._reload_clients.remove(q)
            return
        # inject snippet before </body>
        ...
```

Injected snippet (appended to every `.html` response):

```html
<script>
  new EventSource("/__reload__").onmessage = () => location.reload();
</script>
```

Call `server.notify_reload()` at the end of `ServeCommand._rebuild()`.

**Possible downsides**

- The snippet pollutes production builds if users accidentally build with serve-mode artifacts. The snippet should only be injected by the server at serve time, never written to disk.
- Concurrent SSE client management needs thread safety (use `threading.Lock` around `_reload_clients`).

**Confidence: 88%** — Major DX win; SSE is simpler than WebSockets; no new dependencies needed.
