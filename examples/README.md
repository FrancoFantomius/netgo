# netgo examples

Runnable, end-to-end examples that exercise the library against the live
network (search engines, web pages and the Wikimedia APIs).

Each script is self-contained: run it with plain Python and read the output.

```bash
python examples/01_search.py
python examples/04_wikipedia.py
```

| File                        | What it shows                                            |
| --------------------------- | -------------------------------------------------------- |
| `01_search.py`              | Google and Bing via the same `netgo.search` API.         |
| `02_parallel_search.py`     | Batching queries with `netgo.search_many`.               |
| `03_read_page.py`           | Fetching a URL and reading its main content.             |
| `04_wikipedia.py`           | Article deep-dive: search, summary, sections, links, ... |
| `05_wikidata.py`            | From article title to QID to structured entity facts.    |
| `06_commons.py`             | Finding media files and reading their metadata.          |
| `07_wiktionary.py`          | Look up definitions, etymology and languages.            |
| `08_research_pipeline.py`   | The full journey: search -> fetch -> summarize.          |
| `09_sitemap.py`             | Discover sitemaps via robots.txt and read page URLs.     |

Notes:

- These examples make real HTTP requests. Search engines may rate-limit
  datacenter IPs; `netgo` raises `SearchBlockedError` in that case, and
  the Wikimedia examples reuse a polite default client.
- The Wikimedia APIs are free but public: keep the batch sizes small and
  don't hammer them.