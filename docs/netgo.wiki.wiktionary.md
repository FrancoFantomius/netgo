# Wiktionary API: dictionary definitions and etymology.

Wiktionary stores one page per \*word\* containing sections for every language it exists in (``== English ==``, ``== Latin ==``, ...). This module reads those pages through the ``action=parse`` endpoint and extracts the part-of-speech headers, the numbered definitions and the etymology paragraphs for a requested language.

Because Wiktionary content is free-form wikitext, the extraction here is deliberately tolerant: definitions are the lines prefixed by ``#`` under a ``===Noun===``/``===Verb===``/... heading, cleaned of wiki markup.

**Example:**
```python
>>> from netgo.wiki import wiktionary_definition
>>> e = wiktionary_definition("serendipity")
>>> e.word
'serendipity'
>>> any("fortunate" in d.lower() for d in e.definitions)
True
```

### `_clean(line: str) -> str`
Strip wiki markup from a single line of wikitext.

### `_section_name(word: str, lang: str) -> str`
Return the Wiktionary header name for a language code.

### `_parse_page(wikitext: str, heading: str) -> tuple[str | None, list[str], list[str]]`
Split a Wiktionary wikitext page by a ``== heading ==`` language block.

Returns ``(pos, definitions, etymology)`` for the given language section: the first part-of-speech header, the ``#``-definition lines and the text under the etymology heading.

### `definition(word: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> netgo.wiki.models.Entry`
Return the definition(s) of a word in a Wiktionary language.

**Args:**
- `word`: The word to look up (exact page title on Wiktionary).
- `lang`: Language code of the dictionary (``"en"``, ``"it"``, ...).
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- An `Entry` with the part of speech and the definitions.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the word page does not exist or the requested language section is missing from it.

**Example:**
```python
>>> from netgo.wiki import wiktionary_definition
>>> e = wiktionary_definition("cat")
>>> e.pos.lower()
'noun'
>>> bool(e.definitions)
True
```

### `etymology(word: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> str`
Return the etymology text of a word.

**Args:**
- `word`: The word to look up.
- `lang`: Language code of the dictionary.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- The etymology paragraph(s) joined by newlines, or ``""`` when the entry has no etymology section.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the word page is missing.

**Example:**
```python
>>> from netgo.wiki import etymology
>>> text = etymology("serendipity")
>>> "Walpole" in text
True
```

### `languages(word: str, lang: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[str]`
Return the languages in which a word has an entry.

Reads the page's top-level (level-2) headings, which on Wiktionary are the language names.

**Args:**
- `word`: The word to look up.
- `lang`: The wiki edition to query (defines the default target but the page lists all languages regardless).
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of language names, e.g. ``["English", "Italian"]``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the word page is missing.

**Example:**
```python
>>> from netgo.wiki import languages
>>> "English" in languages("serendipity")
True
```

### `search(word: str, lang: str = 'en', limit: int = 10, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[str]`
Find Wiktionary entries whose titles begin with ``word``.

Uses the prefix search, ideal for auto-complete and dictionary-style "words starting with ..." queries.

**Args:**
- `word`: The prefix to match.
- `lang`: Language code of the dictionary.
- `limit`: Maximum number of matches.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of matching entry titles.  

**Example:**
```python
>>> from netgo.wiki import wiktionary_search
>>> "serendipity" in wiktionary_search("seren", limit=5)
True
```