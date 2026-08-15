"""netgo - a toolkit for scraping search engines and getting the links back.

Every backend returns list of :class:`Result` objects, so switching or
combining engines keeps the same data model. Currently shipped backends:

- Google (:mod:`netgo.search.google`) - the default and first backend.
- Bing (:mod:`netgo.search.bing`) - pick it with ``engine="bing"``.

The package re-exports the main entry points and shared types at the top
level for convenience: ``netgo.search``, ``netgo.search_many``,
``netgo.Result``, ``netgo.SearchParams`` and the search errors.
The ``engine`` option of ``netgo.search`` selects the backend.

Besides search engines, netgo also wraps the MediaWiki Action API in
``netgo.wiki``: Wikipedia full-text search and article structure,
Wikidata entities, Wikimedia Commons files and Wiktionary definitions,
all behind a shared :class:`netgo.wiki.WikiClient` session. And
``netgo.page`` fetches any web page and reduces it to its main content,
skipping the site template around the article. ``netgo.sitemap`` fetches
and parses XML sitemaps, discovers them through ``robots.txt`` and
crawls whole sitemap trees.

Example:
    >>> import netgo
    >>> links = netgo.search("italy travel", num=5)
    >>> for r in links:
    ...     print(r.position, r.url)
    1 https://www.italia.it/en
    ...

    >>> bing_links = netgo.search("italy travel", num=5, engine="bing")
    >>> len(bing_links)  # non-empty on a normal network
    5

    >>> batch = netgo.search_many(["cats", "dogs"], num=3)
    >>> list(batch)
    ['cats', 'dogs']
"""

from . import page, sitemap, wiki
from .page import Page, PageError, PageFetchError, PageParseError, fetch
from .search import (
    Result,
    SearchBlockedError,
    SearchError,
    SearchParams,
    bing,
    google,
    search,
    search_many,
)
from .sitemap import (
    Sitemap,
    SitemapEntry,
    SitemapError,
    SitemapFetchError,
    SitemapParseError,
    crawl,
    discover,
    filter_by_prefix,
    load,
    parse,
)

__version__ = "0.4.1"

__all__ = [
    "Result",
    "SearchParams",
    "SearchError",
    "SearchBlockedError",
    "google",
    "bing",
    "search",
    "search_many",
    "Page",
    "PageError",
    "PageFetchError",
    "PageParseError",
    "fetch",
    # sitemap
    "Sitemap",
    "SitemapEntry",
    "SitemapError",
    "SitemapFetchError",
    "SitemapParseError",
    "parse",
    "load",
    "discover",
    "crawl",
    "filter_by_prefix",
    "sitemap",
    "page",
    "wiki",
    "__version__",
]