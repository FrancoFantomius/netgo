class SearchError(Exception):
    """Generic error raised by a search backend."""


class SearchBlockedError(SearchError):
    """Raised when Google serves an interstitial/consent page instead of results."""