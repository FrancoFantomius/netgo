"""From a Wikipedia title to structured Wikidata facts.

Resolves the article to its QID, fetches the full entity and reads its
labels, claims, aliases and sitelinks.
"""

import netgo.wiki as wiki

PROPS = {
    "P31": "instance of",
    "P279": "subclass of",
    "P571": "inception",
    "P112": "founded by",
}


def main():
    title = "Python (programming language)"

    qid = wiki.wikidata_id(title)
    print(f"{title!r} -> {qid}")

    item = wiki.entity(qid, language="en")
    print(f"\n== entity: {item.qid} ==")
    print(f"  labels      : {item.labels}")
    print(f"  description : {item.descriptions.get('en')}")

    print("\n== claims ==")
    for pid, claims in item.claims.items():
        if pid in PROPS:
            values = [c.value for c in claims]
            print(f"  {PROPS[pid]:>12} ({pid}): {values}")

    print("\n== aliases (en) ==")
    print(" ", item.aliases.get("en", []))

    print("\n== sitelinks ==")
    for site, page in sorted(item.sitelinks.items()):
        print(f"  {site}: {page}")


if __name__ == "__main__":
    main()