### `_build_url(params: netgo.search.models.SearchParams) -> str`
Build a Google search URL from the given `SearchParams`.

The query is URL-encoded, then ``num``, ``hl`` and ``start`` are appended. ``safe`` and ``gbv`` add their respective URL flags, so the returned URL is ready to be fetched with `requests.get`.

**Example:**
```python
>>> from netgo.search import SearchParams
>>> _build_url(SearchParams(query="hello world", safe=True, gbv=True))
'https://www.google.com/search?q=hello%20world&num=10&hl=en&start=0&safe=active&gbv=1'
```

### `_decode_google_url(text: str) -> str`
Resolve a Google redirect link to the real destination URL.

Result anchors come in three shapes, all of which are handled:

- relative: ``/url?q=<encoded-URL>&sa=...``

- absolute: ``https://www.google.com/url?esrc=s&q=<encoded-URL>&usg=...``

- translated: ``https://translate.google.com/translate?u=<encoded-URL>``

The target is decoded from the ``q`` (or ``u``) parameter. Inputs that are not redirect links are returned unchanged.

**Example:**
```python
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
```

### `_parse_results(soup: bs4.BeautifulSoup) -> list[netgo.search.models.Result]`
Parse a Google SERP HTML tree into a list of `Result`.

Walks every result anchor in document order — both the relative ``/url?q=...`` links and the absolute ``https://www.google.com/url?...`` and ``https://translate.google.com/translate?...`` forms — decodes the destination URL and picks the title and snippet from the surrounding result card. Non-http targets (javascript:, intl/ pages) and google.com internal links are discarded, so the returned list is strictly the organic results.

**Example:**
```python
>>> from bs4 import BeautifulSoup
>>> html = '<a href="/url?q=https%3A%2F%2Fexample.org"><h3>Example</h3></a>'
>>> _parse_results(BeautifulSoup(html, "html.parser"))[0]
Result(url='https://example.org', title='Example', snippet='', position=1, meta={})
```

### `search(query: str, num: int = 10, lang: str = 'en', start: int = 0, safe: bool = False, gbv: bool = False, delay: float = 0.0, timeout: int = 10, session: requests.sessions.Session | None = None) -> list[netgo.search.models.Result]`
Search Google and return a list of `Result` links.

Builds the search URL from the parameters, fetches the results page with `requests`, and parses the organic result links. Google redirect URLs are resolved to their real destination, and each result carries its title and snippet when available.

**Notes:**
- ``num`` is capped by Google at 100, whatever value is passed.
- Datacenter IPs are frequently rate-limited; when Google serves
an interstitial page instead of results, ``SearchBlockedError``
is raised so callers can tell a real empty result from a block.
- Passing ``gbv=True`` switches to Google's basic HTML interface,
which sometimes bypasses the block but in some regions gets
redirected to the consent page instead.
- Use ``delay`` to throttle consecutive requests.

**Example:**
```python
>>> from netgo import search
>>> results = search("python packaging", num=10)
>>> results[0].position
1
>>> for r in results[:3]:
...     print(r.title)
...
```

**Args:**
- `query`: The text to search for.
- `num`: Number of results to request (max 100).
- `lang`: Language code, e.g. "en", "it".
- `start`: Pagination offset (0-based).
- `safe`: Enable Google's safe search.
- `gbv`: Use Google's basic, non-JavaScript HTML interface. May help when the default page is blocked, but some regions redirect it to a consent page instead.
- `delay`: Seconds to sleep before the request (rate limiting).
- `timeout`: Request timeout in seconds.
- `session`: Optional `requests.Session` to reuse.

**Returns:**
- A list of `Result` ordered by Google's ranking.  

**Raises:**
- `requests.HTTPError`: If the HTTP request fails.
- `SearchBlockedError`: If Google served an interstitial or consent page instead of search results.

### `search_many(queries: Iterable[str], *, max_workers: int = 4, **kwargs) -> dict[str, list[netgo.search.models.Result]]`
Run `search` for several queries in parallel.

Each query is submitted to a thread pool and all searches are executed concurrently, which is much faster than a loop for dozens of queries. ``kwargs`` (e.g. ``num``, ``delay``) are forwarded to `search` for every query.

A query that fails does not abort the others: it maps to an empty list and its exception is stored under ``"<query>_error"``, so the caller can inspect failures without losing the successful results.

**Example:**
```python
>>> from netgo import search_many
>>> out = search_many(["cats", "dogs"], num=3, delay=0.5)
>>> out.keys()
dict_keys(['cats', 'dogs'])
>>> for query, results in out.items():
...     print(query, [r.url for r in results])
...
```

**Returns:**
- A mapping of ``query -> list[Result]``.  