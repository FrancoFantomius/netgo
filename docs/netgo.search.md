# Search engine backends for netgo.

Two backends are shipped: Google (`netgo.search.google`) and Bing (`netgo.search.bing`). The subpackage exposes the shared data model (`Result`, `SearchParams`), the backend modules, the engine agnostic entry points (`search`, `search_many`) and the package-wide search errors (`SearchError`, `SearchBlockedError`).

The results produced by every backend are plain `Result` dataclass instances, so code written against one engine keeps working unchanged when another is selected via the ``engine`` option.

**Example:**
```python
>>> from netgo.search import search
>>> google_hits = search("web scraping", num=5, engine="google")
>>> bing_hits = search("web scraping", num=5, engine="bing")
>>> type(google_hits[0]).__name__
'Result'
```

### `search(query: str, engine: str = 'google', **kwargs) -> list[netgo.search.models.Result]`
Search any installed engine and return a list of `Result`.

Dispatches to the backend selected by ``engine``, forwarding ``num``, ``lang``, ``safe`` and the other backend-specific keyword arguments.

**Args:**
- `query`: The text to search for.
- `engine`: The backend to use: ``"google"`` or ``"bing"``.
- `kwargs`: Forwarded to the selected backend's search function.

**Returns:**
- A list of `Result` ordered by the engine's ranking.  

**Raises:**
- `KeyError`: If ``engine`` is not an installed backend.

**Example:**
```python
>>> from netgo import search
>>> hits = search("climate report", num=5, engine="bing")
>>> hits[0].position
1
```

### `search_many(queries: Iterable[str], *, engine: str = 'google', **kwargs) -> dict[str, list[netgo.search.models.Result]]`
Run `search` for several queries in parallel.

Dispatches to the backend selected by ``engine``; every query is executed concurrently. A failing query maps to an empty list and its exception is stored under ``"<query>_error"``.

**Args:**
- `queries`: An iterable of search queries.
- `engine`: The backend to use: ``"google"`` or ``"bing"``.
- `kwargs`: Forwarded to the selected backend's search_many.

**Returns:**
- A mapping of ``query -> list[Result]``.  

**Raises:**
- `KeyError`: If ``engine`` is not an installed backend.

**Example:**
```python
>>> from netgo import search_many
>>> out = search_many(["cats", "dogs"], engine="bing", num=3)
>>> list(out)
['cats', 'dogs']
```