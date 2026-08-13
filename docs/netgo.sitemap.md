# netgo.sitemap - fetch, discover and parse XML sitemaps.

Talks to the sitemap protocol (sitemaps.org) through a few plain entry points:

- `parse` - parse sitemap content (XML URL sets, sitemap indexes

or plain-text URL lists) into a `Sitemap`, resolving relative locations against a base URL.

- `load` - fetch a sitemap URL (plain or gzip-compressed) and

parse it.

- `discover` - find the ``Sitemap:`` URLs a site declares in its

``robots.txt``.

- `crawl` - recursively follow a sitemap index and collect every

URL entry across the whole tree.

- `filter_by_prefix` - crawl a sitemap tree and keep only the URLs

that start with a given prefix (e.g. ``page_1``, ``page_2``, ...).

Every function returns structured dataclasses (see `netgo.sitemap.models`) and raises ``SitemapError`` subclasses on failure, so a ``try/except SitemapError`` covers the whole subpackage.

**Example:**
```python
>>> from netgo import sitemap
>>> sm = sitemap.load("https://www.example.com/sitemap.xml")
>>> first = sm.entries[0]
>>> first.loc.startswith("http")
True
>>> for child in sm.children:
...     print(child.startswith("http"))
True
```