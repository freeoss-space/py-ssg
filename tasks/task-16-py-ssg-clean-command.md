# Task 16: `py-ssg clean` Command


**What it is**

`py-ssg clean` deletes the `output/` directory and the `.pyssg_cache.json` file. Useful when: a template file was deleted (stale output file remains), a post was renamed (old slug file persists), or after switching between site configurations.

**Why it's a good improvement**

Without `clean`, stale files from deleted templates or renamed posts silently remain in `output/`. Users discover this only when they deploy and see old pages still live. A clean command is the standard solution and rounds out the toolset (`init`, `build`, `serve`, `clean`).

**Implementation plan**

Add a `CleanCommand` in `pyssg/commands/clean.py`:

```python
class CleanCommand(BaseCommand):
    def execute(self) -> None:
        project_dir = Path.cwd()
        output_dir = project_dir / "output"
        cache_path = project_dir / ".pyssg_cache.json"
        if output_dir.exists():
            shutil.rmtree(output_dir)
            self._success("Removed output/")
        if cache_path.exists():
            cache_path.unlink()
            self._success("Removed .pyssg_cache.json")
```

Register in `main.py`:

```python
@app.command()
def clean() -> None:
    CleanCommand().execute()
```

Optionally add `--output-only` and `--cache-only` flags.

**Possible downsides**

- Accidental `py-ssg clean` in the wrong directory. The command should only operate in a directory that contains `py-ssg.toml` — add a guard check.

**Confidence: 96%** — Essential maintenance command; trivial to implement safely.
