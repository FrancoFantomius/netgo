from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    """A single search result returned by a search backend.

    Results are ordered by the engine's ranking; ``position`` is 1-based.
    Instances are plain dataclasses, so they support equality, hashing
    and repr, and can be unpacked like tuples.

    Example:
        >>> from netgo import search
        >>> results = search("web scraping", num=3)
        >>> first = results[0]
        >>> first.position
        1
        >>> str(first)  # defaults to the URL
        'https://...'
    """

    url: str
    title: str = ""
    snippet: str = ""
    position: int = 0
    meta: dict = field(default_factory=dict)

    def __str__(self) -> str:
        """Return the result URL for string formatting."""
        return self.url


@dataclass
class SearchParams:
    """Parameters sent to a search engine when running a query.

    Used internally by backends to build the request URL. The defaults
    match a plain Google search: 10 organic results, English, first
    page, safe search off.

    Example:
        >>> from netgo.search import SearchParams
        >>> p = SearchParams(query="hello world", num=5, safe=True)
        >>> p.gbv
        False
    """

    query: str
    num: int = 10
    lang: str = "en"
    start: int = 0
    safe: bool = False
    gbv: bool = False