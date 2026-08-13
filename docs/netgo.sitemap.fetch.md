# Fetch sitemaps over HTTP and discover them through robots.txt.

`load` downloads a sitemap (plain or gzip-compressed, index or URL set) and parses it into a `netgo.sitemap.models.Sitemap`. `discover` finds the ``Sitemap:`` URLs a site declares in its ``robots.txt``, and `crawl` recursively follows ``<sitemapindex>`` children to collect every URL across all sub-sitemaps. `filter_by_prefix` crawls a tree and keeps only the URLs that start with a given prefix.

Transport and HTTP failures raise `netgo.sitemap.errors.SitemapFetchError`; bodies that cannot be read raise `netgo.sitemap.errors.SitemapParseError`.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> sm.urls[0]
'https://www.example.com/'
```

### `load(url: str, *, timeout: int = 10, delay: float = 0.0, session: requests.sessions.Session | None = None, headers: dict | None = None) -> netgo.sitemap.models.Sitemap`
Fetch a sitemap URL and parse it into a `Sitemap`.

Handles plain and gzip-compressed sitemap bodies (both a real ``Content-Encoding`` header and a bare ``sitemap.xml.gz`` served without one), and resolves relative locations against the final URL.

**Args:**
- `url`: The sitemap (or sitemap index) URL.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).
- `session`: Optional `requests.Session` to reuse (proxies, cookies are honoured).
- `headers`: Extra HTTP headers merged over the browser defaults.

**Returns:**
- A `Sitemap` carrying the URL entries or child locations.  

**Raises:**
- `SitemapFetchError`: When the request fails or returns a non-2xx response.
- `SitemapParseError`: When the body is empty or not a valid sitemap.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> sm.kind
'urlset'
```

### `discover(url_or_domain: str, *, timeout: int = 10, delay: float = 0.0, session: requests.sessions.Session | None = None, headers: dict | None = None) -> list[str]`
Return the ``Sitemap:`` URLs a site declares in its robots.txt.

Accepts a full URL (``https://example.com/any/path``) or a bare domain (``example.com``); robots.txt is looked up on the origin, so a site \*must\* advertise its sitemaps there for this to find them. A missing robots.txt (404) simply yields an empty list.

**Args:**
- `url_or_domain`: A site URL, or a bare hostname.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).
- `session`: Optional `requests.Session` to reuse.
- `headers`: Extra HTTP headers merged over the browser defaults.

**Returns:**
- The list of sitemap URLs declared by robots.txt (empty when the site advertises none).  

**Raises:**
- `SitemapFetchError`: When robots.txt cannot be downloaded for a reason other than a missing file (404).

**Example:**
```python
>>> from netgo import sitemap
>>> urls = sitemap.discover("https://www.example.com")
>>> urls[0].startswith("http")
True
```

### `crawl(url: str, *, max_entries: int = 1000, timeout: int = 10, delay: float = 0.0, session: requests.sessions.Session | None = None, headers: dict | None = None) -> list[netgo.sitemap.models.SitemapEntry]`
Fetch a whole sitemap tree and return every URL entry.

Starting from a sitemap URL, follows ``<sitemapindex>`` children recursively (skipping already-visited sub-sitemaps), downloads each child, and collects all ``<url>`` entries across the tree in document order, deduplicated by location.

**Args:**
- `url`: A sitemap or sitemap index URL.
- `max_entries`: Stop after collecting this many entries.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before every request (rate limiting).
- `session`: Optional `requests.Session` to reuse.
- `headers`: Extra HTTP headers merged over the browser defaults.

**Returns:**
- A list of `SitemapEntry`, deduplicated by ``loc``.  

**Raises:**
- `SitemapFetchError`: When any sitemap in the tree fails to load.
- `SitemapParseError`: When any sitemap body cannot be read.

**Example:**
```python
>>> from netgo import sitemap
>>> urls = sitemap.crawl("https://www.example.com/sitemap.xml")
>>> urls[0].loc.startswith("http")
True
```

### `filter_by_prefix(url: str, prefix: str, *, max_entries: int = 1000, timeout: int = 10, delay: float = 0.0, session: requests.sessions.Session | None = None, headers: dict | None = None) -> list[netgo.sitemap.models.SitemapEntry]`
Crawl a sitemap tree and return only the entries starting with a prefix.

Crawls the whole sitemap tree exactly like `crawl`, then keeps only the URL entries whose ``loc`` starts with ``prefix``. Use it to grab every page of a numbered family (``https://example.com/page_1``, ``https://example.com/page_2``, ...) straight from the sitemap.

**Args:**
- `url`: A sitemap or sitemap index URL.
- `prefix`: URL prefix to match against each entry's ``loc``.
- `max_entries`: Stop after collecting this many entries in the crawl.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before every request (rate limiting).
- `session`: Optional `requests.Session` to reuse.
- `headers`: Extra HTTP headers merged over the browser defaults.

**Returns:**
- A list of `SitemapEntry` whose ``loc`` starts with ``prefix``, in crawl order.  

**Raises:**
- `SitemapFetchError`: When any sitemap in the tree fails to load.
- `SitemapParseError`: When any sitemap body cannot be read.

**Example:**
```python
>>> from netgo import sitemap
>>> pages = sitemap.filter_by_prefix(
...     "https://www.example.com/sitemap.xml",
...     "https://www.example.com/page_",
... )
>>> pages[0].loc.startswith("https://www.example.com/page_")
True
```

### `_origin(url: str) -> str`
Return the ``scheme://netloc`` of a URL, defaulting to https.

### `_robots_sitemaps(text: str) -> list[str]`
Extract the ``Sitemap:`` lines from a robots.txt body.