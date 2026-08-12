"""Errors raised by the netgo Wikipedia API wrappers.

Every wrapper in :mod:`netgo.wiki` wraps its failures (transport errors,
MediaWiki API errors, missing pages) in ``WikiError`` subclasses, so
caller code can catch the single base class and handle all of them
uniformly.

Example:
    >>> from netgo.wiki import WikiError, WikiNotFoundError
    >>> try:
    ...     raise WikiNotFoundError("Python (programming language)")
    ... except WikiError as exc:
    ...     print("wiki failed:", exc)
    wiki failed: Python (programming language)
"""


class WikiError(Exception):
    """Base class for every error raised by :mod:`netgo.wiki`.

    Catching this class covers transport failures, MediaWiki ``error``
    responses and missing pages alike.
    """


class WikiAPIError(WikiError):
    """Raised when the MediaWiki API rejects or fails the request.

    Carries the HTTP status code when the request never reached the API
    (SEO failures, timeouts, non-200 responses) and the MediaWiki error
    ``code``/``info`` strings when the API returned an ``error`` object.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        info: str | None = None,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.info = info
        self.status = status


class WikiNotFoundError(WikiError):
    """Raised when a page, entity or file does not exist.

    MediaWiki returns a ``missing`` marker for unknown titles and
    ``wbsearchentities`` returns an empty list for unknown Wikidata
    queries; both cases map to this error so callers can distinguish a
    simply-absent page from a real API failure.
    """

    def __init__(self, subject: str, *, lang: str | None = None) -> None:
        self.subject = subject
        self.lang = lang
        where = f" in '{lang}'" if lang else ""
        super().__init__(f"Not found: '{subject}'{where}")