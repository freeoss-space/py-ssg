# Task 11: Watcher Debouncing


**What it is**

Most editors write a file in two events: a truncation followed by a content write, sometimes also firing a `modified` and a `moved` event. Without debouncing, a single save triggers 2–4 `_rebuild()` calls within milliseconds. Adding a 300 ms debounce collapses these into one rebuild.

**Why it's a good improvement**

Multiple near-simultaneous rebuilds cause race conditions (two processes writing to the same output file), wasted CPU, and confusing terminal output with interleaved log lines.

**Implementation plan**

```python
import threading

class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change, debounce_seconds=0.3):
        self._on_change = on_change
        self._debounce = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._on_change)
            self._timer.start()
```

**Possible downsides**

- The 300 ms delay means the rebuild starts slightly later after a save. This is imperceptible to humans and a fair trade for correctness.

**Confidence: 97%** — Standard pattern; solves a real race condition with trivial code.
