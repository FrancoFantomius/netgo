---
layout: home

hero:
  name: "netgo"
  text: "Python Search Toolkit & Wikimedia APIs"
  tagline: Lightweight Python library for scraping search engines, extracting clean page content, parsing sitemaps, and querying Wikimedia APIs.
  actions:
    - theme: brand
      text: Explore API Reference
      link: /netgo
    - theme: alt
      text: Code Examples
      link: /examples
    - theme: alt
      text: GitHub Repository
      link: https://github.com/FrancoFantomius/netgo

features:
  - title: Unified Search Engines
    details: Engine-agnostic API querying Google and Bing, returning consistent Result objects with pagination and safe search.
    link: /netgo.search
  - title: Clean Page Extraction
    details: Download any web page and extract the core article text, filtering out navigation, ads, headers, and footers.
    link: /netgo.page
  - title: XML & Text Sitemaps
    details: Discover sitemaps via robots.txt, parse XML sitemap indexes, and crawl or filter URLs efficiently.
    link: /netgo.sitemap
  - title: Wikipedia & Commons
    details: Full-text search, section outlines, summaries, backlinks, categories, and Commons media file inspection.
    link: /netgo.wiki
  - title: Wikidata & SPARQL
    details: Resolve titles to QIDs, inspect claims, labels, descriptions, aliases, and run live SPARQL queries.
    link: /netgo.wiki.wikidata
  - title: Wiktionary
    details: Look up parts of speech, numbered definitions, etymologies, and cross-language terms across editions.
    link: /netgo.wiki.wiktionary
---

## Architecture Overview

- **`netgo`**: Top-level package exports and convenient high-level functions (`search`, `search_many`, `fetch`).
- **`netgo.search`**: Google and Bing backends, consistent `Result` models, pagination, error handling.
- **`netgo.page`**: Article body extraction engine, HTML boilerplate filtering, and `Page` data model.
- **`netgo.sitemap`**: Robots.txt discovery, XML/text sitemap parsing, index crawling, and prefix filtering.
- **`netgo.wiki`**: MediaWiki Action API client, Wikipedia, Wikidata, Commons, and Wiktionary interfaces.

## Submodule API Reference

| Module | Documentation Link | Documented Classes | Documented Functions |
| :--- | :--- | :--- | :--- |
| `netgo` | [netgo](netgo.md) | 0 | 0 |
| `netgo.page` | [netgo.page](netgo.page.md) | 0 | 0 |
| `netgo.page.errors` | [netgo.page.errors](netgo.page.errors.md) | 3 | 0 |
| `netgo.page.extract` | [netgo.page.extract](netgo.page.extract.md) | 0 | 10 |
| `netgo.page.fetch` | [netgo.page.fetch](netgo.page.fetch.md) | 0 | 1 |
| `netgo.page.models` | [netgo.page.models](netgo.page.models.md) | 1 | 0 |
| `netgo.search` | [netgo.search](netgo.search.md) | 0 | 2 |
| `netgo.search.bing` | [netgo.search.bing](netgo.search.bing.md) | 0 | 5 |
| `netgo.search.errors` | [netgo.search.errors](netgo.search.errors.md) | 2 | 0 |
| `netgo.search.google` | [netgo.search.google](netgo.search.google.md) | 0 | 5 |
| `netgo.search.models` | [netgo.search.models](netgo.search.models.md) | 2 | 0 |
| `netgo.sitemap` | [netgo.sitemap](netgo.sitemap.md) | 0 | 0 |
| `netgo.sitemap.errors` | [netgo.sitemap.errors](netgo.sitemap.errors.md) | 3 | 0 |
| `netgo.sitemap.fetch` | [netgo.sitemap.fetch](netgo.sitemap.fetch.md) | 0 | 6 |
| `netgo.sitemap.models` | [netgo.sitemap.models](netgo.sitemap.models.md) | 2 | 0 |
| `netgo.sitemap.parse` | [netgo.sitemap.parse](netgo.sitemap.parse.md) | 0 | 4 |
| `netgo.wiki` | [netgo.wiki](netgo.wiki.md) | 0 | 0 |
| `netgo.wiki.client` | [netgo.wiki.client](netgo.wiki.client.md) | 1 | 3 |
| `netgo.wiki.core` | [netgo.wiki.core](netgo.wiki.core.md) | 0 | 15 |
| `netgo.wiki.errors` | [netgo.wiki.errors](netgo.wiki.errors.md) | 3 | 0 |
| `netgo.wiki.models` | [netgo.wiki.models](netgo.wiki.models.md) | 11 | 0 |
| `netgo.wiki.wikidata` | [netgo.wiki.wikidata](netgo.wiki.wikidata.md) | 0 | 13 |
| `netgo.wiki.wikimedia` | [netgo.wiki.wikimedia](netgo.wiki.wikimedia.md) | 0 | 5 |
| `netgo.wiki.wiktionary` | [netgo.wiki.wiktionary](netgo.wiki.wiktionary.md) | 0 | 7 |

## Runnable Examples

End-to-end runnable scripts are located in the [GitHub Examples Directory](https://github.com/FrancoFantomius/netgo/tree/master/examples) and documented on the [Code Examples Page](/examples).

| Example File | Purpose / Feature | GitHub Source |
| :--- | :--- | :--- |
| [`01_search.py`](/examples#01-searchpy) | Search Google and Bing through the same engine-agnostic API. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/01_search.py) |
| [`02_parallel_search.py`](/examples#02-parallel-searchpy) | Run many search queries at once with ``netgo.search_many``. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/02_parallel_search.py) |
| [`03_read_page.py`](/examples#03-read-pagepy) | Fetch any web page and read just its main content. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/03_read_page.py) |
| [`04_wikipedia.py`](/examples#04-wikipediapy) | Deep-dive into a Wikipedia article with ``netgo.wiki``. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/04_wikipedia.py) |
| [`05_wikidata.py`](/examples#05-wikidatapy) | From a Wikipedia title to structured Wikidata facts. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/05_wikidata.py) |
| [`06_commons.py`](/examples#06-commonspy) | Find Wikimedia Commons files and inspect their metadata. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/06_commons.py) |
| [`07_wiktionary.py`](/examples#07-wiktionarypy) | Dictionary data from Wiktionary. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/07_wiktionary.py) |
| [`08_research_pipeline.py`](/examples#08-research-pipelinepy) | The full journey in one script: search -> fetch -> enrich with Wikipedia. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/08_research_pipeline.py) |
| [`09_sitemap.py`](/examples#09-sitemappy) | Discover and read a site's XML sitemaps. | [View Source](https://github.com/FrancoFantomius/netgo/blob/master/examples/09_sitemap.py) |
