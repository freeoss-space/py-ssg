# Task 10: Watch `py-ssg.toml` and `pyssg_build.py`


**What it is**

The `ServeCommand` currently watches `content/`, `templates/`, and `components/`. Changing `py-ssg.toml` (e.g., toggling syntax highlighting, adding a feed) or editing `pyssg_build.py` does not trigger a rebuild — a silent bug. The fix adds the config file and build script file to the watched paths.

**Why it's a good improvement**

This is a correctness fix. Users who edit `py-ssg.toml` during development currently see stale output and may not realise the server didn't pick up the change. The fix is a one-liner.

**Implementation plan**

In `ServeCommand.execute()`:

```python
watch_files = [
    project_dir / "content",
    project_dir / "templates",
    project_dir / "components",
]
# Also watch individual files
for f in ["py-ssg.toml", "pyssg_build.py"]:
    p = project_dir / f
    if p.exists():
        watch_files.append(p)
```

The `Watcher` already supports individual file paths via `watchdog`'s `schedule` call with a non-recursive watch.

**Possible downsides**

- `watchdog` emits events for the parent directory when watching a file on some platforms. Use `recursive=False` and filter by filename in the handler.

**Confidence: 99%** — Pure correctness fix. Zero downside.
