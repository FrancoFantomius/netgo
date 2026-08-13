"""Shared HTTP client for the MediaWiki Action API.

:class:`WikiClient` wraps a :class:`requests.Session` and points it at
one of the four Wikimedia wikis that netgo talks to (Wikipedia,
Wikidata, Wikimedia Commons, Wiktionary). Every higher-level function in
:mod:`netgo.wiki` builds (or reuses) a client and drives it through
:meth:`WikiClient.api_call`, which handles the common plumbing: the
``format=json`` flag, error handling and missing-page detection. For
the Wikidata Query Service, :meth:`WikiClient.sparql_call` runs raw
SPARQL queries through the same session and rate-limiting settings.

The constructor is public so advanced users can reuse a single session
(or inject their own ``requests.Session`` with proxies/timeouts) across
many calls:

    >>> from netgo.wiki import WikiClient
    >>> client = WikiClient(lang="de")
    >>> client.base_url
    'https://de.wikipedia.org/w/api.php'

    >>> from netgo.wiki import search
    >>> search("berlin", client=client)[0].title
    'Berlin'
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import requests

from .errors import WikiAPIError, WikiNotFoundError

_USER_AGENT = (
    "netgo/0.4.0 (https://github.com/FrancoFantomius/netgo; "
    "mediawiki action api wrapper) requests/2.28"
)

_HOSTS = {
    "wikipedia": "https://{lang}.wikipedia.org/w/api.php",
    "wikidata": "https://www.wikidata.org/w/api.php",
    "wikimedia": "https://commons.wikimedia.org/w/api.php",
    "wiktionary": "https://{lang}.wiktionary.org/w/api.php",
}

_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }


@dataclass
class WikiClient:
    """A session wrapper around a single MediaWiki endpoint.

    Attributes:
        lang: Language code used by language-specific hosts
            (``wikipedia``, ``wiktionary``); ignored otherwise.
        host: Which wiki to talk to: ``"wikipedia"``, ``"wikidata"``,
            ``"wikimedia"`` or ``"wiktionary"``.
        session: A :class:`requests.Session` to reuse; created on demand
            when ``None``.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before every request (rate limiting).
        headers: Extra headers merged over the defaults.

    Example:
        >>> from netgo.wiki import WikiClient
        >>> c = WikiClient(lang="it", host="wikipedia", delay=0.1)
        >>> c.base_url
        'https://it.wikipedia.org/w/api.php'
        >>> c.host == "wikipedia"
        True
    """

    lang: str = "en"
    host: str = "wikipedia"
    session: requests.Session | None = None
    timeout: int = 10
    delay: float = 0.0
    headers: dict = field(default_factory=_default_headers)

    @property
    def base_url(self) -> str:
        """The API endpoint URL for the configured host and language."""
        try:
            url = _HOSTS[self.host]
        except KeyError:
            raise ValueError(f"unknown wiki host: {self.host!r}") from None
        return url.format(lang=self.lang)

    def _session(self) -> requests.Session:
        if self.session is None:
            self.session = requests.Session()
        return self.session

    def api_call(self, params: dict[str, object], *, ignore_missing: bool = False) -> dict:
        """Perform a GET against the API and return the JSON payload.

        Adds ``format=json`` to ``params``, sends the request through the
        configured session and raises on errors:

        - :class:`WikiAPIError` when the HTTP request fails or the API
          replies with an ``error`` object,
        - :class:`WikiNotFoundError` when every requested page is marked
          ``missing`` and ``ignore_missing`` is ``False``.

        Args:
            params: Query parameters for the ``w/api.php`` endpoint.
            ignore_missing: Return the raw payload (instead of raising
                :class:`WikiNotFoundError`) when the queried page is
                missing; used by callers that handle absence themselves.

        Raises:
            WikiAPIError: On transport failures or API-level errors.
            WikiNotFoundError: When all pages in the reply are missing.
        """
        if self.delay:
            time.sleep(self.delay)

        params = {**params, "format": "json"}
        url = self.base_url
        resp: requests.Response | None = None
        try:
            resp = self._session().get(
                url, params=params, headers=self.headers, timeout=self.timeout
            )
            resp.raise_for_status()
            try:
                payload = resp.json()
            except ValueError as exc:
                raise WikiAPIError(
                    "MediaWiki returned non-JSON content",
                    status=resp.status_code,
                ) from exc
        except requests.RequestException as exc:
            status = None
            if isinstance(exc, requests.HTTPError):
                status = getattr(exc, "response", None) and exc.response.status_code
            raise WikiAPIError(str(exc), status=status) from exc

        if payload.get("error"):
            err = payload["error"]
            raise WikiAPIError(
                err.get("info", "MediaWiki API error"),
                code=err.get("code"),
                info=err.get("info"),
            )
        if not ignore_missing and _all_missing(payload):
            raise WikiNotFoundError(_subject(payload), lang=self.lang)
        return payload

    def sparql_call(self, query: str) -> dict:
        """Run a raw SPARQL query against the Wikidata Query Service.

        Unlike :meth:`api_call` this talks to ``query.wikidata.org``, so
        it is meant for Wikidata-oriented clients. It sends the query
        with ``format=json`` through the same session, timeout and rate
        limiting settings and raises :class:`WikiAPIError` on HTTP
        failures or replies that do not parse as JSON.

        Args:
            query: The raw SPARQL query to execute.

        Returns:
            The parsed SPARQL JSON payload (``head``/``results``).

        Raises:
            WikiAPIError: On transport failures, HTTP errors or non-JSON
                replies (e.g. a malformed query).

        Example:
            >>> from netgo.wiki import WikiClient
            >>> client = WikiClient(host="wikidata")
            >>> payload = client.sparql_call(
            ...     "SELECT ?item WHERE { ?item wdt:P624 ?x . } LIMIT 3"
            ... )
            >>> "results" in payload
            True
        """
        if self.delay:
            time.sleep(self.delay)

        resp: requests.Response | None = None
        try:
            resp = self._session().get(
                _SPARQL_ENDPOINT,
                params={"query": query, "format": "json"},
                headers={
                    **self.headers,
                    "Accept": "application/sparql-results+json",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError as exc:
                detail = (getattr(resp, "text", "") or "").strip()
                raise WikiAPIError(
                    "Wikidata Query Service returned non-JSON content",
                    info=detail[:200] or None,
                    status=resp.status_code,
                ) from exc
        except requests.RequestException as exc:
            status = None
            if isinstance(exc, requests.HTTPError):
                status = getattr(exc, "response", None) and exc.response.status_code
            raise WikiAPIError(str(exc), status=status) from exc


def _all_missing(payload: dict) -> bool:
    """Return True when every page in the payload is marked missing."""
    pages = payload.get("query", {}).get("pages", {})
    if not isinstance(pages, dict) or not pages:
        return False
    return all(
        ("missing" in p or "redirect" in p and not _has_content(p))
        for p in pages.values()
    )


def _has_content(page: dict) -> bool:
    # A page that only carries a redirect marker is treated as content-less.
    return bool(
        set(page) & {
            "extract",
            "extracts",
            "sections",
            "categories",
            "images",
            "links",
            "pageprops",
        }
    )


def _subject(payload: dict) -> str:
    """Pick a human-readable subject for NotFound errors."""
    pages = payload.get("query", {}).get("pages", {})
    if pages:
        first = next(iter(pages.values()))
        title = first.get("title")
        if title:
            return title
    queries = payload.get("query", {}).get("search", [])
    if queries:
        return queries[0].get("title", "?")
    return "?"


def default_client(lang: str = "en", **kwargs) -> WikiClient:
    """Return a :class:`WikiClient` pre-pointed at the given Wikipedia.

    Convenience helper used by the module-level entry points; passes any
    extra ``kwargs`` through to :class:`WikiClient`.

    Example:
        >>> from netgo.wiki import default_client
        >>> c = default_client("fr", delay=0.2)
        >>> c.base_url
        'https://fr.wikipedia.org/w/api.php'
    """
    return WikiClient(lang=lang, **kwargs)


__all__ = ["WikiClient", "default_client"]