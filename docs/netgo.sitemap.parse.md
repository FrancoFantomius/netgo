# Parse sitemap content into structured :class:`~netgo.sitemap.models.Sitemap`.

Handles all three sitemap formats defined by sitemaps.org:

1. \*\*URL sets\*\* (``<urlset>``) - every ``<url>`` becomes a `netgo.sitemap.models.SitemapEntry` with its ``loc``, ``lastmod``, ``changefreq`` and ``priority``. 2. \*\*Sitemap indexes\*\* (``<sitemapindex>``) - every nested ``<loc>`` is collected as a child sitemap URL. 3. \*\*Plain-text sitemaps\*\* - one URL per line.

Parsing is namespace-agnostic (the sitemap schema tags are recognized no matter the ``xmlns``), and relative or protocol-relative ``<loc>`` values are resolved against ``base_url`` using `urllib.parse.urljoin`.

Content that cannot be read - empty payloads, malformed XML, unrecognized root elements, text without URLs - raises `netgo.sitemap.errors.SitemapParseError`.

**Example:**
```python
>>> from netgo.sitemap import parse, SitemapEntry
>>> xl = (
...     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
...     "<url><loc>/</loc><lastmod>2026-01-01</lastmod>"
...     "<changefreq>daily</changefreq><priority>1.0</priority></url>"
...     "</urlset>"
... )
>>> sm = parse(xl, base_url="https://example.com/sitemap.xml")
>>> sm.kind
'urlset'
>>> sm.urls
['https://example.com/']
```

### `parse(content: str | bytes, *, base_url: str = '') -> netgo.sitemap.models.Sitemap`
Parse sitemap content (XML or plain text) into a `Sitemap`.

Auto-detects the format from the payload: content beginning with an XML element (``<urlset>``, ``<sitemapindex>`` or any other root, with or without a namespace) is parsed as XML, anything else is treated as a plain-text URL list. Relative ``<loc>`` values are resolved against ``base_url`` with `urllib.parse.urljoin`, so absolute URLs pass through unchanged.

**Args:**
- `content`: The raw sitemap body, as ``str`` or ``bytes``.
- `base_url`: The sitemap's own URL; used to resolve relative and protocol-relative locations. Ignored when empty.

**Returns:**
- A `Sitemap` with ``kind`` set to ``"urlset"``, ``"sitemapindex"`` or ``"text"``.  

**Raises:**
- `SitemapParseError`: When the content is empty, not well formed, uses an unknown root element, or holds no URL at all.

**Example:**
```python
>>> from netgo.sitemap import parse
>>> sm = parse(
...     '<sitemapindex><sitemap><loc>/posts/sitemap.xml</loc></sitemap></sitemapindex>',
...     base_url="https://example.com/sitemap.xml",
... )
>>> sm.kind
'sitemapindex'
>>> sm.children
['https://example.com/posts/sitemap.xml']
```

### `_to_bytes(content: str | bytes) -> bytes`
Return ``content`` as bytes without a conflicting XML declaration.

### `_local_name(tag: str) -> str`
Strip a ``{namespace}`` prefix from an ElementTree tag name.

### `_child_text(element: xml.etree.ElementTree.Element, name: str) -> str | None`
Return the direct ``<loc>``/``<lastmod>``-style text of a child.