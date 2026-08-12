"""Wikimedia Commons API: searching and inspecting media files.

Commons is the central media repository for every Wikimedia project,
with tens of millions of free images, videos and audio files. This
module wraps ``commons.wikimedia.org/w/api.php`` to find files by text
and pull down their direct URLs, thumbnails and licensing metadata.

Example:
    >>> from netgo.wiki import search_images, image_url
    >>> hits = search_images("sunflower", limit=3)
    >>> bool(hits[0].name.startswith("File:"))
    True
    >>> url = image_url("File:Sunflower 2016.jpg")
    >>> url.endswith(".jpg")
    True
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from .client import WikiClient
from .errors import WikiNotFoundError
from .models import MediaFile


def _media_client(*, timeout: int, delay: float) -> WikiClient:
    return WikiClient(host="wikimedia", timeout=timeout, delay=delay)


def _plain(html: str) -> str:
    """Strip HTML out of Commons ``extmetadata`` text blocks."""
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def search_images(
    query: str,
    limit: int = 10,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> list[MediaFile]:
    """Search Commons for media files by free-text query.

    Searches the ``File:`` namespace (namespace 6); each hit only
    carries the file name — use :func:`file_info` for the URL and
    metadata of the ones you care about.

    Args:
        query: The text to search for (tags, captions, categories...).
        limit: Maximum number of files to return.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of :class:`MediaFile` with the file names populated.

    Example:
        >>> from netgo.wiki import search_images
        >>> hits = search_images("cat", limit=2)
        >>> hits[0].name or "File:..."
        'File:...'
    """
    client = client or _media_client(timeout=timeout, delay=delay)
    payload = client.api_call(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": 6,
            "srlimit": min(limit, 50),
        }
    )
    return [
        MediaFile(name=h.get("title", ""))
        for h in payload["query"].get("search", [])
    ]


def file_info(
    filename: str,
    thumb_width: int = 320,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> MediaFile:
    """Return full metadata for a single Commons file.

    Includes the direct download URL, a resized thumbnail (``thumburl``),
    dimensions, MIME type and licensing/author/description text from the
    file's ``extmetadata``.

    Args:
        filename: The file title, e.g. ``"File:Earth.jpg"``.
        thumb_width: Pixel width of the generated thumbnail.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A populated :class:`MediaFile`.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the file does not exist.

    Example:
        >>> from netgo.wiki import file_info
        >>> f = file_info("File:Earth.jpg")
        >>> f.mime
        'image/jpeg'
    """
    client = client or _media_client(timeout=timeout, delay=delay)
    payload = client.api_call(
        {
            "action": "query",
            "titles": filename,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": thumb_width,
        }
    )
    pages = payload.get("query", {}).get("pages", {})
    if not pages:
        raise WikiNotFoundError(filename)
    page = next(iter(pages.values()))
    if "imageinfo" not in page:
        raise WikiNotFoundError(filename)
    info = page["imageinfo"][0]
    meta = info.get("extmetadata", {})
    return MediaFile(
        name=page.get("title", filename),
        url=info.get("url", ""),
        thumburl=info.get("thumburl", ""),
        size=info.get("size", 0),
        width=info.get("width", 0),
        height=info.get("height", 0),
        mime=info.get("mime", ""),
        description=_plain(meta.get("ImageDescription", {}).get("value")),
        license=meta.get("LicenseShortName", {}).get("value", ""),
        artist=_plain(meta.get("Artist", {}).get("value")),
    )


def image_url(
    filename: str,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> str:
    """Return the direct download URL of a Commons file.

    Convenience wrapper over :func:`file_info`.

    Args:
        filename: The file title, e.g. ``"File:Earth.jpg"``.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        The absolute URL of the original file.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the file does not exist.

    Example:
        >>> from netgo.wiki import image_url
        >>> bool(image_url("File:Earth.jpg"))
        True
    """
    return file_info(
        filename, client=client, timeout=timeout, delay=delay
    ).url


def random_file(
    limit: int = 1,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> list[MediaFile]:
    """Return random files from the Commons repository.

    Useful for wander-style exploration of the media library.

    Args:
        limit: Number of random files to return.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of :class:`MediaFile` with the file names populated.

    Example:
        >>> from netgo.wiki import random_file
        >>> len(random_file(limit=2))
        2
    """
    client = client or _media_client(timeout=timeout, delay=delay)
    payload = client.api_call(
        {"action": "query", "list": "random", "rnnamespace": 6, "rnlimit": min(limit, 50)}
    )
    return [
        MediaFile(name=r.get("title", ""))
        for r in payload["query"].get("random", [])
    ]


__all__ = ["search_images", "file_info", "image_url", "random_file"]