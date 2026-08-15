# netgo

A lightweight Python toolkit for scraping search engines and getting the
links back, and for talking to the Wikimedia APIs.

netgo exposes a single, engine-agnostic API on top of several search
backends, so you can switch or combine engines without touching your
data model. Every backend returns the same `netgo.Result` objects,
ranked by the engine.

On the Wikimedia side, `netgo.wiki` wraps the MediaWiki Action API
behind one shared `WikiClient` session: Wikipedia search and article
structure, Wikidata entities and facts, Wikimedia Commons files and
Wiktionary definitions.

**Search backends**

- **Google** — the default.
- **Bing** — selected with `engine="bing"`.

**Wikimedia APIs**

- **Wikipedia** — full-text search, summaries, paragraphs, sections,
  links, backlinks, categories, images, random pages, geo search.
- **Wikidata** — titles → QIDs, entities, label search, claims,
  aliases, sitelinks, raw SPARQL.
- **Wikimedia Commons** — image search, file URLs, thumbnails, licences.
- **Wiktionary** — definitions, etymology, languages of a word.

**Page reading**

- **`netgo.fetch`** — download any web page and get back just its main
  content, with the site template (nav, headers, footers, sidebars,
  banners) filtered out.

When a search page is throttled or blocked, netgo raises `SearchBlockedError`
instead of silently returning nothing, so automation can detect and react.

## Install

```bash
pip install git+https://github.com/FrancoFantomius/netgo.git
```

Requires Python 3.9+.

## Getting started

```python
import netgo

# Google (default), num results per page
results = netgo.search("python web scraping", num=10)

# Bing, same interface
results = netgo.search("python web scraping", num=10, engine="bing")

for r in results:
    print(r.position, r.title)
    print("  ", r.url)
    print("  ", r.snippet[:80])
```

Run several queries in parallel:

```python
out = netgo.search_many(["cats", "dogs"], max_workers=4, num=5)
for query, results in out.items():
    print(query, [r.url for r in results])
```

## Viewing a page

Fetch any URL and read just its real content; the site template
(navigation, headers, footers, sidebars, banners, comment widgets) is
filtered out:

```python
import netgo

page = netgo.fetch("https://www.bbc.co.uk/news/science-environment-56837908")
print(page.title)      # "Climate change: Biggest..."
print(page.site)       # "bbc.co.uk"
print(page.paragraphs[:3])
```

`netgo.fetch` returns a `Page` with the extracted title, domain, cleaned
plain-text body (`text` and `paragraphs`), the content HTML and the raw
HTML as the server sent it (`raw`). ``PageError``
is raised for transport failures (`PageFetchError`) or pages with no
readable content (`PageParseError`), so automation can detect and react.

## Sitemaps

Discover, parse and crawl XML sitemaps (URL sets, sitemap indexes and
plain-text sitemaps):

```python
import netgo

# Sitemaps a site declares in its robots.txt
urls = netgo.sitemap.discover("https://www.example.com")

# View a single sitemap, and every URL it announces
sm = netgo.sitemap.load("https://www.example.com/sitemap.xml")
print(sm.kind)              # "urlset" | "sitemapindex" | "text"
for entry in sm:            # SitemapEntry with loc/lastmod/...
    print(entry.loc)

# Follow a sitemap index down to every page URL across all children
pages = netgo.sitemap.crawl("https://www.example.com/sitemap_index.xml")

# Every page whose URL starts with a given prefix (page_1, page_2, ...)
paged = netgo.sitemap.filter_by_prefix(
    "https://www.example.com/sitemap_index.xml",
    "https://www.example.com/page_",
)

# Or filter a sitemap you already loaded
subset = sm.by_prefix("https://www.example.com/page_")
```

`parse` handles raw content without the network (namespace-agnostic, resolves
relative locations), `load` also unpacks gzip-compressed sitemaps, and
`SitemapError` subclasses (`SitemapFetchError`, `SitemapParseError`) make
failures detectable.

## Wikipedia APIs

```python
import netgo.wiki as wiki

# Wikipedia: full-text search and article structure
hits = wiki.search("python programming", limit=5)
for h in hits:
    print(h.title, h.wordcount)

lead = wiki.summary("Bread", sentences=2)
paras = wiki.paragraphs("Bread")
toc = wiki.sections("Bread")
near = wiki.geo_search(41.89, 12.49, radius=2000, limit=5)

# Wikidata: resolve a title to its QID and read its facts
qid = wiki.wikidata_id("Bread")
item = wiki.entity(qid, language="en")
print(item.labels["en"], item.claims.get("P279", []))

# Wikidata: raw SPARQL (default query returns items with a P624 guidance system)
rows = wiki.sparql(language="en")
print(rows[0]["itemLabel"], rows[0]["guidanceSystemLabel"])

# Wikimedia Commons: find files and their metadata
files = wiki.search_images("sunflower", limit=3)
meta = wiki.file_info(files[0].name)

# Wiktionary: dictionary data
entry = wiki.wiktionary_definition("serendipity")
print(entry.pos, entry.definitions)
```

Every function accepts `lang=` to pick a Wikipedia/Wiktionary edition,
reuses a shared `WikiClient` session, and raises `WikiError` subclasses
(`WikiAPIError`, `WikiNotFoundError`) on failure.

## Examples

Runnable, end-to-end scripts that use the library against the live network
live in [`examples/`](examples/), covering search engines, page reading and
each Wikimedia API:

```bash
python examples/01_search.py
python examples/08_research_pipeline.py
```

See [`examples/README.md`](examples/README.md) for the full list.

## Documentation

The documentation is hosted at **[francofantomius.com/netgo/](https://francofantomius.com/netgo/)**.

The documentation is built with [VitePress](https://vitepress.dev/) and generated directly from Python docstrings. To regenerate the documentation files locally:

```bash
python scripts/generate_docs.py
```

To run the VitePress documentation server locally:

```bash
npm install
npm run docs:dev
```

## Notes

- This scrapes public search-engine result pages. Engines may throttle or
  block requests from datacenter IPs; add `delay` between calls, or use the
  alternate engine when one is blocked.
- The Wikimedia APIs are public and free, but be polite: reuse a single
  `WikiClient`, keep `delay` for batch loops, and set a descriptive
  `User-Agent` (see `netgo/wiki/client.py`).
- Check each engine's terms of service for your use case.