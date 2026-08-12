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
all behind a shared :class:`netgo.wiki.WikiClient` session.

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

from . import wiki
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

__version__ = "0.2.0"

__all__ = [
    "Result",
    "SearchParams",
    "SearchError",
    "SearchBlockedError",
    "google",
    "bing",
    "search",
    "search_many",
    "wiki",
    "__version__",
]