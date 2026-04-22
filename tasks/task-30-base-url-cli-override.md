# Task 30: `--base-url` CLI Override


**What it is**

`py-ssg build --base-url https://staging.example.com` overrides `site.url` for that build run without modifying `py-ssg.toml`. This is essential for CI/CD pipelines that build to different environments (GitHub Pages sub-path, Netlify preview URLs, staging, production).

**Why it's a good improvement**

Today a CI pipeline deploying to GitHub Pages (`https://user.github.io/repo/`) must either maintain separate `py-ssg.toml` files or use `sed` to patch the URL. An override flag is the clean solution used by virtually all SSG tools.

**Implementation plan**

```python
@app.command()
def build(base_url: str | None = typer.Option(default=None)) -> None:
    BuildCommand(base_url=base_url).execute()
```

```python
class BuildCommand(BaseCommand):
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url

    def execute(self) -> None:
        ...
        config = SiteConfig.load(project_dir)
        if self._base_url:
            config.url = self._base_url
        ...
```

**Possible downsides**

- The flag only affects `site.url`; any config values derived from the URL at load time (e.g., feed links computed on init) must be re-derived after the override. Since `RssFeedGenerator` reads `config.url` at call time, this is already handled correctly.

**Confidence: 91%** — One-liner addition to the CLI that solves a concrete DevOps pain point.
