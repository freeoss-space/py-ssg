import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILENAME = "py-ssg.toml"


@dataclass
class AuthorConfig:
    name: str = ""
    email: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> AuthorConfig:
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
    def from_dict(cls, data: dict) -> FeedConfig:
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
class SyntaxConfig:
    enabled: bool = True
    theme_light: str = "friendly"
    theme_dark: str = "monokai"

    @classmethod
    def from_dict(cls, data: dict) -> SyntaxConfig:
        return cls(
            enabled=bool(data.get("enabled", True)),
            theme_light=str(data.get("theme_light", "friendly")),
            theme_dark=str(data.get("theme_dark", "monokai")),
        )


@dataclass
class TocConfig:
    enabled: bool = False
    max_depth: int = 3

    @classmethod
    def from_dict(cls, data: dict) -> TocConfig:
        return cls(
            enabled=bool(data.get("enabled", False)),
            max_depth=int(data.get("max_depth", 3)),
        )


@dataclass
class ServerConfig:
    port: int = 8000

    @classmethod
    def from_dict(cls, data: dict) -> ServerConfig:
        return cls(
            port=int(data.get("port", 8000)),
        )


@dataclass
class SiteConfig:
    name: str = ""
    url: str = ""
    description: str = ""
    authors: list[AuthorConfig] = field(default_factory=list)
    feeds: list[FeedConfig] = field(default_factory=list)
    cache: bool = True
    syntax: SyntaxConfig = field(default_factory=SyntaxConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    toc: TocConfig = field(default_factory=TocConfig)

    @classmethod
    def load(cls, project_dir: Path) -> SiteConfig:
        config_path = project_dir / CONFIG_FILENAME
        if not config_path.exists():
            return cls()
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return cls.from_dict(data.get("py-ssg", {}))

    @classmethod
    def from_dict(cls, data: dict) -> SiteConfig:
        authors = [AuthorConfig.from_dict(a) for a in data.get("authors", [])]
        feeds = [FeedConfig.from_dict(f) for f in data.get("feeds", [])]
        syntax = SyntaxConfig.from_dict(data.get("syntax", {}))
        server = ServerConfig.from_dict(data.get("server", {}))
        toc = TocConfig.from_dict(data.get("toc", {}))
        return cls(
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            description=str(data.get("description", "")),
            authors=authors,
            feeds=feeds,
            cache=bool(data.get("cache", True)),
            syntax=syntax,
            server=server,
            toc=toc,
        )
