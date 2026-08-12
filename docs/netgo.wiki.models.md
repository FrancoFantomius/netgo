# Data models returned by the :mod:`netgo.wiki` API wrappers.

Every wrapper maps the MediaWiki JSON responses onto plain dataclasses, so the callers get structured objects instead of raw dicts. The models are deliberately small and focused on the fields the wrappers actually use; extra fields returned by the API are exposed through the ``raw`` slots where relevant.

**Example:**
```python
>>> from netgo.wiki import search
>>> hits = search("python (programming language)", limit=2)
>>> hits[0].title
'Python (programming language)'
>>> hits[0].wordcount
133
```

### class `WikiResult`
```python
WikiResult(title: 'str', pageid: 'int' = 0, snippet: 'str' = '', wordcount: 'int' = 0, size: 'int' = 0, timestamp: 'str' = '', ns: 'int' = 0) -> None
```
A single full-text search hit returned by ``search``.

Mirrors the fields of a ``list=search`` entry: the matched title, its stable page id, a plain-text snippet, and basic stats.

**Example:**
```python
>>> from netgo.wiki import search
>>> r = search("web scraping", limit=1)[0]
>>> r.title
'Web scraping'
>>> r.ns
0
```
**Fields:**
- `title`
- `pageid` = 0
- `snippet`
- `wordcount` = 0
- `size` = 0
- `timestamp`
- `ns` = 0

### class `Section`
```python
Section(index: 'str', title: 'str', level: 'int' = 1) -> None
```
A single heading in a page's table of contents.

``index`` and ``level`` mirror the values reported by the API; ``title`` is the extracted heading text, later rendered by the paragraph helpers.

**Example:**
```python
>>> from netgo.wiki import sections
>>> for s in sections("Python (programming language)")[:2]:
...     print(s.index, s.title)
1 History
2 Features and philosophy
```
**Fields:**
- `index`
- `title`
- `level` = 1

### class `Link`
```python
Link(title: 'str', ns: 'int' = 0, pageid: 'int' = 0) -> None
```
A link found on (or to) a page.

``ns`` is the MediaWiki namespace id (0 for articles), ``title`` the target title. Used by ``links`` and ``backlinks``.
**Fields:**
- `title`
- `ns` = 0
- `pageid` = 0

### class `Category`
```python
Category(title: 'str', ns: 'int' = 14, hidden: 'bool' = False) -> None
```
A category membership of a page.

``hidden`` marks MediaWiki maintenance categories, which are hidden from readers by default in the article's category box.
**Fields:**
- `title`
- `ns` = 14
- `hidden` = False

### class `Image`
```python
Image(title: 'str', url: 'str' = '', descriptionurl: 'str' = '', size: 'int' = 0, width: 'int' = 0, height: 'int' = 0, mime: 'str' = '') -> None
```
A media file embedded in a page (namespace ``File:``).

URL fields are populated by ``images`` only when the metadata is requested; otherwise only ``title`` is set.
**Fields:**
- `title`
- `url`
- `descriptionurl`
- `size` = 0
- `width` = 0
- `height` = 0
- `mime`

### class `Article`
```python
Article(title: 'str', pageid: 'int' = 0, lang: 'str' = 'en', summary: 'str' = '', url: 'str' = '', sections: 'list[Section]' = <factory>, categories: 'list[Category]' = <factory>, links: 'list[Link]' = <factory>, images: 'list[Image]' = <factory>) -> None
```
An aggregated view of a Wikipedia article.

Built by `netgo.wiki.page` from several API calls, so a single object carries the intro summary, the section outline, and the parsed link/category/image tables in one place.

**Example:**
```python
>>> from netgo.wiki import page
>>> art = page("Python (programming language)")
>>> art.title
'Python (programming language)'
>>> art.sections[0].title
'History'
```
**Fields:**
- `title`
- `pageid` = 0
- `lang` = 'en'
- `summary`
- `url`
- `sections`
- `categories`
- `links`
- `images`

### class `Claim`
```python
Claim(pid: 'str', datatype: 'str' = '', value: 'Any' = None, qualifiers: 'dict' = <factory>) -> None
```
A single Wikidata claim (property + value pair).

``pid`` is the property id (e.g. ``"P31"``), ``datatype`` its type, ``value`` the raw JSON value (a string for external identifiers and quantities, a QID for items) and ``qualifiers`` holds any additional qualifier claims nested under the property.

**Example:**
```python
>>> from netgo.wiki import entity
>>> e = entity("Q2")
>>> e.claims["P31"][0].value
'Q5'
```
**Fields:**
- `pid`
- `datatype`
- `value` = None
- `qualifiers`

### class `Item`
```python
Item(qid: 'str', labels: 'dict' = <factory>, descriptions: 'dict' = <factory>, aliases: 'dict' = <factory>, claims: 'dict' = <factory>, sitelinks: 'dict' = <factory>) -> None
```
A Wikidata entity.

``qid`` is the entity id (e.g. ``"Q2"``), ``labels``/``descriptions``/ ``aliases`` map a language code to the translated text, ``claims`` maps a property id to its list of `Claim` and ``sitelinks`` maps a site (e.g. ``"enwiki"``) to the external page title.

**Example:**
```python
>>> from netgo.wiki import entity
>>> e = entity("Q2")
>>> e.labels["en"]
'Earth'
>>> e.claims["P31"][0].value
'Q5'
```
**Fields:**
- `qid`
- `labels`
- `descriptions`
- `aliases`
- `claims`
- `sitelinks`

### class `GeoResult`
```python
GeoResult(title: 'str', pageid: 'int' = 0, ns: 'int' = 0, lat: 'float' = 0.0, lon: 'float' = 0.0, dist: 'float' = 0.0) -> None
```
A geo-search hit returned by `netgo.wiki.geo_search`.

``dist`` is the distance in metres from the queried coordinate as reported by the API.

**Example:**
```python
>>> from netgo.wiki import geo_search
>>> hits = geo_search(41.89, 12.49, radius=2000, limit=3)
>>> hits[0].title
'Rome'
```
**Fields:**
- `title`
- `pageid` = 0
- `ns` = 0
- `lat` = 0.0
- `lon` = 0.0
- `dist` = 0.0

### class `MediaFile`
```python
MediaFile(name: 'str', url: 'str' = '', thumburl: 'str' = '', size: 'int' = 0, width: 'int' = 0, height: 'int' = 0, mime: 'str' = '', description: 'str' = '', license: 'str' = '', artist: 'str' = '') -> None
```
A Wikimedia Commons file.

``name`` is the full file title (``File:...``), ``url`` the direct download URL, ``thumburl`` a resized preview, and the remaining fields carry size, dimensions and licensing metadata which Commons exposes through ``extmetadata``.

**Example:**
```python
>>> from netgo.wiki import file_info
>>> f = file_info("File:Earth.jpg")
>>> f.mime
'image/jpeg'
>>> bool(f.url)
True
```
**Fields:**
- `name`
- `url`
- `thumburl`
- `size` = 0
- `width` = 0
- `height` = 0
- `mime`
- `description`
- `license`
- `artist`

### class `Entry`
```python
Entry(word: 'str', lang: 'str' = 'en', pos: 'str' = '', definitions: 'list[str]' = <factory>, etymology: 'str' = '') -> None
```
A Wiktionary entry: the word and one or more senses.

``word`` is the lookup term, ``lang`` the dictionary language, ``pos`` the part of speech as written in the wikitext header, and ``definitions`` collects the numbered definition lines. ``etymology`` is filled by the etymology helper.

**Example:**
```python
>>> from netgo.wiki import wiktionary_definition
>>> e = wiktionary_definition("serendipity")
>>> e.word
'serendipity'
>>> bool(e.definitions)
True
```
**Fields:**
- `word`
- `lang` = 'en'
- `pos`
- `definitions`
- `etymology`