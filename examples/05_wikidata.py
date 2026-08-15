"""From a Wikipedia title to structured Wikidata facts.

Resolves the article to its QID, fetches the full entity and reads its
labels, claims, aliases and sitelinks. Also executes raw SPARQL queries.
"""

# Import Wikidata helpers from netgo.wiki
import netgo.wiki as wiki

# Common Wikidata Property ID mapping for readable output
PROPS = {
    "P31": "instance of",
    "P279": "subclass of",
    "P571": "inception",
    "P112": "founded by",
}


def main():
    title = "Python (programming language)"

    # -------------------------------------------------------------
    # 1. Resolve Wikipedia title to Wikidata QID
    # -------------------------------------------------------------
    # `wikidata_id(title)`: looks up the unique entity identifier (e.g. Q28865)
    qid = wiki.wikidata_id(title)
    print(f"Article: {title!r} -> Wikidata QID: {qid}")

    # -------------------------------------------------------------
    # 2. Fetch full entity model
    # -------------------------------------------------------------
    # `entity(qid, language="en")`: loads structured data (claims, labels, descriptions)
    item = wiki.entity(qid, language="en")
    print(f"\n== Wikidata Entity: {item.qid} ==")
    print(f"  English Label : {item.labels.get('en')}")
    print(f"  Description   : {item.descriptions.get('en')}")

    # -------------------------------------------------------------
    # 3. Read structured claims & statements
    # -------------------------------------------------------------
    # `item.claims`: dictionary mapping property IDs (e.g., P31) to claim values
    print("\n== Key Claims ==")
    for pid, claims in item.claims.items():
        if pid in PROPS:
            values = [c.value for c in claims]
            print(f"  {PROPS[pid]:>14} ({pid}): {values}")

    # -------------------------------------------------------------
    # 4. Aliases and multi-lingual Sitelinks
    # -------------------------------------------------------------
    # `item.aliases`: alternative names / search terms
    print(f"\n== Aliases (en) ==\n  {item.aliases.get('en', [])}")

    # `item.sitelinks`: mappings across Wikimedia projects (Wikipedia, Wikiquote, etc.)
    print(f"\n== Sitelinks ({len(item.sitelinks)} connected sites) ==")
    for site in ["enwiki", "itwiki", "dewiki", "frwiki", "eswiki"]:
        if site in item.sitelinks:
            print(f"  {site:8}: {item.sitelinks[site]}")

    # -------------------------------------------------------------
    # 5. Execute raw SPARQL query
    # -------------------------------------------------------------
    # `wiki.sparql(...)`: executes SPARQL on the Wikidata query service
    print("\n== Raw SPARQL Query (Items with guidance system P624) ==")
    rows = wiki.sparql(language="en")
    for row in rows[:5]:
        item_lbl = row.get("itemLabel")
        sys_lbl = row.get("guidanceSystemLabel")
        print(f"  {row.get('item')}: {item_lbl} -> {sys_lbl}")


if __name__ == "__main__":
    main()