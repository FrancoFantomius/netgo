"""Filter an HTML page down to its main content, skipping the template.

The extractor follows the classic "readability" recipe:

1. Drop the template chrome outright: ``<nav>``, ``<header>``,
   ``<footer>``, ``<aside>``, forms, scripts, banners and any element
   whose ``class``/``id`` marks it as navigation, ads, comments, social
   widgets, cookie consent, etc.
2. Score every remaining container by the amount of prose it holds
   (paragraph length, punctuation and structural hints like
   ``<article>``/``<main>``).
3. Keep the highest-scoring container, trim it to the span of its first
   and last block, and render its headings and paragraphs as one plain
   block per line.

Pages that are mostly template produce no prose; :func:`render` then
returns an empty list and the callers decide whether that is an error.

Examples:
    >>> from bs4 import BeautifulSoup
    >>> from netgo.page.extract import extract_content, render, extract_title
    >>> html = (
    ...     "<html><head><title>Apple pie - Recipes</title></head><body>"
    ...     "<header>Site</header><nav>Home Recipes</nav>"
    ...     "<article><h1>Apple pie</h1><p>An apple pie is a pie whose filling is apples.</p>"
    ...     "<p>It is served warm with ice cream.</p></article>"
    ...     "<footer>Copyright</footer></body></html>"
    ... )
    >>> soup = BeautifulSoup(html, "html.parser")
    >>> extract_title(soup)
    'Apple pie'
    >>> text, _ = render(extract_content(soup))
    >>> "An apple pie is a pie whose filling is apples." in text
    True
    >>> "ge" in text
    False
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

# Block-level tags that are template chrome by definition and are always
# dropped from the main content.
_REMOVABLE_TAGS = frozenset(
    {
        "nav",
        "header",
        "footer",
        "aside",
        "form",
        "iframe",
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "button",
        "select",
        "input",
        "textarea",
    }
)

# ``class``/``id`` tokens that mark template chrome. Any element whose
# hints contain one of these is removed wholesale (even when it holds
# prose, e.g. "comments").
_NEGATIVE_WORDS = frozenset(
    {
        "ad",
        "ads",
        "advert",
        "adverts",
        "advertisement",
        "banner",
        "breadcrumb",
        "comment",
        "comments",
        "consent",
        "cookie",
        "cookies",
        "copyright",
        "footer",
        "header",
        "legal",
        "login",
        "masthead",
        "menu",
        "modal",
        "nav",
        "newsletter",
        "pagefooter",
        "pagination",
        "popup",
        "promo",
        "related",
        "remarks",
        "reply",
        "share",
        "sharing",
        "sidebar",
        "signup",
        "social",
        "sponsor",
        "subscribe",
        "toolbar",
        "topnav",
        "widget",
    }
)

# ``class``/``id`` tokens that hint at the main content.
_POSITIVE_WORDS = frozenset(
    {
        "article",
        "blog",
        "body",
        "content",
        "entry",
        "main",
        "page",
        "post",
        "story",
        "text",
    }
)

_INVISIBLE = re.compile(r"display\s*:\s*none", re.I)

# Tags whose text is treated as prose blocks when rendering.
_PROSE_TAGS = ("p", "li", "pre", "blockquote")
_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def extract_title(soup: BeautifulSoup) -> str:
    """Return the page title, preferring semantic metadata.

    Checks, in order: an ``og:title`` meta tag, the ``<title>`` tag (its
    site-name suffix such as ``Title - Site`` or ``Title | Site`` is
    stripped), and the first ``<h1>``. Falls back to an empty string.
    """
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        return og["content"].strip()

    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.get_text(" ", strip=True)
        if raw:
            parts = re.split(r"\s+[|·]\s+|\s+[-–—]\s+", raw)
            if len(parts) > 1 and parts[0]:
                return parts[0].strip()
            return raw

    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text:
            return text
    return ""


def extract_site(url: str) -> str:
    """Return the bare domain of ``url`` (``www.`` prefix removed)."""
    netloc = urlparse(url).netloc
    if not netloc:
        return ""
    return netloc.removeprefix("www.")


def extract_content(soup: BeautifulSoup) -> Tag | None:
    """Return the main-content subtree of ``soup``, or ``None``.

    The returned :class:`~bs4.Tag` is what loads below everything else
    that the template adds around the article. ``None`` means the page
    offered no container worth keeping.
    """
    _drop_template(soup)
    container = _best_container(soup)
    if container is None:
        container = soup.body or soup.find("html") or soup
    return _clamp(container)


def render(container: Tag | None) -> tuple[str, list[str]]:
    """Render a content subtree into plain text blocks.

    Returns ``(text, paragraphs)`` where ``text`` joins the blocks with
    blank lines. ``paragraphs`` is empty when the container has no
    extractable prose.
    """
    if container is None:
        return "", []
    paragraphs: list[str] = []
    for el in container.find_all(_PROSE_TAGS + _HEADING_TAGS):
        text = el.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs), paragraphs


def _hints(node: Tag) -> str:
    """Fold an element's ``class``/``id`` into a searchable string."""
    attrs = node.attrs or {}
    classes = attrs.get("class") or []
    if isinstance(classes, str):
        classes = [classes]
    node_id = attrs.get("id") or ""
    return f"{' '.join(classes)} {node_id}".strip()


def _tokens_match(hints: str, words: frozenset[str]) -> bool:
    """Return True when ``hints`` contains any ``words`` token.

    Tokens are matched on non-word boundaries, so ``post-content`` and
    ``post_content`` both match ``post`` (and ``content``).
    """
    for word in words:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", hints):
            return True
    return False


def _has_negative_hint(node: Tag) -> bool:
    hints = _hints(node)
    return bool(hints) and _tokens_match(hints, _NEGATIVE_WORDS)


def _has_positive_hint(node: Tag) -> bool:
    hints = _hints(node)
    return bool(hints) and _tokens_match(hints, _POSITIVE_WORDS)


def _is_invisible(node: Tag) -> bool:
    style = node.get("style") or ""
    if style and _INVISIBLE.search(style):
        return True
    if node.get("hidden") is not None:
        return True
    aria = node.get("aria-hidden")
    if aria and aria.strip().lower() == "true":
        return True
    return False


def _drop_template(soup: BeautifulSoup) -> None:
    """Strip template chrome from ``soup`` in place."""
    to_remove = []
    for node in soup.find_all(True):
        if node.name in _REMOVABLE_TAGS or _has_negative_hint(node) or _is_invisible(node):
            to_remove.append(node)
    for node in to_remove:
        node.decompose()


def _prose_ancestors(leaf: Tag) -> list[Tag]:
    """Credit a prose leaf to its nearest two-three ancestor containers.

    Stops before ``<html>``/``<body>`` so the whole document does not
    always accumulate the highest score.
    """
    chain: list[Tag] = []
    for parent in leaf.parents:
        if parent.name in ("html", "body"):
            break
        chain.append(parent)
        if len(chain) >= 3:
            break
    return chain


def _best_container(soup: BeautifulSoup) -> Tag | None:
    """Return the container holding the most prose, or ``None``."""
    scores: dict[Tag, int] = {}

    for leaf in soup.find_all(_PROSE_TAGS):
        text = leaf.get_text(" ", strip=True)
        if len(text) < 40:
            continue
        weight = (
            min(len(text), 400)
            + 5 * min(text.count(","), 10)
            + 5 * min(text.count(";"), 5)
        )
        for container in _prose_ancestors(leaf):
            scores[container] = scores.get(container, 0) + weight

    for container, score in list(scores.items()):
        hint = 0
        if container.name == "article":
            hint += 40
        elif container.name == "main":
            hint += 30
        if _has_positive_hint(container):
            hint += 25
        total = score + hint
        if total <= 0:
            del scores[container]
        elif hint:
            scores[container] = total

    if not scores:
        return None
    return max(scores, key=scores.get)


def _clamp(container: Tag) -> Tag:
    """Trim ``container`` to the span of its first and last prose block.

    Empty containers are returned unchanged; otherwise the tightest
    ancestor that holds both the first and the last block is returned,
    so stray chrome before/after the article body is not included.
    """
    leaves = container.find_all(_PROSE_TAGS + _HEADING_TAGS)
    leaves = [n for n in leaves if n.get_text(" ", strip=True)]
    if len(leaves) < 2:
        return container
    first, last = leaves[0], leaves[-1]
    tight = container
    for parent in first.parents:
        if parent.name in ("html", "body"):
            break
        if last in parent.descendants:
            tight = parent
            break
    return tight