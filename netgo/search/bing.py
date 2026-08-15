from __future__ import annotations

import base64
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.parse import urlparse

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

_U_PARAM_RE = re.compile(r"[?&]u=(?:a1)?([A-Za-z0-9_=-]+)")

_BING_HOSTS = ("bing.com", "bingj.com")


def _is_bing_host(hostname: str | None) -> bool:
    """Return True if the given hostname matches bing.com, bingj.com, or subdomains."""
    if not hostname:
        return False
    host = hostname.lower()
    return any(host == bh or host.endswith("." + bh) for bh in _BING_HOSTS)


_BLOCK_MARKERS = (
    "robot check",
    "verify you are human",
    "there's no content to show here yet",
)


def _build_url(params: SearchParams) -> str:
    """Build a Bing search URL from the given :class:`SearchParams`.

    ``count`` mirrors ``num``, ``first`` mirrors ``start`` and ``setlang``
    mirrors ``lang``. Safe search maps to ``adlt=strict``; ``gbv`` is not
    used by Bing.
    """
    query = requests.utils.quote(params.query)
    url = (
        f"https://www.bing.com/search?q={query}"
        f"&count={params.num}"
        f"&setlang={params.lang}"
        f"&first={params.start}"
    )
    if params.safe:
        url += "&adlt=strict"
    return url


def _decode_bing_url(text: str) -> str | None:
    """Resolve a Bing result link to the real destination URL.

    Organic results point at ``https://www.bing.com/ck/a?...&u=a1<base64url>``;
    the ``u`` parameter carries the URL-encoded target (the ``a1`` marker
    is optional). Links that are already plain http(s) URLs are returned
    unchanged. Bing-internal pages (``/ck/a`` without ``u``, its cache
    host ``bingj.com``) and anything else that cannot be resolved return
    ``None`` and are skipped by the caller.
    """
    parsed = urlparse(text)
    host = parsed.hostname
    is_bing = _is_bing_host(host)

    if is_bing and parsed.path.rstrip("/").endswith("/ck/a"):
        match = _U_PARAM_RE.search(text)
        if match:
            payload = match.group(1)
            padded = payload + "=" * ((4 - len(payload) % 4) % 4)
            try:
                decoded = base64.urlsafe_b64decode(padded)
                return decoded.decode("utf-8", "replace")
            except Exception:  # noqa: BLE001
                return None
        return None
    if text.startswith("http") and not is_bing:
        return text
    return None


def _parse_results(soup: BeautifulSoup) -> list[Result]:
    """Parse a Bing SERP HTML tree into a list of :class:`Result`.

    Each ``li.b_algo`` card contributes one result: the longest searchable
    anchor inside its ``h2`` heading provides the title and the resolved
    URL, and the first ``<p>`` inside the card provides the snippet.
    """
    position = 0
    results: list[Result] = []
    for li in soup.select("li.b_algo"):
        h2 = li.find("h2")
        if not h2:
            continue
        best = None
        best_text = ""
        for a in h2.find_all("a", href=True):
            if _decode_bing_url(a.get("href", "")):
                text = a.get_text(separator=" ", strip=True)
                if len(text) > len(best_text):
                    best, best_text = a, text
        if best is None:
            continue
        url = _decode_bing_url(best.get("href", ""))
        if not url:
            continue
        position += 1
        para = li.select_one("p")
        results.append(
            Result(
                url=url,
                title=best_text,
                snippet=para.get_text(strip=True) if para else "",
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
    delay: float = 0.0,
    timeout: int = 10,
    session: requests.Session | None = None,
) -> list[Result]:
    """Search Bing and return a list of :class:`Result` links.

    Fetches ``https://www.bing.com/search`` with the same options that
    the Google backend accepts and parses the ``b_algo`` result cards.
    The real destination of every result is recovered from Bing's
    base64 ``u`` parameter, so no follow-up redirect requests are needed.

    Notes:
        - Bing rarely rate-limits as aggressively as Google, but the same
          ``delay`` throttling applies.
        - ``num`` and ``lang`` map to Bing's ``count`` and ``setlang``.

    Example:
        >>> from netgo import search
        >>> results = search("llm inference", num=5, engine="bing")
        >>> results[0].position
        1
        >>> for r in results[:3]:
        ...     print(r.title)
        ...

    Args:
        query: The text to search for.
        num: Number of results to request.
        lang: Language/locale code, e.g. "en", "it".
        start: Pagination offset (0-based).
        safe: Enable Bing's safe search.
        delay: Seconds to sleep before the request (rate limiting).
        timeout: Request timeout in seconds.
        session: Optional :class:`requests.Session` to reuse.

    Returns:
        A list of :class:`Result` ordered by Bing's ranking.

    Raises:
        ~requests.HTTPError: If the HTTP request fails.
        SearchBlockedError: If Bing served a captcha or empty page.
    """
    params = SearchParams(query=query, num=num, lang=lang, start=start, safe=safe)
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
                "Bing returned a captcha or empty page instead of results. "
                "Try adding a `delay`, rotating IP/proxy, or retrying later."
            )
    return results


def search_many(
    queries: Iterable[str],
    *,
    max_workers: int = 4,
    **kwargs,
) -> dict[str, list[Result]]:
    """Run :func:`search` for several queries in parallel.

    Behaves like :func:`netgo.search.google.search_many`: failed queries
    map to an empty list and their exception is stored under
    ``"<query>_error"``.

    Example:
        >>> from netgo import search_many
        >>> out = search_many(["windows", "linux"], engine="bing", num=3)
        >>> list(out)
        ['windows', 'linux']

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