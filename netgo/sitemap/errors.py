"""Errors raised when fetching and parsing sitemaps.

Every failure of :mod:`netgo.sitemap` (transport errors, HTTP errors,
content that is not a valid sitemap) is wrapped in a ``SitemapError``
subclass, so caller code can catch the single base class and handle all
of them uniformly.

Example:
    >>> from netgo import SitemapError
    >>> try:
    ...     raise SitemapError("sitemap failed")
    ... except SitemapError as exc:
    ...     print("sitemap failed:", exc)
    sitemap failed: sitemap failed
"""


class SitemapError(Exception):
    """Base class for every error raised by :mod:`netgo.sitemap`.

    Catching this class covers transport failures, HTTP errors and
    content that cannot be parsed as a sitemap.
    """


class SitemapFetchError(SitemapError):
    """Raised when a sitemap (or robots.txt) could not be downloaded.

    Carries the HTTP status code when the request reached a server but
    answered with a non-2xx response, so callers can tell "blocked"
    (403/429) from plain network failures.
    """

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class SitemapParseError(SitemapError):
    """Raised when sitemap content cannot be read.

    Typical causes: an empty payload, XML that is not well formed, an
    unrecognized root element, or plain text that yields no URLs.
    Nothing is silently returned, so automation can detect the situation
    and react.
    """