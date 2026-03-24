import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = "py-ssg.toml"


@dataclass
class AuthorConfig:
    name: str = ""
    email: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "AuthorConfig":
        return cls(
            name=str(data.get("name", "")),
            email=str(data.get("email", "")),
        )


@dataclass
class FeedConfig:
    title: str = ""
    output: str = "feed.xml"
    description: str = ""
    tags: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "FeedConfig":
        tags = data.get("tags")
        if isinstance(tags, list):
            tags = [str(t) for t in tags]
        return cls(
            title=str(data.get("title", "")),
            output=str(data.get("output", "feed.xml")),
            description=str(data.get("description", "")),
            tags=tags,
        )


@dataclass
class SiteConfig:
    name: str = ""
    url: str = ""
    description: str = ""
    authors: list[AuthorConfig] = field(default_factory=list)
    feeds: list[FeedConfig] = field(default_factory=list)
    cache: bool = True

    @classmethod
    def load(cls, project_dir: Path) -> "SiteConfig":
        config_path = project_dir / CONFIG_FILENAME
        if not config_path.exists():
            return cls()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return cls.from_dict(data.get("py-ssg", {}))

    @classmethod
    def from_dict(cls, data: dict) -> "SiteConfig":
        authors = [AuthorConfig.from_dict(a) for a in data.get("authors", [])]
        feeds = [FeedConfig.from_dict(f) for f in data.get("feeds", [])]
        return cls(
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            description=str(data.get("description", "")),
            authors=authors,
            feeds=feeds,
            cache=bool(data.get("cache", True)),
        )
