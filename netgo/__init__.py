from .search import (
    Result,
    SearchBlockedError,
    SearchError,
    SearchParams,
    search,
    search_many,
)

__version__ = "0.1.0"

__all__ = [
    "Result",
    "SearchParams",
    "SearchError",
    "SearchBlockedError",
    "search",
    "search_many",
    "__version__",
]