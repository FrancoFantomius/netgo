# Wikidata API: structured data about entities.

Wikidata stores facts as \*entities\* (Q-items like ``Q2`` = Earth and P-properties like ``P31`` = instance of) independent of any language. This module talks to ``www.wikidata.org/w/api.php`` and maps the JSON onto the `netgo.wiki.models.Item` and `netgo.wiki.models.Claim` models.

**Notes:**
- ``language`` selects which translation of the labels/descriptions
the API returns; it does not change the entity itself.
- ``wikidata_id`` bridges a Wikipedia title to its QID so you can
jump from an article to its facts in one helper.
- `sparql` runs raw SPARQL against ``query.wikidata.org`` for
questions the Action API cannot answer (e.g. items carrying a
given property).

**Example:**
```python
>>> from netgo.wiki import wikidata_id, entity
>>> q = wikidata_id("Python (programming language)")
>>> e = entity(q, language="en")
>>> e.qid
'Q28865'
>>> e.labels["en"] == "Python"
True
```

### `_query(params: dict[str, object], *, client: netgo.wiki.client.WikiClient | None = None, language: str = 'en', timeout: int = 10, delay: float = 0.0) -> dict`
Run a Wikidata API call through a shared client.

### `_claim_value(mainsnak: dict)`
Map a Wikidata snak to a plain Python value.

Item ids become ``"Q123"`` strings, quantities keep their ``amount``, dates keep the ISO ``time`` string, and plain values pass through.

**Example:**
```python
>>> _claim_value({"snaktype": "value", "datavalue": {"value": "Q5"}})
'Q5'
```

### `_parse_claims(raw_claims: dict) -> dict[str, list[netgo.wiki.models.Claim]]`
Turn a raw Wikidata ``claims`` object into ``pid -> [Claim]``.

### `_first_entity(payload: dict, qid: str, *, language: str) -> dict`
Pull the single entity object out of a ``wbgetentities`` reply.

### `wikidata_id(title: str, lang: str = 'en', site: str = 'wikipedia', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> str`
Resolve a wiki page title to its Wikidata QID.

Looks for the ``wikibase_item`` page property on the given language edition, which every real Wikipedia article carries.

**Args:**
- `title`: The page title on the wiki (e.g. ``"Python"``).
- `lang`: Language code of the wiki edition to query.
- `site`: Site key of the wiki (nearly always ``"wikipedia"``).
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- The QID string, e.g. ``"Q28865"``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the page has no Wikidata link.

**Example:**
```python
>>> from netgo.wiki import wikidata_id
>>> wikidata_id("Python (programming language)")
'Q28865'
```

### `entity(qid: str, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> netgo.wiki.models.Item`
Fetch a full Wikidata entity and structure it.

Brings back labels, descriptions, aliases, claims and sitelinks for the given QID in the requested language.

**Args:**
- `qid`: The entity id, e.g. ``"Q2"``.
- `language`: Language code for labels/descriptions/aliases.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A populated `Item`.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the entity does not exist.

**Example:**
```python
>>> from netgo.wiki import entity
>>> e = entity("Q2")
>>> e.labels["en"]
'Earth'
```

### `search(query: str, language: str = 'en', limit: int = 10, client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> list[netgo.wiki.models.Item]`
Search Wikidata by label.

Uses ``wbsearchentities``, the same backend as Wikidata's own search box: each hit is a partial `Item` with the QID, label and description in the requested language.

**Args:**
- `query`: The text to search for.
- `language`: Language code for the matched label.
- `limit`: Maximum number of hits.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of partial `Item` objects.  

**Example:**
```python
>>> from netgo.wiki import wikidata_search
>>> hits = wikidata_search("Mount Everest", limit=2)
>>> hits[0].labels["en"]
'Mount Everest'
```

### `claims(qid: str, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> dict[str, list[netgo.wiki.models.Claim]]`
Return all claims (facts) of an entity.

Each property id maps to its list of `Claim` values, so ``claims("Q2")["P31"][0].value`` reads "Earth is an instance of ...".

**Args:**
- `qid`: The entity id, e.g. ``"Q2"``.
- `language`: Language code used for labels.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A mapping ``pid -> [Claim]``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the entity does not exist.

**Example:**
```python
>>> from netgo.wiki import claims
>>> props = claims("Q2")
>>> "P31" in props
True
```

### `labels(qid: str, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> dict[str, str]`
Return the names of an entity across languages.

**Args:**
- `qid`: The entity id.
- `language`: Preferred language; other languages stay available.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A mapping ``lang_code -> label``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the entity does not exist.

**Example:**
```python
>>> from netgo.wiki import labels
>>> isinstance(labels("Q2"), dict)
True
```

### `aliases(qid: str, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> dict[str, list[str]]`
Return the alternate names of an entity across languages.

**Args:**
- `qid`: The entity id.
- `language`: Preferred language; other languages stay available.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A mapping ``lang_code -> [alias]``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the entity does not exist.

**Example:**
```python
>>> from netgo.wiki import aliases
>>> isinstance(aliases("Q2"), dict)
True
```

### `sitelinks(qid: str, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 10, delay: float = 0.0) -> dict[str, str]`
Return the links from an entity to every sister wiki.

Keys are site keys like ``"enwiki"``, ``"commons"`` or ``"itwikiquote"`` and values are the page titles there.

**Args:**
- `qid`: The entity id.
- `language`: Preferred language used for the label fallbacks.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A mapping ``site_key -> title``.  

**Raises:**
- `netgo.wiki.WikiNotFoundError`: If the entity does not exist.

**Example:**
```python
>>> from netgo.wiki import sitelinks
>>> links = sitelinks("Q2")
>>> "enwiki" in links
True
```

### `_binding_value(binding: dict) -> str`
Map a SPARQL JSON binding to a plain string.

Entity IRIs are trimmed to their QID (``http://www.wikidata.org/ entity/Q2`` -> ``"Q2"``); every other value (literals, external IRIs, blank nodes) keeps the raw ``value`` string.

**Example:**
```python
>>> _binding_value({"value": "http://www.wikidata.org/entity/Q2", "type": "uri"})
'Q2'
>>> _binding_value({"value": "Earth", "type": "literal", "xml:lang": "en"})
'Earth'
```

### `sparql(query: str | None = None, language: str = 'en', client: netgo.wiki.client.WikiClient | None = None, timeout: int = 30, delay: float = 0.0) -> list[dict[str, str]]`
Run a raw SPARQL query against the Wikidata Query Service.

Executes ``query`` on ``query.wikidata.org`` and returns each row as a ``{variable: value}`` dict, with Wikidata entity IRIs trimmed to their QID. The default query demonstrates property ``P624`` (guidance system of a missile): it returns every item carrying a P624 statement together with its value and their English labels.

**Args:**
- `query`: The raw SPARQL query to run. When omitted, a query that selects items with a ``P624`` guidance-system statement is used.
- `language`: Language code interpolated into the default query's ``wikibase:label`` service; ignored when ``query`` is given.
- `client`: Optional `netgo.wiki.WikiClient` to reuse.
- `timeout`: Request timeout in seconds.
- `delay`: Seconds to sleep before the request (rate limiting).

**Returns:**
- A list of rows; each row maps a selected variable name to a plain string value (QIDs for Wikidata entities).  

**Raises:**
- `netgo.wiki.WikiAPIError`: On transport failures, HTTP errors or non-JSON replies (e.g. a malformed query).

**Example:**
```python
>>> from netgo.wiki import sparql
>>> rows = sparql()
>>> rows[0]["item"].startswith("Q")
True
>>> rows = sparql(
...     "SELECT ?page WHERE { wd:Q191157 wdt:P2860 ?page . } LIMIT 5"
... )
```