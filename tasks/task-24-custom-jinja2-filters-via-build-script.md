# Task 24: Custom Jinja2 Filters via Build Script


**What it is**

Expose the `jinja2.Environment` object through `BuildContext`, allowing `pyssg_build.py` to register custom filters and global functions before templates are rendered.

```python
# pyssg_build.py
def before_build(context):
    context.jinja_env.filters["slugify"] = lambda s: s.lower().replace(" ", "-")
    context.jinja_env.globals["current_year"] = datetime.now().year
```

Template usage:

```html
<a href="/{{ post.title|slugify }}">{{ post.title }}</a>
<footer>© {{ current_year }}</footer>
```

**Why it's a good improvement**

Power users who need custom template logic currently have no clean hook to register Jinja2 filters. They must fork the project or use ugly workarounds. Exposing `jinja_env` through the build context unlocks this without any architecture change — the `Environment` already exists.

**Implementation plan**

Add `jinja_env: Environment` to `BuildContext`:

```python
@dataclass
class BuildContext:
    ...
    jinja_env: Environment
```

Pass the `HtmlTemplateEngine`'s environment instance into `BuildContext` before `before_build` is called. In `HtmlTemplateEngine`, expose `self.env` as a public attribute.

Call `build_script.before_build(context)` *after* the engine is constructed so the environment is available.

**Possible downsides**

- Users overwriting built-in filters (like `sort_by_date`) could break their own templates. Document the precedence rules.
- Exposing the `Environment` is a semi-stable API; changes to `HtmlTemplateEngine` internals could break build scripts. Mark it as the public API and commit to it.

**Confidence: 88%** — Major power-user unlock; the plumbing is already there; just needs to be exposed.
