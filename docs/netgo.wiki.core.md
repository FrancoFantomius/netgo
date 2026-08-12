# Wikipedia core API: articles, search and page structure.

This module wraps the ``action=query`` endpoints of each language edition of Wikipedia. Every function accepts ``lang`` to pick the edition (the default is English), ``client`` to reuse a `netgo.wiki.WikiClient` instance, plus ``timeout``/``delay`` matching the search backends.

**Notes:**
- All text-based functions return plain text: ``explaintext`` strips
markup, links and tables, so what you get is reader-friendly prose.
- Pages that do not exist raise
`netgo.wiki.WikiNotFoundError` (the API marks them
``missing``); nothing is silently returned.

**Example:**
```python
>>> from netgo.wiki import summary, paragraphs, geo_search
>>> summary("Python (programming language)")
'Python is a high-level, interpreted programming language...'
>>> pars = paragraphs("Bread")
>>> len(pars) > 1
True
>>> geo_search(41.9, 12.5, radius=10000, limit=2)[0].title
'Vatican City'
```

### `_page_of(payload: dict, *, lang: str) -> dict`
Return the single page object out of a ``query.pages`` payload.

Raises `WikiNotFoundError` when the page is missing, so the callers do not repeat the check themselves.

**Example:**
```python
>>> _page_of({"query": {"pages": {"1": {"title": "A", "missing": ""}}}}, lang="en")
Traceback (most recent call last):
...
netgo.wiki.errors.WikiNotFoundError: Not found: 'A' in 'en'
```

### `_query(titles: str | None = None, *, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0, **props) -> dict`
Share the tiny plumbing used by the article-level wrappers.

### `search(query: str, lang: str = 'en', limit: int = 10, namespace: int = 0, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.WikiResult]`
Full-text search across a Wikipedia edition.

Uses ``list=search`` (the same backend that powers MediaWiki's own search box) and returns the ranked hits with their snippet, size, word count and last-edit timestamp.

**Args:**
- `query`: The text to search for.
- `lang`: Language code of the Wikipedia edition.
- `limit`: Maximum number of hits (MediaWiki caps at 50 per call).
- `namespace`: Namespace to search (0 = articles).
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `WikiResult`, ranked by the engine.  

**Example:**
```python
>>> from netgo.wiki import search
>>> hits = search("deep learning", limit=3)
>>> hits[0].title
'Deep learning'
```

### `summary(title: str, lang: str = 'en', sentences: int = 5, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> str`
Return the lead/intro of an article as plain text.

Fetches the introductory paragraphs only (``exintro``), with markup stripped, so the result reads like the article's opening blurb.

**Args:**
- `title`: The article title (normalized by the API on request).
- `lang`: Language code of the Wikipedia edition.
- `sentences`: Maximum number of sentences to keep.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- The article's lead paragraph(s) as a string.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import summary
>>> s = summary("Python (programming language)", sentences=1)
>>> s.startswith("Python is")
True
```

### `paragraphs(title: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[str]`
Return the full body of an article split into paragraphs.

Fetches the whole page as plain text and splits it on blank lines, so each item is one prose paragraph, ready for display or NLP downstream of this library.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of paragraph strings; the first is the lead.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import paragraphs
>>> pars = paragraphs("Bread")
>>> bool(pars[0].strip())
True
```

### `sections(title: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Section]`
Return the table of contents (section outline) of an article.

Uses ``action=parse&prop=sections`` so each heading of the article becomes a `Section` with its index and nesting level.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `Section`, in document order.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import sections
>>> toc = sections("Python (programming language)")
>>> any(s.title == "History" for s in toc)
True
```

### `links(title: str, lang: str = 'en', limit: int = 50, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Link]`
Return the wikilinks that leave an article.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `limit`: Maximum number of links to fetch.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `Link`.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import links
>>> out = links("Python (programming language)", limit=5)
>>> out[0].ns
0
```

### `backlinks(title: str, lang: str = 'en', limit: int = 50, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Link]`
Return the articles that link \*to\* a given page.

"What links here" — a lightweight cross-reference useful for graph building and recommending related articles.

**Args:**
- `title`: The page to look up.
- `lang`: Language code of the Wikipedia edition.
- `limit`: Maximum number of backlinks to fetch.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `Link`.  

**Example:**
```python
>>> from netgo.wiki import backlinks
>>> out = backlinks("Python (programming language)", limit=5)
>>> bool(out)
True
```

### `categories(title: str, lang: str = 'en', limit: int = 50, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Category]`
Return the categories an article belongs to.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `limit`: Maximum number of categories to fetch.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `Category`.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import categories
>>> cats = categories("Python (programming language)")
>>> any("Programming languages" in c.title for c in cats)
True
```

### `images(title: str, lang: str = 'en', limit: int = 50, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Image]`
Return the ``File:`` media embedded in an article.

Only titles are resolved here; for direct URLs, thumbnails and licence metadata use `netgo.wiki.file_info` on each result.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `limit`: Maximum number of images to fetch.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `Image` with their ``File:`` titles.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import images
>>> imgs = images("Python (programming language)")
>>> imgs[0].title.startswith("File:")
True
```

### `pageinfo(title: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> dict`
Return basic metadata about an article.

Includes the canonical URL, display title, last touched timestamp and pageid, exposed as a plain dict since the shape varies a lot.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A dict with ``pageid``, ``title``, ``fullurl``, ``displaytitle``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import pageinfo
>>> info = pageinfo("Bread")
>>> info["fullurl"].endswith("/Bread")
True
```

### `page(title: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> netgo.wiki.models.Article`
Fetch an article's structure in one aggregated object.

Combines the intro summary, the section outline, the outgoing links, the categories and the image list in a single `Article` using one API round-trip per property available in ``prop``.

**Args:**
- `title`: The article title.
- `lang`: Language code of the Wikipedia edition.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A populated `Article`.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the article does not exist.

**Example:**
```python
>>> from netgo.wiki import page
>>> art = page("Bread")
>>> bool(art.summary)
True
```

### `random(lang: str = 'en', limit: int = 1, namespace: int = 0, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.WikiResult]`
Return random article titles from a Wikipedia edition.

Handy for building "explore" features or sampling corpora. The API picks uniformly among the pages of the requested namespace.

**Args:**
- `lang`: Language code of the Wikipedia edition.
- `limit`: Number of random titles to return.
- `namespace`: Namespace to sample from (0 = articles).
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `WikiResult` with only the title filled in.  

**Example:**
```python
>>> from netgo.wiki import random
>>> hits = random(limit=2)
>>> len(hits)
2
```

### `geo_search(lat: float, lon: float, radius: int = 1000, limit: int = 10, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.GeoResult]`
Find articles located near a coordinate.

Uses ``list=geosearch``: every hit carries its coordinates and the distance (in metres) from the queried point, so you can power "near me" features or location-aware recommendations.

**Args:**
- `lat`: Latitude of the centre point.
- `lon`: Longitude of the centre point.
- `radius`: Search radius in metres.
- `limit`: Maximum number of hits.
- `lang`: Language code of the Wikipedia edition.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of `GeoResult`, nearest first.  

**Example:**
```python
>>> from netgo.wiki import geo_search
>>> hits = geo_search(51.5074, -0.1278, radius=5000, limit=2)
>>> hits[0].dist < 5000
True
```

### `search_many(queries: Iterable[str], *, lang: str = 'en', max_workers: int = 4, **kwargs) -> dict[str, list[netgo.wiki.models.WikiResult]]`
Run Wikipedia full-text `search` for several queries in parallel.

Follows the same contract as `netgo.search.search_many`: every query is executed in a thread pool; a failing query maps to an empty list and its exception is stored under ``"<query>_error"``.

**Args:**
- `queries`: An iterable of search queries.
- `lang`: Language code of the Wikipedia edition.
- `max_workers`: Size of the thread pool.
- `kwargs`: Forwarded to `search` (e.g. ``limit``).

**Returns:**
- A mapping of ``query -> list[WikiResult]``.  

**Example:**
```python
>>> from netgo.wiki import search_many
>>> out = search_many(["cats", "dogs"], limit=3)
>>> list(out)
['cats', 'dogs']
```