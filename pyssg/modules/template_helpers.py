import re
from datetime import date, datetime
from pathlib import PurePosixPath

from pyssg.modules.markdown import MarkdownContent

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SLUG_STRIP_RE = re.compile(r"[^\w\s-]")
_SLUG_SPACE_RE = re.compile(r"[\s]+")


def post_url(post: MarkdownContent) -> str:
    return post.url


def is_blog_post(post: MarkdownContent) -> bool:
    return PurePosixPath(post.filename).parts[:1] == ("blog",)


def slug(value: object) -> str:
    text = str(value).lower()
    stripped = _SLUG_STRIP_RE.sub("", text)
    return _SLUG_SPACE_RE.sub("-", stripped).strip("-")


def _parse_datetime_value(value: object) -> date | datetime | None:
    if isinstance(value, datetime | date):
        return value
    if not isinstance(value, str) or value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def date_format(value: object, fmt: str = "%Y-%m-%d") -> str:
    parsed = _parse_datetime_value(value)
    if parsed is None:
        return str(value)
    return parsed.strftime(fmt)


def _normalize_excerpt_text(value: object) -> str:
    without_tags = _HTML_TAG_RE.sub("", str(value))
    return _WHITESPACE_RE.sub(" ", without_tags).strip()


def excerpt(value: object, max_length: int = 160) -> str:
    text = _normalize_excerpt_text(value)
    if max_length < 0 or len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]
    return text[: max_length - 3].rstrip() + "..."
