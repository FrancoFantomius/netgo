from __future__ import annotations

import html
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.parse import unquote, urlparse

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

_REDIRECT_RE = re.compile(r"^/url\?q=|&?url=([^&]+)&")

_BLOCK_MARKERS = (
    "if you are not redirected",
    "se non vieni reindirizzato",
    "before you continue to google",
)


def _build_url(params: SearchParams) -> str:
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
    """Extract the real URL from a Google /url?q=... redirect."""
    if not text.startswith("/url"):
        return text

    match = _REDIRECT_RE.search(text)
    if match:
        rest = text[match.end():]
        rest = rest.split("&")[0]
        return unquote(rest)

    return html.unescape(text)


def _parse_results(soup: BeautifulSoup) -> list[Result]:
    position = 0
    results: list[Result] = []
    for a in soup.select("a[href^='/url?q=']"):
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

    ``kwargs`` are forwarded to :func:`search` for every query.

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