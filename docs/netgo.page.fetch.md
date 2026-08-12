# Fetch a web page and reduce it to its main content.

`fetch` requests the URL with a browser-like ``User-Agent``, parses the HTML, extracts the article body (dropping the site template) and wraps the result in a `netgo.page.models.Page`.

Non-HTML payloads (PDFs, images, raw API responses) and pages that yield no extractable prose raise `netgo.page.errors.PageParseError`; transport and HTTP errors raise `netgo.page.errors.PageFetchError`.

**Example:**
```python
>>> from netgo import page
>>> p = page.fetch("https://www.bbc.co.uk/news/science-environment-56837908")
>>> p.site
'bbc.co.uk'
>>> bool(p.paragraphs)
True
```

### `fetch(url: str, *, timeout: int = 10, delay: float = 0.0, session: requests.sessions.Session | None = None, headers: dict | None = None) -> netgo.page.models.Page`
Fetch ``url`` and return its readable main content.

Downloads the page, filters out the site template (navigation, headers, footers, sidebars, banners, comment widgets) and returns the remaining article as a `Page`.

**Args:**
- `url`: The page to read.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).
- `session`: Optional `requests.Session` to reuse (proxies, timeouts, cookies are honoured).
- `headers`: Extra HTTP headers merged over the browser defaults.

**Returns:**
- A `Page` with the extracted title, site, plain-text body, paragraph list and the cleaned content HTML.  

**Raises:**
- `PageFetchError`: When the request fails or returns a non-2xx response.
- `PageParseError`: When the payload is not readable HTML or the page has no extractable main content.