# Code Examples

Runnable, end-to-end examples demonstrating how to use `netgo` for web search, parallel query execution, page content extraction, sitemap parsing, and Wikimedia integrations.

All source files are available in the **[GitHub Examples Directory](https://github.com/FrancoFantomius/netgo/tree/master/examples)**.

## Index of Examples

| Example | Description | Source Link |
| :--- | :--- | :--- |
| [01_search.py](#01-searchpy) | Search Google and Bing through the same engine-agnostic API. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/01_search.py) |
| [02_parallel_search.py](#02-parallel-searchpy) | Run many search queries at once with ``netgo.search_many``. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/02_parallel_search.py) |
| [03_read_page.py](#03-read-pagepy) | Fetch any web page and read just its main content. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/03_read_page.py) |
| [04_wikipedia.py](#04-wikipediapy) | Deep-dive into a Wikipedia article with ``netgo.wiki``. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/04_wikipedia.py) |
| [05_wikidata.py](#05-wikidatapy) | From a Wikipedia title to structured Wikidata facts. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/05_wikidata.py) |
| [06_commons.py](#06-commonspy) | Find Wikimedia Commons files and inspect their metadata. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/06_commons.py) |
| [07_wiktionary.py](#07-wiktionarypy) | Dictionary data from Wiktionary. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/07_wiktionary.py) |
| [08_research_pipeline.py](#08-research-pipelinepy) | The full journey in one script: search -> fetch -> enrich with Wikipedia. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/08_research_pipeline.py) |
| [09_sitemap.py](#09-sitemappy) | Discover and read a site's XML sitemaps. | [View on GitHub](https://github.com/FrancoFantomius/netgo/blob/master/examples/09_sitemap.py) |

---

## `01_search.py`

**Description:** Search Google and Bing through the same engine-agnostic API.

Every backend returns the same list of ``netgo.Result`` objects, so
switching engines never touches your data models or downstream code.

**GitHub Source:** [01_search.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/01_search.py)

```python
"""Search Google and Bing through the same engine-agnostic API.

Every backend returns the same list of ``netgo.Result`` objects, so
switching engines never touches your data models or downstream code.
"""

# Import the unified search entry point from netgo
from netgo import search


def show(label, results):
    """Helper to display search results in a readable format.
    
    Each `Result` object has:
      - `position`: 1-based index on the search engine results page
      - `title`: Extracted title text
      - `url`: Direct link to the result
      - `snippet`: Text preview or snippet from the search engine
    """
    print(f"\n== {label} ==")
    for r in results:
        print(f"  #{r.position}: {r.title}")
        print(f"          {r.url}")
        print(f"          {r.snippet[:100]}")


def main():
    # -------------------------------------------------------------
    # 1. Standard Google Search (default engine)
    # -------------------------------------------------------------
    # `num`: number of search results to fetch (default is 10)
    query = "python web scraping"
    print("Executing standard Google search...")
    show("Google (default)", search(query, num=5))

    # -------------------------------------------------------------
    # 2. Bing Search using the identical interface
    # -------------------------------------------------------------
    # `engine="bing"`: select the Bing backend instead of Google
    print("Executing Bing search...")
    show("Bing", search(query, num=5, engine="bing"))

    # -------------------------------------------------------------
    # 3. Paginated Search
    # -------------------------------------------------------------
    # `start`: offset to begin results from (e.g., start=5 gets page 2 if num=5)
    print("Fetching paginated results...")
    show(
        "Google, paginated page 2",
        search(query, num=5, start=5),
    )

    # -------------------------------------------------------------
    # 4. Search with Safe Search and Language Filter
    # -------------------------------------------------------------
    # `safe=True`: enable strict safe search filtering
    # `lang="it"`: prioritize results in Italian
    print("Executing filtered search...")
    show(
        "Bing, safe search on, Italian",
        search(query, num=5, engine="bing", safe=True, lang="it"),
    )


if __name__ == "__main__":
    main()
```

---

## `02_parallel_search.py`

**Description:** Run many search queries at once with ``netgo.search_many``.

Queries execute in parallel across a thread pool. A failing query does not
abort the others: it maps to an empty list and stores its exception under
``"<query>_error"``.

**GitHub Source:** [02_parallel_search.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/02_parallel_search.py)

```python
"""Run many search queries at once with ``netgo.search_many``.

Queries execute in parallel across a thread pool. A failing query does not
abort the others: it maps to an empty list and stores its exception under
``"<query>_error"``.
"""

# Import the parallel search utility from netgo
from netgo import search_many


def main():
    # Define a list of search queries to execute concurrently
    queries = [
        "python asyncio tutorial",
        "web scraping best practices",
        "rust vs go 2025",
        "sqlite full text search",
    ]

    # -------------------------------------------------------------
    # Execute batch search in parallel
    # -------------------------------------------------------------
    # `engine="bing"`: specify search engine backend ("google" or "bing")
    # `num=3`: number of results requested per query
    # `max_workers=4`: size of the concurrent thread pool
    print(f"Executing {len(queries)} queries in parallel...")
    out = search_many(queries, engine="bing", num=3, max_workers=4)

    # -------------------------------------------------------------
    # Process results and inspect possible errors
    # -------------------------------------------------------------
    for query, results in out.items():
        # netgo stores exceptions under `<query>_error` keys so the rest
        # of the batch continues without crashing
        if query.endswith("_error"):
            print(f"  [ERROR] {query} raised {type(results).__name__}: {results}")
        elif results:
            print(f"\nResults for {query!r} ({len(results)} found):")
            for r in results:
                print(f"  #{r.position} {r.title}")
                print(f"       URL: {r.url}")
        else:
            print(f"\n{query!r}: no results returned (blocked or empty page)")


if __name__ == "__main__":
    main()
```

---

## `03_read_page.py`

**Description:** Fetch any web page and read just its main content.

``netgo.fetch`` strips the site template (navigation, headers, footers,
sidebars, banners) and leaves the actual article behind as a ``Page`` object.

**GitHub Source:** [03_read_page.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/03_read_page.py)

```python
"""Fetch any web page and read just its main content.

``netgo.fetch`` strips the site template (navigation, headers, footers,
sidebars, banners) and leaves the actual article behind as a ``Page`` object.
"""

# Import the fetch helper and base error class
from netgo import PageError, fetch


def main():
    # Target URL to fetch and clean
    url = "https://www.bbc.co.uk/news/science-environment-56837908"

    # -------------------------------------------------------------
    # Fetch and parse the page content
    # -------------------------------------------------------------
    # `fetch(url)` downloads the HTML, detects encoding, strips boilerplate
    # tags (nav, footer, header, scripts, styles), and extracts the article.
    # Handles transport and parsing failures gracefully via `PageError`.
    try:
        page = fetch(url, timeout=15)
    except PageError as exc:
        print(f"Failed to fetch or parse {url}: {exc}")
        return

    # -------------------------------------------------------------
    # Inspect metadata and cleaned content
    # -------------------------------------------------------------
    # `page.title`: Extracted title of the document/article
    # `page.site`: Cleaned hostname/domain
    # `page.url`: Canonical or final fetched URL
    print(f"Title : {page.title}")
    print(f"Site  : {page.site}")
    print(f"URL   : {page.url}\n")

    # `page.paragraphs`: List of non-empty cleaned plain-text paragraphs
    print(f"== First 3 paragraphs of {len(page.paragraphs)} total ==")
    for idx, para in enumerate(page.paragraphs[:3], 1):
        print(f"\n[Paragraph {idx}]")
        print(para)

    # `page.html`: Extracted and cleaned main content HTML (excluding boilerplate)
    # `page.raw`: Raw HTML body returned by the HTTP server
    print("\n== Content HTML snippet ==")
    print(page.html[:160].replace("\n", " ") + "...")


if __name__ == "__main__":
    main()
```

---

## `04_wikipedia.py`

**Description:** Deep-dive into a Wikipedia article with ``netgo.wiki``.

Searches for the article, then walks its structure: summary, section
outline, outgoing links, backlinks, categories and embedded images.

**GitHub Source:** [04_wikipedia.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/04_wikipedia.py)

```python
"""Deep-dive into a Wikipedia article with ``netgo.wiki``.

Searches for the article, then walks its structure: summary, section
outline, outgoing links, backlinks, categories and embedded images.
"""

# Import the high-level Wikipedia API helpers
import netgo.wiki as wiki


def main():
    title = "Python (programming language)"

    # -------------------------------------------------------------
    # 1. Search Wikipedia articles
    # -------------------------------------------------------------
    # `wiki.search(query, limit=3)`: performs full-text title and content search
    hits = wiki.search(title, limit=3)
    print(f"== Search Hits ({len(hits)}) ==")
    for h in hits:
        print(f"  {h.title!r} (Word count: {h.wordcount}, Size: {h.size} bytes)")

    # -------------------------------------------------------------
    # 2. Retrieve structured page details
    # -------------------------------------------------------------
    # `wiki.page(title)`: loads page summary, full text, sections, links, and categories
    page = wiki.page(title)
    print(f"\n== Page: {page.title} ==")
    print(f"  URL     : {page}")
    print(f"  Summary : {page.summary[:180]}...")

    # -------------------------------------------------------------
    # 3. Table of Contents & Sections
    # -------------------------------------------------------------
    # `page.sections`: list of `Section` objects containing heading title and nesting level
    print(f"\n== Table of Contents ({len(page.sections)} sections) ==")
    for s in page.sections[:8]:
        indent = "  " * (s.level - 1)
        print(f"  {indent}[{s.index}] {s.title}")

    # -------------------------------------------------------------
    # 4. Categories & Taxonomy
    # -------------------------------------------------------------
    # `page.categories`: list of Wikipedia categories the page belongs to
    print(f"\n== Categories ({len(page.categories)}) ==")
    for c in page.categories[:6]:
        print(f"  - {c.title}")

    # -------------------------------------------------------------
    # 5. Outgoing Links & Embedded Images
    # -------------------------------------------------------------
    # `page.links`: internal links to other Wikipedia articles
    print(f"\n== Outgoing Links ({len(page.links)}) ==")
    for l in page.links[:6]:
        print(f"  -> {l.title}")

    # `page.images`: file names of images referenced on the page
    print(f"\n== Embedded Images ({len(page.images)}) ==")
    for i in page.images[:5]:
        print(f"  - {i.title}")

    # -------------------------------------------------------------
    # 6. Backlinks (Pages linking to this article)
    # -------------------------------------------------------------
    # `wiki.backlinks(title, limit=5)`: queries which other articles reference this page
    print(f"\n== Backlinks (What links here) ==")
    for l in wiki.backlinks(title, limit=5):
        print(f"  <- {l.title}")


if __name__ == "__main__":
    main()
```

---

## `05_wikidata.py`

**Description:** From a Wikipedia title to structured Wikidata facts.

Resolves the article to its QID, fetches the full entity and reads its
labels, claims, aliases and sitelinks. Also executes raw SPARQL queries.

**GitHub Source:** [05_wikidata.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/05_wikidata.py)

```python
"""From a Wikipedia title to structured Wikidata facts.

Resolves the article to its QID, fetches the full entity and reads its
labels, claims, aliases and sitelinks. Also executes raw SPARQL queries.
"""

# Import Wikidata helpers from netgo.wiki
import netgo.wiki as wiki

# Common Wikidata Property ID mapping for readable output
PROPS = {
    "P31": "instance of",
    "P279": "subclass of",
    "P571": "inception",
    "P112": "founded by",
}


def main():
    title = "Python (programming language)"

    # -------------------------------------------------------------
    # 1. Resolve Wikipedia title to Wikidata QID
    # -------------------------------------------------------------
    # `wikidata_id(title)`: looks up the unique entity identifier (e.g. Q28865)
    qid = wiki.wikidata_id(title)
    print(f"Article: {title!r} -> Wikidata QID: {qid}")

    # -------------------------------------------------------------
    # 2. Fetch full entity model
    # -------------------------------------------------------------
    # `entity(qid, language="en")`: loads structured data (claims, labels, descriptions)
    item = wiki.entity(qid, language="en")
    print(f"\n== Wikidata Entity: {item.qid} ==")
    print(f"  English Label : {item.labels.get('en')}")
    print(f"  Description   : {item.descriptions.get('en')}")

    # -------------------------------------------------------------
    # 3. Read structured claims & statements
    # -------------------------------------------------------------
    # `item.claims`: dictionary mapping property IDs (e.g., P31) to claim values
    print("\n== Key Claims ==")
    for pid, claims in item.claims.items():
        if pid in PROPS:
            values = [c.value for c in claims]
            print(f"  {PROPS[pid]:>14} ({pid}): {values}")

    # -------------------------------------------------------------
    # 4. Aliases and multi-lingual Sitelinks
    # -------------------------------------------------------------
    # `item.aliases`: alternative names / search terms
    print(f"\n== Aliases (en) ==\n  {item.aliases.get('en', [])}")

    # `item.sitelinks`: mappings across Wikimedia projects (Wikipedia, Wikiquote, etc.)
    print(f"\n== Sitelinks ({len(item.sitelinks)} connected sites) ==")
    for site in ["enwiki", "itwiki", "dewiki", "frwiki", "eswiki"]:
        if site in item.sitelinks:
            print(f"  {site:8}: {item.sitelinks[site]}")

    # -------------------------------------------------------------
    # 5. Execute raw SPARQL query
    # -------------------------------------------------------------
    # `wiki.sparql(...)`: executes SPARQL on the Wikidata query service
    print("\n== Raw SPARQL Query (Items with guidance system P624) ==")
    rows = wiki.sparql(language="en")
    for row in rows[:5]:
        item_lbl = row.get("itemLabel")
        sys_lbl = row.get("guidanceSystemLabel")
        print(f"  {row.get('item')}: {item_lbl} -> {sys_lbl}")


if __name__ == "__main__":
    main()
```

---

## `06_commons.py`

**Description:** Find Wikimedia Commons files and inspect their metadata.

``search_images`` returns matching file names; ``file_info`` resolves a
name to its direct download URL, thumbnail, MIME type, dimensions, and licence.

**GitHub Source:** [06_commons.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/06_commons.py)

```python
"""Find Wikimedia Commons files and inspect their metadata.

``search_images`` returns matching file names; ``file_info`` resolves a
name to its direct download URL, thumbnail, MIME type, dimensions, and licence.
"""

# Import Wikimedia Commons helpers from netgo.wiki
import netgo.wiki as wiki


def main():
    query = "sunflower"

    # -------------------------------------------------------------
    # 1. Search media files on Wikimedia Commons
    # -------------------------------------------------------------
    # `search_images(query, limit=3)`: finds files matching the search terms
    hits = wiki.search_images(query, limit=3)
    print(f"== Media files matching {query!r} ({len(hits)} returned) ==")
    for f in hits:
        print(f"  - {f.name}")

    # -------------------------------------------------------------
    # 2. Inspect detailed file metadata and image URLs
    # -------------------------------------------------------------
    # `file_info(name, thumb_width=640)`: retrieves resolution, licence,
    # author, and generates scaled thumbnail links.
    for hit in hits[:2]:
        info = wiki.file_info(hit.name, thumb_width=640)
        print(f"\n== File Details: {info.name} ==")
        print(f"  Direct URL     : {info.url}")
        print(f"  Thumbnail (640): {info.thumburl}")
        print(f"  Dimensions     : {info.width} x {info.height} px")
        print(f"  Size & MIME    : {info.size} bytes ({info.mime})")
        print(f"  Licence        : {info.license}")
        print(f"  Artist/Author  : {info.artist}")
        print(f"  Description    : {info.description[:120]}...")

    # -------------------------------------------------------------
    # 3. Direct Image URL convenience helper
    # -------------------------------------------------------------
    # `image_url(name)`: fast single-step URL resolution
    print("\n== Quick Direct URL ==")
    print(f"  {wiki.image_url(hits[0].name)}")

    # -------------------------------------------------------------
    # 4. Fetch random Commons files
    # -------------------------------------------------------------
    # `random_file(limit=1)`: retrieves randomly selected file entries
    print("\n== Random Commons File ==")
    for r in wiki.random_file(limit=1):
        print(f"  - {r.name}")


if __name__ == "__main__":
    main()
```

---

## `07_wiktionary.py`

**Description:** Dictionary data from Wiktionary.

Reads the part of speech, numbered definitions, etymology and the set of
languages a word exists in, for any requested Wiktionary edition.

**GitHub Source:** [07_wiktionary.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/07_wiktionary.py)

```python
"""Dictionary data from Wiktionary.

Reads the part of speech, numbered definitions, etymology and the set of
languages a word exists in, for any requested Wiktionary edition.
"""

# Import Wiktionary helpers from netgo.wiki
import netgo.wiki as wiki


def main():
    word = "serendipity"

    # -------------------------------------------------------------
    # 1. Fetch structured definition entry
    # -------------------------------------------------------------
    # `wiktionary_definition(word, lang="en")`: fetches parsed dictionary entry
    entry = wiki.wiktionary_definition(word)
    print(f"== Entry: {entry.word} (Language Edition: {entry.lang}) ==")
    print(f"  Part of speech: {entry.pos or 'n/a'}")
    print("  Definitions:")
    for i, d in enumerate(entry.definitions, 1):
        print(f"    {i}. {d}")

    # -------------------------------------------------------------
    # 2. Extract word etymology
    # -------------------------------------------------------------
    # `wiki.etymology(word)`: retrieves origin and historical background
    etymology = wiki.etymology(word)
    if etymology:
        print(f"\n  Etymology: {etymology[:200]}...")

    # -------------------------------------------------------------
    # 3. Check language presence on Wiktionary
    # -------------------------------------------------------------
    # `wiki.languages(word)`: discovers all language sections defined for this entry
    langs = wiki.languages(word)
    print(f"\n  Defined in {len(langs)} language sections on en.wiktionary:")
    print(f"  {', '.join(langs[:8])}...")

    # -------------------------------------------------------------
    # 4. Search word titles with prefix matching
    # -------------------------------------------------------------
    # `wiki.wiktionary_search(prefix, limit=5)`: autocomplete/title suggestions
    prefix = word[:5]
    print(f"\n== Prefix search for {prefix!r} ==")
    for title in wiki.wiktionary_search(prefix, limit=5):
        print(f"  - {title}")

    # -------------------------------------------------------------
    # 5. Query non-English Wiktionary editions
    # -------------------------------------------------------------
    # `lang="it"`: query the Italian Wiktionary edition directly
    print("\n== Same word on Italian Wiktionary (lang='it') ==")
    it = wiki.wiktionary_definition(word, lang="it")
    print(f"  Part of speech: {it.pos or 'n/a'}")
    for d in it.definitions[:2]:
        print(f"    - {d}")


if __name__ == "__main__":
    main()
```

---

## `08_research_pipeline.py`

**Description:** The full journey in one script: search -> fetch -> enrich with Wikipedia.

1. Search a topic across web engines and select the top organic result.
2. Download the article content with ``netgo.fetch`` and clean the text.
3. Cross-reference the topic on Wikipedia and extract structured Wikidata facts.
This demonstrates how netgo's APIs combine into an end-to-end research pipeline.

**GitHub Source:** [08_research_pipeline.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/08_research_pipeline.py)

```python
"""The full journey in one script: search -> fetch -> enrich with Wikipedia.

1. Search a topic across web engines and select the top organic result.
2. Download the article content with ``netgo.fetch`` and clean the text.
3. Cross-reference the topic on Wikipedia and extract structured Wikidata facts.

This demonstrates how netgo's APIs combine into an end-to-end research pipeline.
"""

# Import the core netgo tools and Wikimedia client methods
from netgo import PageError, fetch, search
from netgo.wiki import WikiError, entity, page, wikidata_id


def topic_research(topic: str, engine: str = "bing", num: int = 3):
    """Run an automated research workflow for a given topic."""
    print(f"\n=======================================================")
    print(f" Researching topic: {topic.upper()}")
    print(f"=======================================================")

    # ---------------------------------------------------------
    # Step 1: Web Search
    # ---------------------------------------------------------
    print(f"\n[Step 1] Searching {engine.title()} for top {num} results...")
    results = search(topic, engine=engine, num=num)
    for r in results:
        print(f"  #{r.position} {r.title}")
        print(f"      {r.url}")

    # ---------------------------------------------------------
    # Step 2: Fetch and Clean Page Body
    # ---------------------------------------------------------
    best_url = results[0].url if results else None
    if best_url:
        print(f"\n[Step 2] Fetching and parsing top result ({best_url})...")
        try:
            web = fetch(best_url, timeout=15)
            print(f"  Title: {web.title}")
            print(f"  Site : {web.site}")
            if web.paragraphs:
                print(f"  Lead paragraph: {web.paragraphs[0][:200]}...")
        except PageError as exc:
            print(f"  Warning: Could not fetch page ({exc})")

    # ---------------------------------------------------------
    # Step 3: Wikipedia & Wikidata Knowledge Enrichment
    # ---------------------------------------------------------
    print(f"\n[Step 3] Cross-referencing Wikipedia & Wikidata...")
    try:
        art = page(topic)
        print(f"  Wikipedia Title   : {art.title}")
        print(f"  Article Summary   : {art.summary[:160]}...")

        # Resolve Wikidata entity
        qid = wikidata_id(art.title)
        item = entity(qid, language="en")
        print(f"  Wikidata Entity ID: {item.qid}")
        print(f"  Entity Label (EN) : {item.labels.get('en')}")
        print(f"  Description       : {item.descriptions.get('en')}")
    except WikiError as exc:
        print(f"  Warning: Wikipedia/Wikidata lookup error ({exc})")


def main():
    # Execute the research pipeline across two topics
    for topic in ["okapi", "fermentation"]:
        topic_research(topic)


if __name__ == "__main__":
    main()
```

---

## `09_sitemap.py`

**Description:** Discover and read a site's XML sitemaps.

``netgo.sitemap`` finds the sitemaps a site declares in ``robots.txt``
(``discover``), parses a single sitemap URL (``load``/``parse``), crawls
a whole sitemap index tree down to every page URL (``crawl``) and filters
the crawled URLs by a prefix (``filter_by_prefix``).

**GitHub Source:** [09_sitemap.py](https://github.com/FrancoFantomius/netgo/blob/master/examples/09_sitemap.py)

```python
"""Discover and read a site's XML sitemaps.

``netgo.sitemap`` finds the sitemaps a site declares in ``robots.txt``
(``discover``), parses a single sitemap URL (``load``/``parse``), crawls
a whole sitemap index tree down to every page URL (``crawl``) and filters
the crawled URLs by a prefix (``filter_by_prefix``).
"""

# Import sitemap tools and error classes
from netgo import SitemapError, sitemap

SITE = "https://www.example.com"


def main():
    # -------------------------------------------------------------
    # 1. Discover sitemaps declared in robots.txt
    # -------------------------------------------------------------
    # `sitemap.discover(site_url)`: parses robots.txt to find sitemap URLs
    print(f"Discovering sitemaps declared in robots.txt for: {SITE}")
    found = sitemap.discover(SITE)
    print(f"Found {len(found)} sitemap(s):")
    for url in found:
        print(f"  - {url}")

    if not found:
        print("No sitemaps advertised in robots.txt; ending demo.")
        return

    root_sitemap = found[0]

    # -------------------------------------------------------------
    # 2. Load and parse a specific sitemap
    # -------------------------------------------------------------
    # `sitemap.load(url)`: fetches and parses sitemaps, automatically
    # uncompressing .gz sitemaps and determining kind ("urlset" | "sitemapindex" | "text")
    try:
        sm = sitemap.load(root_sitemap)
    except SitemapError as exc:
        print(f"Could not load sitemap at {root_sitemap}: {exc}")
        return

    print(f"\nLoaded Sitemap: {sm.url}")
    print(f"  Type: {sm.kind} | Total entries: {len(sm)}")

    # If the sitemap is an index pointing to child sitemaps:
    if sm.kind == "sitemapindex":
        print("\nChild Sitemaps:")
        for child in sm.children:
            print(f"  - {child}")

    # -------------------------------------------------------------
    # 3. Crawl entire sitemap tree down to page URLs
    # -------------------------------------------------------------
    # `sitemap.crawl(url)`: recursively traverses sitemap indexes
    print("\nCrawling page URLs (first 5 shown):")
    for entry in sitemap.crawl(root_sitemap)[:5]:
        print(f"  - Loc: {entry.loc} (Last modified: {entry.lastmod})")

    # -------------------------------------------------------------
    # 4. Filter crawled URLs by prefix
    # -------------------------------------------------------------
    # `sitemap.filter_by_prefix(url, prefix)`: returns only URLs starting with prefix
    prefix = f"{SITE}/"
    print(f"\nFiltering URLs with prefix '{prefix}' (first 5 shown):")
    for entry in sitemap.filter_by_prefix(root_sitemap, prefix)[:5]:
        print(f"  - {entry.loc}")


if __name__ == "__main__":
    main()
```

---
