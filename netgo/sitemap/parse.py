"""Parse sitemap content into structured :class:`~netgo.sitemap.models.Sitemap`.

Handles all three sitemap formats defined by sitemaps.org:

1. **URL sets** (``<urlset>``) - every ``<url>`` becomes a
   :class:`~netgo.sitemap.models.SitemapEntry` with its ``loc``,
   ``lastmod``, ``changefreq`` and ``priority``.
2. **Sitemap indexes** (``<sitemapindex>``) - every nested ``<loc>`` is
   collected as a child sitemap URL.
3. **Plain-text sitemaps** - one URL per line.

Parsing is namespace-agnostic (the sitemap schema tags are recognized no
matter the ``xmlns``), and relative or protocol-relative ``<loc>``
values are resolved against ``base_url`` using :func:`urllib.parse.urljoin`.

Content that cannot be read - empty payloads, malformed XML,
unrecognized root elements, text without URLs - raises
:class:`~netgo.sitemap.errors.SitemapParseError`.

Example:
    >>> from netgo.sitemap import parse, SitemapEntry
    >>> xl = (
    ...     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ...     "<url><loc>/</loc><lastmod>2026-01-01</lastmod>"
    ...     "<changefreq>daily</changefreq><priority>1.0</priority></url>"
    ...     "</urlset>"
    ... )
    >>> sm = parse(xl, base_url="https://example.com/sitemap.xml")
    >>> sm.kind
    'urlset'
    >>> sm.urls
    ['https://example.com/']
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .errors import SitemapParseError
from .models import Sitemap, SitemapEntry, _SITEMAPINDEX, _TEXT, _URLSET


def parse(content: str | bytes, *, base_url: str = "") -> Sitemap:
    """Parse sitemap content (XML or plain text) into a :class:`Sitemap`.

    Auto-detects the format from the payload: content beginning with an
    XML element (``<urlset>``, ``<sitemapindex>`` or any other root, with
    or without a namespace) is parsed as XML, anything else is treated as
    a plain-text URL list. Relative ``<loc>`` values are resolved against
    ``base_url`` with :func:`urllib.parse.urljoin`, so absolute URLs pass
    through unchanged.

    Args:
        content: The raw sitemap body, as ``str`` or ``bytes``.
        base_url: The sitemap's own URL; used to resolve relative and
            protocol-relative locations. Ignored when empty.

    Returns:
        A :class:`Sitemap` with ``kind`` set to ``"urlset"``,
        ``"sitemapindex"`` or ``"text"``.

    Raises:
        SitemapParseError: When the content is empty, not well formed,
            uses an unknown root element, or holds no URL at all.

    Example:
        >>> from netgo.sitemap import parse
        >>> sm = parse(
        ...     '<sitemapindex><sitemap><loc>/posts/sitemap.xml</loc></sitemap></sitemapindex>',
        ...     base_url="https://example.com/sitemap.xml",
        ... )
        >>> sm.kind
        'sitemapindex'
        >>> sm.children
        ['https://example.com/posts/sitemap.xml']
    """
    if isinstance(content, bytes):
        stripped = content.lstrip()
        if stripped.startswith(b"<"):
            return _parse_xml(content, base_url)
        return _parse_text(content.decode("utf-8", errors="replace"), base_url)

    text = content.lstrip()
    if not text:
        raise SitemapParseError("sitemap content is empty")
    if text.startswith(("<", "<?xml")):
        return _parse_xml(text, base_url)
    return _parse_text(text, base_url)


def _to_bytes(content: str | bytes) -> bytes:
    """Return ``content`` as bytes without a conflicting XML declaration."""
    if isinstance(content, bytes):
        return content
    text = content.lstrip()
    if text.startswith("<?xml"):
        end = text.find("?>")
        if end != -1:
            text = text[end + 2 :]
    return text.encode("utf-8")


def _local_name(tag: str) -> str:
    """Strip a ``{namespace}`` prefix from an ElementTree tag name."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _child_text(element: ET.Element, name: str) -> str | None:
    """Return the direct ``<loc>``/``<lastmod>``-style text of a child."""
    wanted = name.lower()
    for child in element:
        if _local_name(child.tag).lower() == wanted:
            return (child.text or "").strip()
    return None


def _parse_xml(content: str | bytes, base_url: str) -> Sitemap:
    try:
        root = ET.fromstring(_to_bytes(content))
    except ET.ParseError as exc:
        raise SitemapParseError(f"not well-formed sitemap XML: {exc}") from exc

    kind = _local_name(root.tag)
    if kind == "urlset":
        return _parse_urlset(root, base_url)
    if kind == "sitemapindex":
        children = []
        for node in root:
            if _local_name(node.tag) != "sitemap":
                continue
            loc = _child_text(node, "loc")
            if loc:
                children.append(_resolve(base_url, loc))
        return Sitemap(kind=_SITEMAPINDEX, children=children, url=base_url)
    raise SitemapParseError(f"unrecognized sitemap root element: {kind!r}")


def _parse_urlset(root: ET.Element, base_url: str) -> Sitemap:
    entries = []
    for node in root:
        if _local_name(node.tag) != "url":
            continue
        loc = _child_text(node, "loc")
        if not loc:
            continue
        priority_raw = _child_text(node, "priority")
        priority = 0.0
        if priority_raw:
            try:
                priority = float(priority_raw)
            except ValueError:
                priority = 0.0
        entries.append(
            SitemapEntry(
                loc=_resolve(base_url, loc),
                lastmod=_child_text(node, "lastmod") or "",
                changefreq=_child_text(node, "changefreq") or "",
                priority=priority,
            )
        )
    return Sitemap(kind=_URLSET, entries=entries, url=base_url)


def _parse_text(text: str, base_url: str) -> Sitemap:
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(SitemapEntry(loc=_resolve(base_url, line)))
    if not entries:
        raise SitemapParseError("no URLs found in sitemap content")
    return Sitemap(kind=_TEXT, entries=entries, url=base_url)


def _resolve(base_url: str, loc: str) -> str:
    from urllib.parse import urljoin

    return urljoin(base_url, loc)


__all__ = ["parse"]