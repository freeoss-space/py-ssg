# Task 23: `extra` Table in Config for User-Defined Template Variables


**What it is**

An `[py-ssg.extra]` TOML table whose key-value pairs are forwarded to all templates as `site.extra.<key>`. Users can store arbitrary site-level values (analytics IDs, social handles, locale, theme colour) without touching Python.

```toml
[py-ssg.extra]
analytics_id = "G-XXXXXXXXXX"
twitter = "@myhandle"
locale = "en-US"
```

Template usage:

```html
<meta name="twitter:site" content="{{ site.extra.twitter }}">
```

**Why it's a good improvement**

Every non-trivial site has site-wide variables that don't fit into `name`, `url`, or `description`. Today users must either hardcode these in templates or maintain a build hook that injects them. An `extra` dict is the clean, established solution (used by Hugo, MkDocs, Jekyll).

**Implementation plan**

Add `extra: SimpleNamespace` to `SiteConfig`:

```python
@dataclass
class SiteConfig:
    ...
    extra: SimpleNamespace = field(default_factory=SimpleNamespace)

    @classmethod
    def from_dict(cls, data: dict) -> SiteConfig:
        extra_data = data.get("extra", {})
        extra = SimpleNamespace(**extra_data)
        return cls(..., extra=extra)
```

**Possible downsides**

- Key names in `extra` could shadow built-in `SiteConfig` attribute names if the user accesses `site` as a dict. Since we use `SimpleNamespace` on a sub-object, there is no collision.

**Confidence: 94%** — Zero complexity; eliminates a daily workaround for every advanced user.
