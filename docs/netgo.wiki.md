# netgo.wiki - wrappers around the MediaWiki Action API.

Talks to four Wikimedia wikis through a single shared `netgo.wiki.client.WikiClient`:

- \*\*Wikipedia\*\* (`netgo.wiki.core`) - full-text search, article

summaries and paragraphs, section outlines, links, backlinks, categories, images, random pages and geo search.

- \*\*Wikidata\*\* (`netgo.wiki.wikidata`) - resolve article titles to

QIDs, fetch entities, search labels, read claims/properties, aliases and sitelinks, and run raw SPARQL queries.

- \*\*Wikimedia Commons\*\* (`netgo.wiki.wikimedia`) - find media files

and fetch their URLs, thumbnails and licensing metadata.

- \*\*Wiktionary\*\* (`netgo.wiki.wiktionary`) - dictionary

definitions, etymology and the languages a word exists in.

Every function returns structured dataclasses (see `netgo.wiki.models`) and raises ``WikiError`` subclasses on failure, so a ``try/except WikiError`` covers the whole subpackage.

**Example:**
```python
>>> from netgo.wiki import search, summary, wikidata_id
>>> hits = search("machine learning", limit=3)
>>> hits[0].title
'Machine learning'
>>> summary("Bread", sentences=1).startswith("Bread is")
True
>>> wikidata_id("Python (programming language)")
'Q28865'
```