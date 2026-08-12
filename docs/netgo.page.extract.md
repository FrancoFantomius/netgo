# Filter an HTML page down to its main content, skipping the template.

The extractor follows the classic "readability" recipe:

1. Drop the template chrome outright: ``<nav>``, ``<header>``, ``<footer>``, ``<aside>``, forms, scripts, banners and any element whose ``class``/``id`` marks it as navigation, ads, comments, social widgets, cookie consent, etc. 2. Score every remaining container by the amount of prose it holds (paragraph length, punctuation and structural hints like ``<article>``/``<main>``). 3. Keep the highest-scoring container, trim it to the span of its first and last block, and render its headings and paragraphs as one plain block per line.

Pages that are mostly template produce no prose; `render` then returns an empty list and the callers decide whether that is an error.

**Example:**
```python
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
```

### `extract_title(soup: bs4.BeautifulSoup) -> str`
Return the page title, preferring semantic metadata.

Checks, in order: an ``og:title`` meta tag, the ``<title>`` tag (its site-name suffix such as ``Title - Site`` or ``Title | Site`` is stripped), and the first ``<h1>``. Falls back to an empty string.

### `extract_site(url: str) -> str`
Return the bare domain of ``url`` (``www.`` prefix removed).

### `extract_content(soup: bs4.BeautifulSoup) -> bs4.element.Tag | None`
Return the main-content subtree of ``soup``, or ``None``.

The returned `~bs4.Tag` is what loads below everything else that the template adds around the article. ``None`` means the page offered no container worth keeping.

### `render(container: bs4.element.Tag | None) -> tuple[str, list[str]]`
Render a content subtree into plain text blocks.

Returns ``(text, paragraphs)`` where ``text`` joins the blocks with blank lines. ``paragraphs`` is empty when the container has no extractable prose.

### `_hints(node: bs4.element.Tag) -> str`
Fold an element's ``class``/``id`` into a searchable string.

### `_tokens_match(hints: str, words: frozenset[str]) -> bool`
Return True when ``hints`` contains any ``words`` token.

Tokens are matched on non-word boundaries, so ``post-content`` and ``post_content`` both match ``post`` (and ``content``).

### `_drop_template(soup: bs4.BeautifulSoup) -> None`
Strip template chrome from ``soup`` in place.

### `_prose_ancestors(leaf: bs4.element.Tag) -> list[bs4.element.Tag]`
Credit a prose leaf to its nearest two-three ancestor containers.

Stops before ``<html>``/``<body>`` so the whole document does not always accumulate the highest score.

### `_best_container(soup: bs4.BeautifulSoup) -> bs4.element.Tag | None`
Return the container holding the most prose, or ``None``.

### `_clamp(container: bs4.element.Tag) -> bs4.element.Tag`
Trim ``container`` to the span of its first and last prose block.

Empty containers are returned unchanged; otherwise the tightest ancestor that holds both the first and the last block is returned, so stray chrome before/after the article body is not included.