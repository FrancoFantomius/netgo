# netgo

A lightweight Python toolkit for scraping search engines and getting the links back.

netgo exposes a single, engine-agnostic API on top of several search backends,
so you can switch or combine engines without touching your data model. Every
backend returns the same `netgo.Result` objects, ranked by the engine.

**Backends**

- **Google** — the default.
- **Bing** — selected with `engine="bing"`.

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
- Check each engine's terms of service for your use case.