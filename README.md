# netgo

A Python toolkit for scraping search engines and getting the links back.
Google search is one of its backends (currently the first one).

## Install

```bash
pip install -e .
```

## Usage

```python
import netgo

# Google search, one of netgo's backends
results = netgo.search("python web scraping", num=10)

for r in results:
    print(r.position, r.title)
    print("  ", r.url)
    print("  ", r.snippet[:80])
```

Every result is a `netgo.search.Result` dataclass:

| Field      | Meaning                     |
|------------|-----------------------------|
| `url`      | The real destination URL    |
| `title`    | Page title                  |
| `snippet`  | Short text under the title  |
| `position` | Ranking on the page (1-based)|

## Google options

```python
netgo.search(
    "italy travel",   # query
    num=20,           # how many results to request (max 100)
    lang="it",        # language / host language, e.g. hl=it
    start=10,         # pagination offset
    safe=True,        # enable safe search
    gbv=True,         # use Google's basic HTML interface
    delay=1.0,        # sleep seconds before the request
)
```

### Multiple queries

```python
links = netgo.search_many(["cats", "dogs"], max_workers=4, num=5)
for query, results in links.items():
    print(query, [r.url for r in results])
```

## Notes

- This scrapes the public Google results page. Google may throttle or block
  requests from datacenter IPs; add `delay` between calls, or pass `gbv=True`
  to try the basic HTML interface.
- When blocked, `search` raises `SearchBlockedError` instead of silently
  returning nothing.
- Attribution / webmaster guidelines: use responsibly and check each engine's
  ToS for your use case.