from __future__ import annotations

import html
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .errors import SearchBlockedError
from .models import Result, SearchParams

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_BLOCK_MARKERS = (
    "if you are not redirected",
    "se non vieni reindirizzato",
    "before you continue to google",
)


def _build_url(params: SearchParams) -> str:
    """Build a Google search URL from the given :class:`SearchParams`.

    The query is URL-encoded, then ``num``, ``hl`` and ``start`` are
    appended. ``safe`` and ``gbv`` add their respective URL flags, so
    the returned URL is ready to be fetched with :func:`requests.get`.

    Example:
        >>> from netgo.search import SearchParams
        >>> _build_url(SearchParams(query="hello world", safe=True, gbv=True))
        'https://www.google.com/search?q=hello%20world&num=10&hl=en&start=0&safe=active&gbv=1'
    """
    query = requests.utils.quote(params.query)
    url = (
        f"https://www.google.com/search?q={query}"
        f"&num={params.num}"
        f"&hl={params.lang}"
        f"&start={params.start}"
    )
    if params.safe:
        url += "&safe=active"
    if params.gbv:
        url += "&gbv=1"
    return url


def _decode_google_url(text: str) -> str:
    """Resolve a Google redirect link to the real destination URL.

    Result anchors come in three shapes, all of which are handled:

    - relative: ``/url?q=<encoded-URL>&sa=...``
    - absolute: ``https://www.google.com/url?esrc=s&q=<encoded-URL>&usg=...``
    - translated: ``https://translate.google.com/translate?u=<encoded-URL>``

    The target is decoded from the ``q`` (or ``u``) parameter. Inputs
    that are not redirect links are returned unchanged.

    Example:
        >>> _decode_google_url(
        ...     "/url?q=https%3A%2F%2Fexample.org%2Fa%3Fb%3D1&amp;sa=U&amp;ved=2ahUKE"
        ... )
        'https://example.org/a?b=1'
        >>> _decode_google_url(
        ...     "https://www.google.com/url?esrc=s&q=https%3A%2F%2Fexample.org&sa=D"
        ... )
        'https://example.org'
        >>> _decode_google_url("https://example.org/page")
        'https://example.org/page'
    """
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    is_redirect = (
        text.startswith("/url")
        or (
            (host == "google.com" or host.endswith(".google.com"))
            and parsed.path.rstrip("/").endswith("/url")
        )
        or (
            parsed.netloc == "translate.google.com"
            and parsed.path.rstrip("/").endswith("/translate")
        )
    )
    if not is_redirect:
        return text

    query = parsed.query
    qs = parse_qs(query)
    target_param = "u" if parsed.netloc == "translate.google.com" else "q"
    target = qs.get(target_param)
    if target:
        return target[0]

    return html.unescape(text)


def _parse_results(soup: BeautifulSoup) -> list[Result]:
    """Parse a Google SERP HTML tree into a list of :class:`Result`.

    Walks every result anchor in document order — both the relative
    ``/url?q=...`` links and the absolute ``https://www.google.com/url?...``
    and ``https://translate.google.com/translate?...`` forms — decodes
    the destination URL and picks the title and snippet from the
    surrounding result card. Non-http targets (javascript:, intl/ pages)
    and google.com internal links are discarded, so the returned list is
    strictly the organic results.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '<a href="/url?q=https%3A%2F%2Fexample.org"><h3>Example</h3></a>'
        >>> _parse_results(BeautifulSoup(html, "html.parser"))[0]
        Result(url='https://example.org', title='Example', snippet='', position=1, meta={})
    """
    position = 0
    results: list[Result] = []
    selector = (
        "a[href^='/url?q='], "
        "a[href^='https://www.google.com/url?'], "
        "a[href^='https://translate.google.com/translate?']"
    )
    for a in soup.select(selector):
        url = _decode_google_url(a.get("href", ""))
        if not url.startswith("http") or "google.com" in urlparse(url).netloc:
            continue
        position += 1

        title_el = a.find("h3")
        title = title_el.get_text() if title_el else ""

        parent = a.find_parent(class_=re.compile(r"tF2Cxc|g"))
        snippet = ""
        if parent:
            snip_el = parent.select_one(".VwiC3b, .IsZvec")
            if snip_el:
                snippet = snip_el.get_text()

        results.append(
            Result(
                url=url,
                title=title,
                snippet=snippet,
                position=position,
            )
        )
    return results


def search(
    query: str,
    num: int = 10,
    lang: str = "en",
    start: int = 0,
    safe: bool = False,
    gbv: bool = False,
    delay: float = 0.0,
    timeout: int = 10,
    session: requests.Session | None = None,
) -> list[Result]:
    """Search Google and return a list of :class:`Result` links.

    Builds the search URL from the parameters, fetches the results page
    with :mod:`requests`, and parses the organic result links. Google
    redirect URLs are resolved to their real destination, and each
    result carries its title and snippet when available.

    Notes:
        - ``num`` is capped by Google at 100, whatever value is passed.
        - Datacenter IPs are frequently rate-limited; when Google serves
          an interstitial page instead of results, ``SearchBlockedError``
          is raised so callers can tell a real empty result from a block.
        - Passing ``gbv=True`` switches to Google's basic HTML interface,
          which sometimes bypasses the block but in some regions gets
          redirected to the consent page instead.
        - Use ``delay`` to throttle consecutive requests.

    Example:
        >>> from netgo import search
        >>> results = search("python packaging", num=10)
        >>> results[0].position
        1
        >>> for r in results[:3]:
        ...     print(r.title)
        ...

    Args:
        query: The text to search for.
        num: Number of results to request (max 100).
        lang: Language code, e.g. "en", "it".
        start: Pagination offset (0-based).
        safe: Enable Google's safe search.
        gbv: Use Google's basic, non-JavaScript HTML interface. May help
            when the default page is blocked, but some regions redirect it
            to a consent page instead.
        delay: Seconds to sleep before the request (rate limiting).
        timeout: Request timeout in seconds.
        session: Optional :class:`requests.Session` to reuse.

    Returns:
        A list of :class:`Result` ordered by Google's ranking.

    Raises:
        ~requests.HTTPError: If the HTTP request fails.
        SearchBlockedError: If Google served an interstitial or consent page
            instead of search results.
    """
    params = SearchParams(
        query=query,
        num=num,
        lang=lang,
        start=start,
        safe=safe,
        gbv=gbv,
    )
    url = _build_url(params)

    if delay:
        time.sleep(delay)

    session = session or requests.Session()
    resp = session.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    results = _parse_results(soup)
    if not results:
        body = soup.get_text(" ", strip=True)[:5000].lower()
        if any(marker in body for marker in _BLOCK_MARKERS):
            raise SearchBlockedError(
                "Google returned an interstitial/consent page instead of "
                "results (your IP is likely rate-limited). Options: use "
                "`gbv=True`, add a `delay`, rotate IP/proxy, or retry later."
            )
    return results


def search_many(
    queries: Iterable[str],
    *,
    max_workers: int = 4,
    **kwargs,
) -> dict[str, list[Result]]:
    """Run :func:`search` for several queries in parallel.

    Each query is submitted to a thread pool and all searches are
    executed concurrently, which is much faster than a loop for dozens
    of queries. ``kwargs`` (e.g. ``num``, ``delay``) are forwarded to
    :func:`search` for every query.

    A query that fails does not abort the others: it maps to an empty
    list and its exception is stored under ``"<query>_error"``, so the
    caller can inspect failures without losing the successful results.

    Example:
        >>> from netgo import search_many
        >>> out = search_many(["cats", "dogs"], num=3, delay=0.5)
        >>> out.keys()
        dict_keys(['cats', 'dogs'])
        >>> for query, results in out.items():
        ...     print(query, [r.url for r in results])
        ...

    Returns:
        A mapping of ``query -> list[Result]``.
    """
    queries = list(queries)
    results: dict[str, list[Result]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(search, q, **kwargs): q for q in queries}
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                results[q] = fut.result()
            except Exception as exc:  # noqa: BLE001
                results[q] = []
                results[q + "_error"] = exc  # type: ignore[assignment]
    return results