"""Fetch sitemaps over HTTP and discover them through robots.txt.

:func:`load` downloads a sitemap (plain or gzip-compressed, index or URL
set) and parses it into a :class:`~netgo.sitemap.models.Sitemap`.
:func:`discover` finds the ``Sitemap:`` URLs a site declares in its
``robots.txt``, and :func:`crawl` recursively follows ``<sitemapindex>``
children to collect every URL across all sub-sitemaps.
:func:`filter_by_prefix` crawls a tree and keeps only the URLs that start
with a given prefix.

Transport and HTTP failures raise
:class:`~netgo.sitemap.errors.SitemapFetchError`; bodies that cannot be
read raise :class:`~netgo.sitemap.errors.SitemapParseError`.

Example:
    >>> from netgo import sitemap
    >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
    >>> sm.urls[0]
    'https://www.example.com/'
"""

from __future__ import annotations

import gzip
import time
from urllib.parse import urlsplit

import requests

from .errors import SitemapFetchError, SitemapParseError
from .models import Sitemap, SitemapEntry, _SITEMAPINDEX
from .parse import parse

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml,text/xml,text/plain,*/*;q=0.8",
}

_GZIP_MAGIC = b"\x1f\x8b"


def _get(
    url: str,
    *,
    session: requests.Session,
    timeout: int,
    delay: float,
    headers: dict | None,
) -> requests.Response:
    if delay:
        time.sleep(delay)
    merged = {**_HEADERS, **(headers or {})}
    try:
        resp = session.get(url, headers=merged, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        status = None
        if isinstance(exc, requests.HTTPError):
            status = getattr(exc, "response", None) and exc.response.status_code
        raise SitemapFetchError(f"failed to fetch {url}: {exc}", status=status) from exc
    return resp


def load(
    url: str,
    *,
    timeout: int = 10,
    delay: float = 0.0,
    session: requests.Session | None = None,
    headers: dict | None = None,
) -> Sitemap:
    """Fetch a sitemap URL and parse it into a :class:`Sitemap`.

    Handles plain and gzip-compressed sitemap bodies (both a real
    ``Content-Encoding`` header and a bare ``sitemap.xml.gz`` served
    without one), and resolves relative locations against the final URL.

    Args:
        url: The sitemap (or sitemap index) URL.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).
        session: Optional :class:`requests.Session` to reuse (proxies,
            cookies are honoured).
        headers: Extra HTTP headers merged over the browser defaults.

    Returns:
        A :class:`Sitemap` carrying the URL entries or child locations.

    Raises:
        SitemapFetchError: When the request fails or returns a non-2xx
            response.
        SitemapParseError: When the body is empty or not a valid sitemap.

    Example:
        >>> from netgo import sitemap
        >>> sm = sitemap.load("https://www.example.com/sitemap.xml")
        >>> sm.kind
        'urlset'
    """
    session = session or requests.Session()
    resp = _get(url, session=session, timeout=timeout, delay=delay, headers=headers)
    final_url = resp.url or url
    payload = resp.content
    if payload.startswith(_GZIP_MAGIC):
        try:
            payload = gzip.decompress(payload)
        except OSError as exc:
            raise SitemapParseError(f"corrupt gzip sitemap at {final_url}: {exc}") from exc
    return parse(payload, base_url=final_url)


def discover(
    url_or_domain: str,
    *,
    timeout: int = 10,
    delay: float = 0.0,
    session: requests.Session | None = None,
    headers: dict | None = None,
) -> list[str]:
    """Return the ``Sitemap:`` URLs a site declares in its robots.txt.

    Accepts a full URL (``https://example.com/any/path``) or a bare
    domain (``example.com``); robots.txt is looked up on the origin, so
    a site *must* advertise its sitemaps there for this to find them. A
    missing robots.txt (404) simply yields an empty list.

    Args:
        url_or_domain: A site URL, or a bare hostname.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).
        session: Optional :class:`requests.Session` to reuse.
        headers: Extra HTTP headers merged over the browser defaults.

    Returns:
        The list of sitemap URLs declared by robots.txt (empty when the
        site advertises none).

    Raises:
        SitemapFetchError: When robots.txt cannot be downloaded for a
            reason other than a missing file (404).

    Example:
        >>> from netgo import sitemap
        >>> urls = sitemap.discover("https://www.example.com")
        >>> urls[0].startswith("http")
        True
    """
    origin = _origin(url_or_domain)
    robots = f"{origin}/robots.txt"
    session = session or requests.Session()
    try:
        resp = _get(robots, session=session, timeout=timeout, delay=delay, headers=headers)
    except SitemapFetchError as exc:
        if exc.status == 404:
            return []
        raise
    return [ln.strip() for ln in _robots_sitemaps(resp.text)]


def crawl(
    url: str,
    *,
    max_entries: int = 1000,
    timeout: int = 10,
    delay: float = 0.0,
    session: requests.Session | None = None,
    headers: dict | None = None,
) -> list[SitemapEntry]:
    """Fetch a whole sitemap tree and return every URL entry.

    Starting from a sitemap URL, follows ``<sitemapindex>`` children
    recursively (skipping already-visited sub-sitemaps), downloads each
    child, and collects all ``<url>`` entries across the tree in
    document order, deduplicated by location.

    Args:
        url: A sitemap or sitemap index URL.
        max_entries: Stop after collecting this many entries.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before every request (rate limiting).
        session: Optional :class:`requests.Session` to reuse.
        headers: Extra HTTP headers merged over the browser defaults.

    Returns:
        A list of :class:`SitemapEntry`, deduplicated by ``loc``.

    Raises:
        SitemapFetchError: When any sitemap in the tree fails to load.
        SitemapParseError: When any sitemap body cannot be read.

    Example:
        >>> from netgo import sitemap
        >>> urls = sitemap.crawl("https://www.example.com/sitemap.xml")
        >>> urls[0].loc.startswith("http")
        True
    """
    session = session or requests.Session()
    queue = [url]
    visited: set[str] = set()
    seen: set[str] = set()
    out: list[SitemapEntry] = []

    while queue and len(out) < max_entries:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        sitemap = load(current, timeout=timeout, delay=delay, session=session, headers=headers)
        if sitemap.kind == _SITEMAPINDEX:
            queue.extend(child for child in sitemap.children if child not in visited)
            continue
        for entry in sitemap.entries:
            if entry.loc not in seen:
                seen.add(entry.loc)
                out.append(entry)
    return out


def filter_by_prefix(
    url: str,
    prefix: str,
    *,
    max_entries: int = 1000,
    timeout: int = 10,
    delay: float = 0.0,
    session: requests.Session | None = None,
    headers: dict | None = None,
) -> list[SitemapEntry]:
    """Crawl a sitemap tree and return only the entries starting with a prefix.

    Crawls the whole sitemap tree exactly like :func:`crawl`, then keeps
    only the URL entries whose ``loc`` starts with ``prefix``. Use it to
    grab every page of a numbered family (``https://example.com/page_1``,
    ``https://example.com/page_2``, ...) straight from the sitemap.

    Args:
        url: A sitemap or sitemap index URL.
        prefix: URL prefix to match against each entry's ``loc``.
        max_entries: Stop after collecting this many entries in the crawl.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before every request (rate limiting).
        session: Optional :class:`requests.Session` to reuse.
        headers: Extra HTTP headers merged over the browser defaults.

    Returns:
        A list of :class:`SitemapEntry` whose ``loc`` starts with
        ``prefix``, in crawl order.

    Raises:
        SitemapFetchError: When any sitemap in the tree fails to load.
        SitemapParseError: When any sitemap body cannot be read.

    Example:
        >>> from netgo import sitemap
        >>> pages = sitemap.filter_by_prefix(
        ...     "https://www.example.com/sitemap.xml",
        ...     "https://www.example.com/page_",
        ... )
        >>> pages[0].loc.startswith("https://www.example.com/page_")
        True
    """
    entries = crawl(
        url,
        max_entries=max_entries,
        timeout=timeout,
        delay=delay,
        session=session,
        headers=headers,
    )
    return [entry for entry in entries if entry.loc.startswith(prefix)]


def _origin(url: str) -> str:
    """Return the ``scheme://netloc`` of a URL, defaulting to https."""
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def _robots_sitemaps(text: str) -> list[str]:
    """Extract the ``Sitemap:`` lines from a robots.txt body."""
    urls = []
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            continue
        if key.strip().lower() == "sitemap":
            url = value.strip()
            if url:
                urls.append(url)
    return urls


__all__ = ["load", "discover", "crawl", "filter_by_prefix"]