### class `Result`
```python
Result(url: 'str', title: 'str' = '', snippet: 'str' = '', position: 'int' = 0, meta: 'dict' = <factory>) -> None
```
A single search result returned by a search backend.

Results are ordered by the engine's ranking; ``position`` is 1-based. Instances are plain dataclasses, so they support equality, hashing and repr, and can be unpacked like tuples.

**Example:**
```python
>>> from netgo import search
>>> results = search("web scraping", num=3)
>>> first = results[0]
>>> first.position
1
>>> str(first)  # defaults to the URL
'https://...'
```
**Fields:**
- `url`
- `title`
- `snippet`
- `position` = 0
- `meta`

### class `SearchParams`
```python
SearchParams(query: 'str', num: 'int' = 10, lang: 'str' = 'en', start: 'int' = 0, safe: 'bool' = False, gbv: 'bool' = False) -> None
```
Parameters sent to a search engine when running a query.

Used internally by backends to build the request URL. The defaults match a plain Google search: 10 organic results, English, first page, safe search off.

**Example:**
```python
>>> from netgo.search import SearchParams
>>> p = SearchParams(query="hello world", num=5, safe=True)
>>> p.gbv
False
```
**Fields:**
- `query`
- `num` = 10
- `lang` = 'en'
- `start` = 0
- `safe` = False
- `gbv` = False