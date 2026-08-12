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
  aliases, sitelinks.
- **Wikimedia Commons** — image search, file URLs, thumbnails, licences.
- **Wiktionary** — definitions, etymology, languages of a word.

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

## Documentation

The full API reference (every function, class and parameter, generated from the
docstrings) lives in [`docs/`](docs/). Regenerate it with:

```bash
python scripts/generate_docs.py
```

## Notes

- This scrapes public search-engine result pages. Engines may throttle or
  block requests from datacenter IPs; add `delay` between calls, or use the
  alternate engine when one is blocked.
- The Wikimedia APIs are public and free, but be polite: reuse a single
  `WikiClient`, keep `delay` for batch loops, and set a descriptive
  `User-Agent` (see `netgo/wiki/client.py`).
- Check each engine's terms of service for your use case.