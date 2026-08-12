"""Wikidata API: structured data about entities.

Wikidata stores facts as *entities* (Q-items like ``Q2`` = Earth and
P-properties like ``P31`` = instance of) independent of any language.
This module talks to ``www.wikidata.org/w/api.php`` and maps the JSON
onto the :class:`~netgo.wiki.models.Item` and
:class:`~netgo.wiki.models.Claim` models.

Notes:
    - ``language`` selects which translation of the labels/descriptions
      the API returns; it does not change the entity itself.
    - ``wikidata_id`` bridges a Wikipedia title to its QID so you can
      jump from an article to its facts in one helper.
    - :func:`sparql` runs raw SPARQL against ``query.wikidata.org`` for
      questions the Action API cannot answer (e.g. items carrying a
      given property).

Example:
    >>> from netgo.wiki import wikidata_id, entity
    >>> q = wikidata_id("Python (programming language)")
    >>> e = entity(q, language="en")
    >>> e.qid
    'Q28865'
    >>> e.labels["en"] == "Python"
    True
"""

from __future__ import annotations

from .client import WikiClient
from .errors import WikiNotFoundError
from .models import Claim, Item


def _query(
    params: dict[str, object],
    *,
    client: WikiClient | None = None,
    language: str = "en",
    timeout: int = 10,
    delay: float = 0.0,
) -> dict:
    """Run a Wikidata API call through a shared client."""
    client = client or WikiClient(lang=language, host="wikidata", timeout=timeout, delay=delay)
    return client.api_call(params)


_ENTITY_PREFIX = {"item": "Q", "property": "P", "lexeme": "L", "form": "F", "sense": "S"}


def _claim_value(mainsnak: dict):
    """Map a Wikidata snak to a plain Python value.

    Item ids become ``"Q123"`` strings, quantities keep their ``amount``,
    dates keep the ISO ``time`` string, and plain values pass through.

    Example:
        >>> _claim_value({"snaktype": "value", "datavalue": {"value": "Q5"}})
        'Q5'
    """
    if mainsnak.get("snaktype") != "value":
        return None
    value = mainsnak.get("datavalue", {}).get("value")
    if isinstance(value, dict):
        if "entity-type" in value:
            prefix = _ENTITY_PREFIX.get(value.get("entity-type"), "")
            return f"{prefix}{value.get('numeric-id', '')}"
        for key in ("amount", "time", "text"):
            if key in value:
                return value[key]
        return value.get("id") or value
    return value


def _parse_claims(raw_claims: dict) -> dict[str, list[Claim]]:
    """Turn a raw Wikidata ``claims`` object into ``pid -> [Claim]``."""
    out: dict[str, list[Claim]] = {}
    for pid, snaks in (raw_claims or {}).items():
        claims = []
        for snak in snaks:
            main = snak.get("mainsnak", {})
            claim = Claim(
                pid=pid,
                datatype=snak.get("datatype") or main.get("datatype", ""),
                value=_claim_value(main),
            )
            qualifiers = snak.get("qualifiers") or {}
            if qualifiers:
                claim.qualifiers = {
                    qpid: [_claim_value(q) for q in qsnaks]
                    for qpid, qsnaks in qualifiers.items()
                }
            claims.append(claim)
        out[pid] = claims
    return out


def _first_entity(payload: dict, qid: str, *, language: str) -> dict:
    """Pull the single entity object out of a ``wbgetentities`` reply."""
    entities = payload.get("entities", {})
    if not entities or qid not in entities:
        raise WikiNotFoundError(qid, lang=language)
    return entities[qid]


def wikidata_id(
    title: str,
    lang: str = "en",
    site: str = "wikipedia",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> str:
    """Resolve a wiki page title to its Wikidata QID.

    Looks for the ``wikibase_item`` page property on the given language
    edition, which every real Wikipedia article carries.

    Args:
        title: The page title on the wiki (e.g. ``"Python"``).
        lang: Language code of the wiki edition to query.
        site: Site key of the wiki (nearly always ``"wikipedia"``).
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        The QID string, e.g. ``"Q28865"``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the page has no Wikidata link.

    Example:
        >>> from netgo.wiki import wikidata_id
        >>> wikidata_id("Python (programming language)")
        'Q28865'
    """
    client = client or WikiClient(lang=lang, timeout=timeout, delay=delay)
    payload = client.api_call(
        {
            "action": "query",
            "titles": title,
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "redirects": True,
        }
    )
    pages = payload.get("query", {}).get("pages", {})
    for p in pages.values():
        props = p.get("pageprops", {})
        qid = props.get("wikibase_item")
        if qid:
            return qid
    raise WikiNotFoundError(title, lang=lang)


def entity(
    qid: str,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> Item:
    """Fetch a full Wikidata entity and structure it.

    Brings back labels, descriptions, aliases, claims and sitelinks for
    the given QID in the requested language.

    Args:
        qid: The entity id, e.g. ``"Q2"``.
        language: Language code for labels/descriptions/aliases.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A populated :class:`Item`.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the entity does not exist.

    Example:
        >>> from netgo.wiki import entity
        >>> e = entity("Q2")
        >>> e.labels["en"]
        'Earth'
    """
    payload = _query(
        {
            "action": "wbgetentities",
            "ids": qid,
            "languages": language,
            "props": "labels|descriptions|aliases|claims|sitelinks",
        },
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    raw = _first_entity(payload, qid, language=language)
    return Item(
        qid=qid,
        labels={k: v.get("value", "") for k, v in raw.get("labels", {}).items()},
        descriptions={
            k: v.get("value", "") for k, v in raw.get("descriptions", {}).items()
        },
        aliases={
            k: [a.get("value", "") for a in (v or [])]
            for k, v in raw.get("aliases", {}).items()
        },
        claims=_parse_claims(raw.get("claims", {})),
        sitelinks={
            k: v.get("title", "") for k, v in raw.get("sitelinks", {}).items()
        },
    )


def search(
    query: str,
    language: str = "en",
    limit: int = 10,
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> list[Item]:
    """Search Wikidata by label.

    Uses ``wbsearchentities``, the same backend as Wikidata's own search
    box: each hit is a partial :class:`Item` with the QID, label and
    description in the requested language.

    Args:
        query: The text to search for.
        language: Language code for the matched label.
        limit: Maximum number of hits.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of partial :class:`Item` objects.

    Example:
        >>> from netgo.wiki import wikidata_search
        >>> hits = wikidata_search("Mount Everest", limit=2)
        >>> hits[0].labels["en"]
        'Mount Everest'
    """
    payload = _query(
        {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "limit": min(limit, 50),
            "type": "item",
        },
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    out = []
    for hit in payload.get("search", []):
        out.append(
            Item(
                qid=hit.get("id", ""),
                labels={language: hit.get("label", "")},
                descriptions={language: hit.get("description", "")},
            )
        )
    return out


def claims(
    qid: str,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> dict[str, list[Claim]]:
    """Return all claims (facts) of an entity.

    Each property id maps to its list of :class:`Claim` values, so
    ``claims("Q2")["P31"][0].value`` reads "Earth is an instance of ...".

    Args:
        qid: The entity id, e.g. ``"Q2"``.
        language: Language code used for labels.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A mapping ``pid -> [Claim]``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the entity does not exist.

    Example:
        >>> from netgo.wiki import claims
        >>> props = claims("Q2")
        >>> "P31" in props
        True
    """
    payload = _query(
        {"action": "wbgetclaims", "entity": qid},
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    raw = payload.get("claims", {})
    if not raw:
        raise WikiNotFoundError(qid, lang=language)
    return _parse_claims(raw)


def labels(
    qid: str,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> dict[str, str]:
    """Return the names of an entity across languages.

    Args:
        qid: The entity id.
        language: Preferred language; other languages stay available.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A mapping ``lang_code -> label``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the entity does not exist.

    Example:
        >>> from netgo.wiki import labels
        >>> isinstance(labels("Q2"), dict)
        True
    """
    payload = _query(
        {"action": "wbgetentities", "ids": qid, "props": "labels", "languages": language},
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    raw = _first_entity(payload, qid, language=language)
    return {k: v.get("value", "") for k, v in raw.get("labels", {}).items()}


def aliases(
    qid: str,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> dict[str, list[str]]:
    """Return the alternate names of an entity across languages.

    Args:
        qid: The entity id.
        language: Preferred language; other languages stay available.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A mapping ``lang_code -> [alias]``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the entity does not exist.

    Example:
        >>> from netgo.wiki import aliases
        >>> isinstance(aliases("Q2"), dict)
        True
    """
    payload = _query(
        {"action": "wbgetentities", "ids": qid, "props": "aliases", "languages": language},
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    raw = _first_entity(payload, qid, language=language)
    return {
        k: [a.get("value", "") for a in (v or [])]
        for k, v in raw.get("aliases", {}).items()
    }


def sitelinks(
    qid: str,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 10,
    delay: float = 0.0,
) -> dict[str, str]:
    """Return the links from an entity to every sister wiki.

    Keys are site keys like ``"enwiki"``, ``"commons"`` or ``"itwikiquote"``
    and values are the page titles there.

    Args:
        qid: The entity id.
        language: Preferred language used for the label fallbacks.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A mapping ``site_key -> title``.

    Raises:
        ~netgo.wiki.WikiNotFoundError: If the entity does not exist.

    Example:
        >>> from netgo.wiki import sitelinks
        >>> links = sitelinks("Q2")
        >>> "enwiki" in links
        True
    """
    payload = _query(
        {"action": "wbgetentities", "ids": qid, "props": "sitelinks"},
        client=client,
        language=language,
        timeout=timeout,
        delay=delay,
    )
    raw = _first_entity(payload, qid, language=language)
    return {k: v.get("title", "") for k, v in raw.get("sitelinks", {}).items()}


_P624_QUERY = """\
SELECT ?item ?itemLabel ?guidanceSystem ?guidanceSystemLabel WHERE {
  ?item wdt:P624 ?guidanceSystem .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "{LANG}". }
}
LIMIT 25
"""


def _binding_value(binding: dict) -> str:
    """Map a SPARQL JSON binding to a plain string.

    Entity IRIs are trimmed to their QID (``http://www.wikidata.org/
    entity/Q2`` -> ``"Q2"``); every other value (literals, external
    IRIs, blank nodes) keeps the raw ``value`` string.

    Example:
        >>> _binding_value({"value": "http://www.wikidata.org/entity/Q2", "type": "uri"})
        'Q2'
        >>> _binding_value({"value": "Earth", "type": "literal", "xml:lang": "en"})
        'Earth'
    """
    value = binding.get("value", "")
    if binding.get("type") == "uri" and value.startswith(
        "http://www.wikidata.org/entity/"
    ):
        return value.rsplit("/", 1)[-1]
    return value


def sparql(
    query: str | None = None,
    language: str = "en",
    client: WikiClient | None = None,
    timeout: int = 30,
    delay: float = 0.0,
) -> list[dict[str, str]]:
    """Run a raw SPARQL query against the Wikidata Query Service.

    Executes ``query`` on ``query.wikidata.org`` and returns each row as
    a ``{variable: value}`` dict, with Wikidata entity IRIs trimmed to
    their QID. The default query demonstrates property ``P624``
    (guidance system of a missile): it returns every item carrying a
    P624 statement together with its value and their English labels.

    Args:
        query: The raw SPARQL query to run. When omitted, a query that
            selects items with a ``P624`` guidance-system statement is
            used.
        language: Language code interpolated into the default query's
            ``wikibase:label`` service; ignored when ``query`` is given.
        client: Optional :class:`~netgo.wiki.WikiClient` to reuse.
        timeout: Request timeout in seconds.
        delay: Seconds to sleep before the request (rate limiting).

    Returns:
        A list of rows; each row maps a selected variable name to a
        plain string value (QIDs for Wikidata entities).

    Raises:
        ~netgo.wiki.WikiAPIError: On transport failures, HTTP errors or
            non-JSON replies (e.g. a malformed query).

    Example:
        >>> from netgo.wiki import sparql
        >>> rows = sparql()
        >>> rows[0]["item"].startswith("Q")
        True
        >>> rows = sparql(
        ...     "SELECT ?page WHERE { wd:Q191157 wdt:P2860 ?page . } LIMIT 5"
        ... )
    """
    client = client or WikiClient(timeout=timeout, delay=delay)
    if query is None:
        query = _P624_QUERY.replace("{LANG}", language)
    payload = client.sparql_call(query)
    out = []
    for binding in payload.get("results", {}).get("bindings", []):
        out.append({var: _binding_value(data) for var, data in binding.items()})
    return out


__all__ = [
    "wikidata_id",
    "entity",
    "search",
    "claims",
    "labels",
    "aliases",
    "sitelinks",
    "sparql",
]