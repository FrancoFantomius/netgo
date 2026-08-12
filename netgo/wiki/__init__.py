"""netgo.wiki - wrappers around the MediaWiki Action API.

Talks to four Wikimedia wikis through a single shared
:class:`~netgo.wiki.client.WikiClient`:

- **Wikipedia** (:mod:`netgo.wiki.core`) - full-text search, article
  summaries and paragraphs, section outlines, links, backlinks,
  categories, images, random pages and geo search.
- **Wikidata** (:mod:`netgo.wiki.wikidata`) - resolve article titles to
  QIDs, fetch entities, search labels, read claims/properties, aliases
  and sitelinks.
- **Wikimedia Commons** (:mod:`netgo.wiki.wikimedia`) - find media files
  and fetch their URLs, thumbnails and licensing metadata.
- **Wiktionary** (:mod:`netgo.wiki.wiktionary`) - dictionary
  definitions, etymology and the languages a word exists in.

Every function returns structured dataclasses (see
:mod:`netgo.wiki.models`) and raises ``WikiError`` subclasses on
failure, so a ``try/except WikiError`` covers the whole subpackage.

Example:
    >>> from netgo.wiki import search, summary, wikidata_id
    >>> hits = search("machine learning", limit=3)
    >>> hits[0].title
    'Machine learning'
    >>> summary("Bread", sentences=1).startswith("Bread is")
    True
    >>> wikidata_id("Python (programming language)")
    'Q28865'
"""

from .client import WikiClient, default_client
from .core import (
    backlinks,
    categories,
    geo_search,
    images,
    links,
    page,
    pageinfo,
    paragraphs,
    random,
    sections,
    search,
    search_many,
    summary,
)
from .errors import WikiAPIError, WikiError, WikiNotFoundError
from .models import (
    Article,
    Category,
    Claim,
    Entry,
    GeoResult,
    Image,
    Item,
    Link,
    MediaFile,
    Section,
    WikiResult,
)
from .wikidata import (
    aliases,
    claims,
    entity,
    labels,
    sitelinks,
    wikidata_id,
)
from .wikidata import search as wikidata_search
from .wikimedia import file_info, image_url, random_file, search_images
from .wiktionary import definition, etymology, languages
from .wiktionary import search as wiktionary_search
from .wiktionary import definition as wiktionary_definition

__all__ = [
    # client
    "WikiClient",
    "default_client",
    # errors
    "WikiError",
    "WikiAPIError",
    "WikiNotFoundError",
    # models
    "WikiResult",
    "Article",
    "Section",
    "Link",
    "Category",
    "Image",
    "GeoResult",
    "Item",
    "Claim",
    "MediaFile",
    "Entry",
    # Wikipedia core
    "search",
    "search_many",
    "summary",
    "paragraphs",
    "sections",
    "links",
    "backlinks",
    "categories",
    "images",
    "pageinfo",
    "page",
    "random",
    "geo_search",
    # Wikidata
    "wikidata_id",
    "entity",
    "claims",
    "labels",
    "aliases",
    "sitelinks",
    "wikidata_search",
    # Wikimedia Commons
    "search_images",
    "file_info",
    "image_url",
    "random_file",
    # Wiktionary
    "definition",
    "wiktionary_definition",
    "etymology",
    "languages",
    "wiktionary_search",
]