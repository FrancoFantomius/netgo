"""Search engine backends for netgo.

Two backends are shipped: Google (:mod:`netgo.search.google`) and Bing
(:mod:`netgo.search.bing`). The subpackage exposes the shared data model
(:class:`Result`, :class:`SearchParams`), the backend modules, the engine
agnostic entry points (:func:`search`, :func:`search_many`) and the
package-wide search errors (:class:`SearchError`,
:class:`SearchBlockedError`).

The results produced by every backend are plain :class:`Result` dataclass
instances, so code written against one engine keeps working unchanged when
another is selected via the ``engine`` option.

Example:
    >>> from netgo.search import search
    >>> google_hits = search("web scraping", num=5, engine="google")
    >>> bing_hits = search("web scraping", num=5, engine="bing")
    >>> type(google_hits[0]).__name__
    'Result'
"""

from typing import Iterable

from . import bing, google
from .errors import SearchBlockedError, SearchError
from .models import Result, SearchParams

_BACKENDS = {
    "google": google,
    "bing": bing,
}


def search(query: str, engine: str = "google", **kwargs) -> list[Result]:
    """Search any installed engine and return a list of :class:`Result`.

    Dispatches to the backend selected by ``engine``, forwarding ``num``,
    ``lang``, ``safe`` and the other backend-specific keyword arguments.

    Args:
        query: The text to search for.
        engine: The backend to use: ``"google"`` or ``"bing"``.
        **kwargs: Forwarded to the selected backend's search function.

    Returns:
        A list of :class:`Result` ordered by the engine's ranking.

    Raises:
        KeyError: If ``engine`` is not an installed backend.

    Example:
        >>> from netgo import search
        >>> hits = search("climate report", num=5, engine="bing")
        >>> hits[0].position
        1
    """
    return _BACKENDS[engine].search(query, **kwargs)


def search_many(
    queries: Iterable[str],
    *,
    engine: str = "google",
    **kwargs,
) -> dict[str, list[Result]]:
    """Run :func:`search` for several queries in parallel.

    Dispatches to the backend selected by ``engine``; every query is
    executed concurrently. A failing query maps to an empty list and its
    exception is stored under ``"<query>_error"``.

    Args:
        queries: An iterable of search queries.
        engine: The backend to use: ``"google"`` or ``"bing"``.
        **kwargs: Forwarded to the selected backend's search_many.

    Returns:
        A mapping of ``query -> list[Result]``.

    Raises:
        KeyError: If ``engine`` is not an installed backend.

    Example:
        >>> from netgo import search_many
        >>> out = search_many(["cats", "dogs"], engine="bing", num=3)
        >>> list(out)
        ['cats', 'dogs']
    """
    return _BACKENDS[engine].search_many(queries, **kwargs)


__all__ = [
    "Result",
    "SearchParams",
    "SearchError",
    "SearchBlockedError",
    "google",
    "bing",
    "search",
    "search_many",
]