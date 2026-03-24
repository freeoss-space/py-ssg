from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from pyssg.modules.config import SiteConfig
from pyssg.modules.markdown import MarkdownCollection


class RssFeedGenerator:
    def __init__(self, config: SiteConfig):
        self.site_url = config.url.rstrip("/")
        self.feeds = config.feeds

    def _filter_items(self, collection: MarkdownCollection, feed) -> list:
        items = list(collection)
        if feed.tags:
            tag_set = set(feed.tags)
            items = [item for item in items if tag_set.intersection(item.tags)]
        items.sort(key=lambda x: x.timestamp, reverse=True)
        return items

    def _build_feed(self, feed, collection: MarkdownCollection) -> str:
        rss = Element("rss", version="2.0")
        channel = SubElement(rss, "channel")
        SubElement(channel, "title").text = feed.title
        SubElement(channel, "link").text = self.site_url
        SubElement(channel, "description").text = feed.description

        items = self._filter_items(collection, feed)

        for content in items:
            item = SubElement(channel, "item")
            SubElement(item, "title").text = content.title

            slug = content.filename.removesuffix(".md")
            SubElement(item, "link").text = f"{self.site_url}/{slug}"
            SubElement(item, "guid").text = f"{self.site_url}/{slug}"

            SubElement(item, "description").text = content.html

            if content.timestamp:
                try:
                    dt = datetime.fromisoformat(content.timestamp)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    SubElement(item, "pubDate").text = format_datetime(dt)
                except ValueError:
                    pass

            if content.author.name:
                author_text = content.author.name
                if content.author.email:
                    author_text = f"{content.author.email} ({content.author.name})"
                SubElement(item, "author").text = author_text

        xml_bytes = tostring(rss, encoding="unicode", xml_declaration=False)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes

    def generate(self, collection: MarkdownCollection) -> list[tuple[str, str]]:
        results = []
        for feed in self.feeds:
            xml = self._build_feed(feed, collection)
            results.append((feed.output, xml))
        return results
