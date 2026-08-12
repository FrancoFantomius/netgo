"""Wiktionary API: dictionary definitions and etymology.

Wiktionary stores one page per *word* containing sections for every
language it exists in (``== English ==``, ``== Latin ==``, ...). This
module reads those pages through the ``action=parse`` endpoint and
extracts the part-of-speech headers, the numbered definitions and the
etymology paragraphs for a requested language.

Because Wiktionary content is free-form wikitext, the extraction here is
deliberately tolerant: definitions are the lines prefixed by ``#`` under
a ``===Noun===``/``===Verb===``/... heading, cleaned of wiki markup.

Example:
    >>> from netgo.wiki import wiktionary_definition
    >>> e = wiktionary_definition("serendipity")
    >>> e.word
    'serendipity'
    >>> any("fortunate" in d.lower() for d in e.definitions)
    True
"""

from __future__ import annotations

import re

from .client import WikiClient
from .errors import WikiNotFoundError
from .models import Entry

_LANG_NAMES = {
    "en": "English",
    "it": "Italian",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "ru": "Russian",
    "uk": "Ukrainian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "el": "Greek",
    "la": "Latin",
    "eo": "Esperanto",
}

_HEADER_RE = re.compile(r"^(={2,4})\s*(.*?)\s*\1\s*$")
_DEF_RE = re.compile(r"^#[^*]\s*(.+?)\s*$")
_TPL_RE = re.compile(r"\{\{[^{}]*\}\}")
_LINK_RE = re.compile(r"\[\[([^|\]]*)(?:\|([^\]]*))?\]\]")
_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")

_SKIP_POS = (
    "pronunciation",
    "see also",
    "further reading",
    "references",
    "anagrams",
    "derived terms",
    "related terms",
    "usage notes",
    "quotations",
)


def _clean(line: str) -> str:
    """Strip wiki markup from a single line of wikitext."""
    line = _TPL_RE.sub("", line)
    line = _LINK_RE.sub(lambda m: m.group(2) or m.group(1), line)
    line = _TAG_RE.sub("", line)
    line = line.replace("'''", "").replace("''", "")
    return " ".join(line.split()).strip()


def _section_name(word: str, lang: str) -> str:
    """Return the Wiktionary header name for a language code."""
    return _LANG_NAMES.get(lang, lang.title())


def _parse_page(
    wikitext: str, heading: str
) -> tuple[str | None, list[str], list[str]]:
    """Split a Wiktionary wikitext page by a ``== heading ==`` language block.

    Returns ``(pos, definitions, etymology)`` for the given language
    section: the first part-of-speech header, the ``#``-definition lines
    and the text under the etymology heading.
    """
    pos = None
    definitions: list[str] = []
    etymology: list[str] = []
    in_lang = False
    in_etym = False
    level_line: int | str = ""

    for i, raw in enumerate(wikitext.splitlines()):
        m = _HEADER_RE.match(raw.strip())
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 2:
                in_etym = False
                in_lang = text == heading
                continue
            if in_lang and level in (3, 4):
                lowered = text.lower()
                if lowered.startswith("etymology"):
                    in_etym = True
                    continue
                if pos is None and not lowered.startswith(_SKIP_POS):
                    pos = text
                in_etym = False
                continue
            continue

        if not in_lang:
            continue
        if in_etym:
            cleaned = _clean(raw).strip()
            if cleaned:
                etymology.append(cleaned)
            continue
        if pos is None:
            continue
        dm = _DEF_RE.match(raw.strip())
        if dm:
            cleaned = _clean(dm.group(1))
            if cleaned:
                definitions.append(cleaned)
    return pos, definitions, etymology


def _wiktionary_client(*, lang: str, timeout: int, delay: float) -> WikiClient:
    return WikiClient(lang=lang, host="wiktionary", timeout=timeout, delay=delay)


def definition(
    word: str,
    lang: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> Entry:
    """Return the definition(s) of a word in a Wiktionary language.

    Args:
        word: The word to look up (exact page title on Wiktionary).
        lang: Language code of the dictionary (``"en"``, ``"it"``, ...).
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        An :class:`Entry` with the part of speech and the definitions.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the word page does not exist or
            the requested language section is missing from it.

    Example:
        >>> from netgo.wiki import wiktionary_definition
        >>> e = wiktionary_definition("cat")
        >>> e.pos.lower()
        'noun'
        >>> bool(e.definitions)
        True
    """
    heading = _section_name(word, lang)
    client = client or _wiktionary_client(lang=lang, timeout=timeout, delay=delay)
    payload = client.api_call({"action": "parse", "page": word, "prop": "wikitext"})
    parsed = payload.get("parse")
    if not parsed:
        raise WikiNotFoundError(word, lang=lang)
    pos, definitions, _etym = _parse_page(
        parsed.get("wikitext", {}).get("*", ""), heading
    )
    if pos is None and not definitions:
        raise WikiNotFoundError(word, lang=lang)
    return Entry(word=word, lang=lang, pos=pos or "", definitions=definitions)


def etymology(
    word: str,
    lang: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> str:
    """Return the etymology text of a word.

    Args:
        word: The word to look up.
        lang: Language code of the dictionary.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        The etymology paragraph(s) joined by newlines, or ``""`` when the
        entry has no etymology section.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the word page is missing.

    Example:
        >>> from netgo.wiki import etymology
        >>> text = etymology("serendipity")
        >>> "Walpole" in text
        True
    """
    heading = _section_name(word, lang)
    client = client or _wiktionary_client(lang=lang, timeout=timeout, delay=delay)
    payload = client.api_call({"action": "parse", "page": word, "prop": "wikitext"})
    parsed = payload.get("parse")
    if not parsed:
        raise WikiNotFoundError(word, lang=lang)
    _pos, _defs, etym = _parse_page(
        parsed.get("wikitext", {}).get("*", ""), heading
    )
    return " ".join(etym).strip()


def languages(
    word: str,
    lang: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> list[str]:
    """Return the languages in which a word has an entry.

    Reads the page's top-level (level-2) headings, which on Wiktionary
    are the language names.

    Args:
        word: The word to look up.
        lang: The wiki edition to query (defines the default target but
            the page lists all languages regardless).
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of language names, e.g. ``["English", "Italian"]``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the word page is missing.

    Example:
        >>> from netgo.wiki import languages
        >>> "English" in languages("serendipity")
        True
    """
    client = client or _wiktionary_client(lang=lang, timeout=timeout, delay=delay)
    payload = client.api_call({"action": "parse", "page": word, "prop": "sections"})
    parsed = payload.get("parse")
    if not parsed:
        raise WikiNotFoundError(word, lang=lang)
    return [
        s.get("line", "")
        for s in parsed.get("sections", [])
        if int(s.get("level", 1) or 1) == 2
    ]


def search(
    word: str,
    lang: str = "en",
    limit: int = 10,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> list[str]:
    """Find Wiktionary entries whose titles begin with ``word``.

    Uses the prefix search, ideal for auto-complete and dictionary-style
    "words starting with ..." queries.

    Args:
        word: The prefix to match.
        lang: Language code of the dictionary.
        limit: Maximum number of matches.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of matching entry titles.

    Example:
        >>> from netgo.wiki import wiktionary_search
        >>> "serendipity" in wiktionary_search("seren", limit=5)
        True
    """
    client = client or _wiktionary_client(lang=lang, timeout=timeout, delay=delay)
    payload = client.api_call(
        {"action": "query", "list": "prefixsearch", "pssearch": word, "pslimit": min(limit, 100)}
    )
    return [
        p.get("title", "") for p in payload["query"].get("prefixsearch", [])
    ]


__all__ = ["definition", "etymology", "languages", "search"]