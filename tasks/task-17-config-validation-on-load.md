# Task 17: Config Validation on Load


**What it is**

When `py-ssg.toml` is loaded, validate known fields before the build starts. Specifically:
- Check that `syntax.theme_light` and `syntax.theme_dark` are valid Pygments style names.
- Check that `site.url` is a valid URL when feeds are configured.
- Check that feed `output` filenames don't conflict with template filenames.
- Emit a named `ConfigWarning` (not a crash) for non-critical issues.

**Why it's a good improvement**

Today, an invalid theme name like `"monoke"` causes Pygments to raise an exception deep in the build pipeline with a confusing traceback. Validation surfaces the error immediately with a helpful message like: `"Unknown Pygments theme 'monoke'. Valid themes include: monokai, friendly, …"`.

**Implementation plan**

Add a `validate()` method to `SiteConfig`:

```python
from pygments.styles import get_all_styles

def validate(self) -> list[str]:
    warnings = []
    valid_themes = set(get_all_styles())
    if self.syntax.enabled:
        for attr, name in [("theme_light", self.syntax.theme_light),
                           ("theme_dark", self.syntax.theme_dark)]:
            if name not in valid_themes:
                closest = difflib.get_close_matches(name, valid_themes, n=1)
                hint = f" Did you mean '{closest[0]}'?" if closest else ""
                warnings.append(f"Unknown syntax.{attr} '{name}'.{hint}")
    if self.feeds and not self.url:
        warnings.append("RSS feeds configured but site.url is empty — feed links will be broken.")
    return warnings
```

Call `config.validate()` in `BuildCommand.execute()` and print each warning with `self._warning(...)`.

**Possible downsides**

- Adds a `difflib` import (stdlib). The Pygments import for `get_all_styles` is already a dependency. No new dependencies.

**Confidence: 92%** — Significantly improves the new-user experience at essentially zero cost.
