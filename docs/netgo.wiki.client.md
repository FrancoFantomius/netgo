# Shared HTTP client for the MediaWiki Action API.

`WikiClient` wraps a `requests.Session` and points it at one of the four Wikimedia wikis that netgo talks to (Wikipedia, Wikidata, Wikimedia Commons, Wiktionary). Every higher-level function in `netgo.wiki` builds (or reuses) a client and drives it through `WikiClient.api_call`, which handles the common plumbing: the ``format=json`` flag, error handling and missing-page detection. For the Wikidata Query Service, `WikiClient.sparql_call` runs raw SPARQL queries through the same session and rate-limiting settings.

The constructor is public so advanced users can reuse a single session (or inject their own ``requests.Session`` with proxies/timeouts) across many calls:

>>> from netgo.wiki import WikiClient >>> client = WikiClient(lang="de") >>> client.base_url 'https://de.wikipedia.org/w/api.php'

>>> from netgo.wiki import search >>> search("berlin", client=client)[0].title 'Berlin'

### class `WikiClient`
```python
WikiClient(lang: 'str' = 'en', host: 'str' = 'wikipedia', session: 'requests.Session | None' = None, timeout: 'int' = 10, delay: 'float' = 0.0, headers: 'dict' = <factory>) -> None
```
A session wrapper around a single MediaWiki endpoint.

Attributes: lang: Language code used by language-specific hosts (``wikipedia``, ``wiktionary``); ignored otherwise. host: Which wiki to talk to: ``"wikipedia"``, ``"wikidata"``, ``"wikimedia"`` or ``"wiktionary"``. session: A `requests.Session` to reuse; created on demand when ``None``. timeout: Request timeout in seconds. delay: Seconds to sleep before every request (rate limiting). headers: Extra headers merged over the defaults.

**Example:**
```python
>>> from netgo.wiki import WikiClient
>>> c = WikiClient(lang="it", host="wikipedia", delay=0.1)
>>> c.base_url
'https://it.wikipedia.org/w/api.php'
>>> c.host == "wikipedia"
True
```
**Fields:**
- `lang` = 'en'
- `host` = 'wikipedia'
- `session` = None
- `timeout` = 10
- `delay` = 0.0
- `headers`

### `_all_missing(payload: dict) -> bool`
Return True when every page in the payload is marked missing.

### `_subject(payload: dict) -> str`
Pick a human-readable subject for NotFound errors.

### `default_client(lang: str = 'en', **kwargs) -> netgo.wiki.client.WikiClient`
Return a `WikiClient` pre-pointed at the given Wikipedia.

Convenience helper used by the module-level entry points; passes any extra ``kwargs`` through to `WikiClient`.

**Example:**
```python
>>> from netgo.wiki import default_client
>>> c = default_client("fr", delay=0.2)
>>> c.base_url
'https://fr.wikipedia.org/w/api.php'
```