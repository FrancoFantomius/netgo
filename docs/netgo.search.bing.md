### `_is_bing_host(hostname: str | None) -> bool`
Return True if the given hostname matches bing.com, bingj.com, or subdomains.

### `_build_url(params: netgo.search.models.SearchParams) -> str`
Build a Bing search URL from the given `SearchParams`.

``count`` mirrors ``num``, ``first`` mirrors ``start`` and ``setlang`` mirrors ``lang``. Safe search maps to ``adlt=strict``; ``gbv`` is not used by Bing.

### `_decode_bing_url(text: str) -> str | None`
Resolve a Bing result link to the real destination URL.

Organic results point at ``https://www.bing.com/ck/a?...&u=a1<base64url>``; the ``u`` parameter carries the URL-encoded target (the ``a1`` marker is optional). Links that are already plain http(s) URLs are returned unchanged. Bing-internal pages (``/ck/a`` without ``u``, its cache host ``bingj.com``) and anything else that cannot be resolved return ``None`` and are skipped by the caller.

### `_parse_results(soup: bs4.BeautifulSoup) -> list[netgo.search.models.Result]`
Parse a Bing SERP HTML tree into a list of `Result`.

Each ``li.b_algo`` card contributes one result: the longest searchable anchor inside its ``h2`` heading provides the title and the resolved URL, and the first ``<p>`` inside the card provides the snippet.

### `search(query: str, num: int = 10, lang: str = 'en', start: int = 0, safe: bool = False, delay: float = 0.0, timeout: int = 10, session: requests.sessions.Session | None = None) -> list[netgo.search.models.Result]`
Search Bing and return a list of `Result` links.

Fetches ``https://www.bing.com/search`` with the same options that the Google backend accepts and parses the ``b_algo`` result cards. The real destination of every result is recovered from Bing's base64 ``u`` parameter, so no follow-up redirect requests are needed.

**Notes:**
- Bing rarely rate-limits as aggressively as Google, but the same
``delay`` throttling applies.
- ``num`` and ``lang`` map to Bing's ``count`` and ``setlang``.

**Example:**
```python
>>> from netgo import search
>>> results = search("llm inference", num=5, engine="bing")
>>> results[0].position
1
>>> for r in results[:3]:
...     print(r.title)
...
```

**Args:**
- `query`: The text to search for.
- `num`: Number of results to request.
- `lang`: Language/locale code, e.g. "en", "it".
- `start`: Pagination offset (0-based).
- `safe`: Enable Bing's safe search.
- `delay`: Seconds to sleep before the request (rate limiting).
- `timeout`: Request timeout in seconds.
- `session`: Optional `requests.Session` to reuse.

**Returns:**
- A list of `Result` ordered by Bing's ranking.  

**Raises:**
- `requests.HTTPError`: If the HTTP request fails.
- `SearchBlockedError`: If Bing served a captcha or empty page.

### `search_many(queries: Iterable[str], *, max_workers: int = 4, **kwargs) -> dict[str, list[netgo.search.models.Result]]`
Run `search` for several queries in parallel.

Behaves like `netgo.search.google.search_many`: failed queries map to an empty list and their exception is stored under ``"<query>_error"``.

**Example:**
```python
>>> from netgo import search_many
>>> out = search_many(["windows", "linux"], engine="bing", num=3)
>>> list(out)
['windows', 'linux']
```

**Returns:**
- A mapping of ``query -> list[Result]``.  