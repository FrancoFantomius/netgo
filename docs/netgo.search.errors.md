### class `SearchError`
Generic error raised by a search backend.

Every backend wraps its failures (transport errors, parsing problems, rate limiting) in ``SearchError`` subclasses, so caller code can catch this one class and handle all of them uniformly.

**Example:**
```python
>>> from netgo import SearchError
>>> try:
...     raise SearchError("backend failure")
... except SearchError as exc:
...     print("search failed:", exc)
search failed: backend failure
```

### class `SearchBlockedError`
Raised when a search engine serves a captcha, interstitial or consent page instead of results.

Both backends raise it: Google when it shows an interstitial/consent page, Bing when it shows a robot check. This usually means the requesting IP is rate-limited or flagged as a datacenter. It is raised instead of silently returning an empty list, so automation can detect the problem and react.

**Workarounds:**
- retry later with a small ``delay`` between requests  
- for Google, pass ``gbv=True`` to use its basic HTML interface  
- rotate the source IP or use a proxy  

**Example:**
```python
>>> from netgo import search, SearchBlockedError
>>> try:
...     search("cats", delay=2.0)
... except SearchBlockedError as exc:
...     print("blocked:", exc)
blocked: Google returned an interstitial/consent page instead of results ...
```