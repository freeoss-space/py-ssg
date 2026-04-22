# Task 13: Richer Build Error Reporting


**What it is**

Replace raw Python tracebacks for template/component errors with structured, user-friendly messages that identify the problematic file, the line number, and the error message. Jinja2 already provides `TemplateSyntaxError` and `TemplateError` with filename and line number metadata.

**Why it's a good improvement**

A new user who makes a typo in a template today sees:

```
jinja2.exceptions.TemplateSyntaxError: unexpected char '%' at 42
```

With proper error reporting they see:

```
✗ Syntax error in templates/index.html (line 42):
  unexpected char '%'
```

This is the difference between a beginner giving up and figuring it out in 30 seconds.

**Implementation plan**

Wrap the render step in `BuildCommand.execute()`:

```python
try:
    rendered = engine.render(template, context={"content": list(collection)})
except TemplateSyntaxError as e:
    self._error(f"Syntax error in templates/{filename} (line {e.lineno}):\n  {e.message}")
    continue
except TemplateError as e:
    self._error(f"Render error in templates/{filename}:\n  {e.message}")
    continue
```

Add a similar try/except in `HtmlTemplateEngine._get_component()` with component filename context.

**Possible downsides**

- Swallowing errors and `continue`-ing means a broken template doesn't abort the build. This is arguably the right behaviour for `serve` mode but wrong for `build` mode. Use `--strict` flag to control.

**Confidence: 94%** — Pure DX improvement; Jinja2's error objects already carry all the needed metadata.
