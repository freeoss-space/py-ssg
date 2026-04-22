# Task 1: Auto-generate `sitemap.xml`


**What it is**

After the template rendering phase, py-ssg generates a `sitemap.xml` using the XML Sitemap 0.9 protocol. Every markdown content item contributes a `<url>` entry whose `<loc>` is derived from the site URL and the post slug (filename without `.md`). Templates can optionally opt in with a `sitemap: true` frontmatter field; posts with `draft: true` (see idea 2) are excluded automatically. The feature is enabled by default when `site.url` is set, and can be turned off with `sitemap = false` in `py-ssg.toml`.

**Why it's a good improvement**

A sitemap is the baseline for Google/Bing search indexing. Every serious static site needs one. Generating it automatically from the same metadata already in memory (filenames, timestamps) adds zero overhead.

**Implementation plan**

Add a `SitemapGenerator` class in a new `pyssg/modules/sitemap.py`:

```python
from xml.etree.ElementTree import Element, SubElement, tostring
from pyssg.modules.markdown import MarkdownCollection

class SitemapGenerator:
    def __init__(self, site_url: str):
        self.site_url = site_url.rstrip("/")

    def generate(self, collection: MarkdownCollection) -> str:
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for item in collection:
            # skip drafts automatically
            if getattr(item.custom_fields, "draft", False):
                continue
            url_el = SubElement(urlset, "url")
            slug = item.filename.removesuffix(".md")
            SubElement(url_el, "loc").text = f"{self.site_url}/{slug}"
            if item.timestamp:
                SubElement(url_el, "lastmod").text = item.timestamp
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(urlset, encoding="unicode")
```

Call it in `BuildCommand.execute()` after RSS generation, writing to `output/sitemap.xml`. Add a `sitemap: bool = True` field to `SiteConfig`.

**Possible downsides**

- Sites without `site.url` set will generate sitemaps with relative `<loc>` values, which is invalid per the spec. Guard with a check and emit a warning.

**Confidence: 95%** — Standard, well-defined format; zero new dependencies; trivially extensible.
