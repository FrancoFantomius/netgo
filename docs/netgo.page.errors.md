# Errors raised by the netgo page fetching and content extraction.

Every failure of `netgo.page.fetch` (transport errors, non-HTML payloads, pages that yield no extractable prose) is wrapped in a ``PageError`` subclass, so caller code can catch the single base class and handle all of them uniformly.

**Example:**
```python
>>> from netgo import PageError
>>> try:
...     raise PageError("page failed")
... except PageError as exc:
...     print("page failed:", exc)
page failed: page failed
```

### class `PageError`
Base class for every error raised by `netgo.page`.

Catching this class covers transport failures, HTTP errors and pages whose main content cannot be extracted.

### class `PageFetchError`
```python
PageFetchError(message: str, *, status: int | None = None) -> None
```
Raised when the page could not be downloaded.

Carries the HTTP status code when the request reached a server but answered with a non-2xx response, so callers can tell "blocked" (403/429) from plain network failures.

### class `PageParseError`
Raised when a page has no extractable main content.

Typical causes: the response is not HTML (a PDF, an image, a raw API payload) or the page is almost entirely template chrome whose remaining prose is too thin to count as content. Nothing is silently returned, so automation can detect the situation and react.