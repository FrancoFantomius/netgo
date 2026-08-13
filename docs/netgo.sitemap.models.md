# Data models returned by the :mod:`netgo.sitemap` wrappers.

`Sitemap` is the parsed representation of a sitemap document; it carries either the URL entries of a ``<urlset>`` (or plain-text sitemap) or the child sitemap locations of a ``<sitemapindex>``. Every ``<loc>`` value is resolved against the sitemap's own URL, so relative and protocol-relative references never leak through.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> sm.entries[0].loc
'https://www.example.com/'
>>> sm.urls[0]
'https://www.example.com/'
```

### class `SitemapEntry`
```python
SitemapEntry(loc: 'str', lastmod: 'str' = '', changefreq: 'str' = '', priority: 'float' = 0.0) -> None
```
A single ``<url>`` entry in a sitemap.

``loc`` is the page URL (always absolute, resolved against the sitemap that declared it); ``lastmod``, ``changefreq`` and ``priority`` mirror the optional metadata of the same name, falling back to sensible defaults when omitted.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> sm.entries[0].loc
'https://www.example.com/'
```
**Fields:**
- `loc`
- `lastmod`
- `changefreq`
- `priority` = 0.0

### class `Sitemap`
```python
Sitemap(url: 'str' = '', kind: 'str' = 'urlset', entries: 'list[SitemapEntry]' = <factory>, children: 'list[str]' = <factory>) -> None
```
A parsed sitemap document.

``kind`` is ``"urlset"``, ``"sitemapindex"`` or ``"text"``. ``entries`` holds the `SitemapEntry` list of a URL sitemap and ``children`` the child sitemap locations of an index; the other collection stays empty on each side. ``url`` is where the document was fetched from (empty for a raw `netgo.sitemap.parse` without a base URL).

Iterating over a sitemap yields its ``entries``; ``urls`` is a shortcut for their ``loc`` values.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> bool(sm)
True
>>> for entry in sm:
...     print(entry.loc)
https://www.example.com/
```
**Fields:**
- `url`
- `kind` = 'urlset'
- `entries`
- `children`