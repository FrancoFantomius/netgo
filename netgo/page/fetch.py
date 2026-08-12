"""Fetch a web page and reduce it to its main content.

:func:`fetch` requests the URL with a browser-like ``User-Agent``,
parses the HTML, extracts the article body (dropping the site template)
and wraps the result in a :class:`~netgo.page.models.Page`.

Non-HTML payloads (PDFs, images, raw API responses) and pages that yield
no extractable prose raise :class:`~netgo.page.errors.PageParseError`;
transport and HTTP errors raise
:class:`~netgo.page.errors.PageFetchError`.

Example:
    >>> from netgo import page
    >>> p = page.fetch("https://www.bbc.co.uk/news/science-environment-56837908")
    >>> p.site
    'bbc.co.uk'
    >>> bool(p.paragraphs)
    True
"""

from __future__ import annotations

import time

import requests
from bs4 import BeautifulSoup

from .errors import PageFetchError, PageParseError
from .extract import extract_content, extract_site, extract_title, render
from .models import Page

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


def fetch(
    url: str,
    *,
    timeout: int = 10,
    delay: float = 0.0,
    session: requests.Session | None = None,
    headers: dict | None = None,
) -> Page:
    """Fetch ``url`` and return its readable main content.

    Downloads the page, filters out the site template (navigation,
    headers, footers, sidebars, banners, comment widgets) and returns
    the remaining article as a :class:`Page`.

    Args:
        url: The page to read.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).
        session: Optional :class:`requests.Session` to reuse (proxies,
            timeouts, cookies are honoured).
        headers: Extra HTTP headers merged over the browser defaults.

    Returns:
        A :class:`Page` with the extracted title, site, plain-text body,
        paragraph list and the cleaned content HTML.

    Raises:
        PageFetchError: When the request fails or returns a non-2xx
            response.
        PageParseError: When the payload is not readable HTML or the
            page has no extractable main content.
    """
    if delay:
        time.sleep(delay)

    session = session or requests.Session()
    merged = {**_HEADERS, **(headers or {})}
    try:
        resp = session.get(url, headers=merged, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:
        status = None
        if isinstance(exc, requests.HTTPError):
            status = getattr(exc, "response", None) and exc.response.status_code
        raise PageFetchError(f"failed to fetch {url}: {exc}", status=status) from exc

    final_url = resp.url or url
    soup = BeautifulSoup(resp.text, "html.parser")
    content = extract_content(soup)
    text, paragraphs = render(content)
    if not paragraphs:
        raise PageParseError(f"no readable content found in {final_url}")

    return Page(
        url=final_url,
        title=extract_title(soup),
        site=extract_site(final_url),
        text=text,
        paragraphs=paragraphs,
        html=str(content) if content is not None else "",
    )