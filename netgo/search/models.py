from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    """A single search result."""

    url: str
    title: str = ""
    snippet: str = ""
    position: int = 0
    meta: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.url


@dataclass
class SearchParams:
    """Parameters sent to a search engine."""

    query: str
    num: int = 10
    lang: str = "en"
    start: int = 0
    safe: bool = False
    gbv: bool = False