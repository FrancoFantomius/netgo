"""Data models returned by the :mod:`netgo.sitemap` wrappers.

:class:`Sitemap` is the parsed representation of a sitemap document;
it carries either the URL entries of a ``<urlset>`` (or plain-text
sitemap) or the child sitemap locations of a ``<sitemapindex>``.
Every ``<loc>`` value is resolved against the sitemap's own URL, so
relative and protocol-relative references never leak through.

Example:
    >>> from netgo import sitemap
    >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
    >>> sm.entries[0].loc
    'https://www.example.com/'
    >>> sm.urls[0]
    'https://www.example.com/'
"""

from __future__ import annotations

from dataclasses import dataclass, field

_URLSET = "urlset"
_SITEMAPINDEX = "sitemapindex"
_TEXT = "text"


@dataclass
class SitemapEntry:
    """A single ``<url>`` entry in a sitemap.

    ``loc`` is the page URL (always absolute, resolved against the
    sitemap that declared it); ``lastmod``, ``changefreq`` and
    ``priority`` mirror the optional metadata of the same name, falling
    back to sensible defaults when omitted.

    Example:
        >>> from netgo import sitemap
        >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
        >>> sm.entries[0].loc
        'https://www.example.com/'
    """

    loc: str
    lastmod: str = ""
    changefreq: str = ""
    priority: float = 0.0

    def __str__(self) -> str:
        """Return the entry URL for string formatting."""
        return self.loc


@dataclass
class Sitemap:
    """A parsed sitemap document.

    ``kind`` is ``"urlset"``, ``"sitemapindex"`` or ``"text"``.
    ``entries`` holds the :class:`SitemapEntry` list of a URL sitemap
    and ``children`` the child sitemap locations of an index; the other
    collection stays empty on each side. ``url`` is where the document
    was fetched from (empty for a raw :func:`~netgo.sitemap.parse`
    without a base URL).

    Iterating over a sitemap yields its ``entries``; ``urls`` is a
    shortcut for their ``loc`` values.

    Example:
        >>> from netgo import sitemap
        >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
        >>> bool(sm)
        True
        >>> for entry in sm:
        ...     print(entry.loc)
        https://www.example.com/
    """

    url: str = ""
    kind: str = _URLSET
    entries: list[SitemapEntry] = field(default_factory=list)
    children: list[str] = field(default_factory=list)

    @property
    def urls(self) -> list[str]:
        """The ``loc`` of every entry (empty for a bare sitemap index)."""
        return [entry.loc for entry in self.entries]

    def by_prefix(self, prefix: str) -> list[SitemapEntry]:
        """Return the entries whose URL starts with ``prefix``.

        Filters the entries of this sitemap with ``loc.startswith(prefix)``,
        handy for grabbing every page of a numbered family
        (``https://example.com/page_1``, ``https://example.com/page_2``, ...).
        For a whole sitemap-tree search use
        :func:`~netgo.sitemap.filter_by_prefix`.

        Args:
            prefix: URL prefix to match against each entry's ``loc``.

        Returns:
            The matching :class:`SitemapEntry` list, in document order.

        Example:
            >>> from netgo import sitemap
            >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
            >>> sm.by_prefix("https://www.example.com/page_")[0].loc
            'https://www.example.com/page_1'
        """
        return [entry for entry in self.entries if entry.loc.startswith(prefix)]

    def __iter__(self):
        """Iterate over the URL entries of the sitemap."""
        return iter(self.entries)

    def __len__(self) -> int:
        """Return the number of URL entries."""
        return len(self.entries)

    def __bool__(self) -> bool:
        """Return True when the sitemap carries any URLs."""
        return bool(self.entries) or bool(self.children)

    def __str__(self) -> str:
        """Return the sitemap URL for string formatting."""
        return self.url


__all__ = ["Sitemap", "SitemapEntry", "_URLSET", "_SITEMAPINDEX", "_TEXT"]