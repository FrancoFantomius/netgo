"""The full journey in one script: search -> fetch -> enrich with Wikipedia.

1. Search an engine for a topic and keep the top organic results.
2. Follow the best result with ``netgo.fetch`` to read the article body.
3. Cross-reference the topic on Wikipedia and pull its Wikidata facts.

This is the shape of a small "research a topic" automation built purely
from netgo's public API.
"""

from netgo import PageError, fetch, search
from netgo.wiki import WikiError, entity, page, wikidata_id


def topic_research(topic, engine="bing", num=3):
    print(f"########## topic: {topic} ##########\n")

    results = search(topic, engine=engine, num=num)
    print(f"== top {len(results)} web results ==")
    for r in results:
        print(f"  #{r.position} {r.title}")

    best_url = results[0].url if results else None
    if best_url:
        try:
            web = fetch(best_url, timeout=15)
            print(f"\n== fetched {web.site} ==")
            print(f"  title: {web.title}")
            print(f"  paragraph 1: {web.paragraphs[0][:200]}...")
        except PageError as exc:
            print(f"\n== could not fetch {best_url}: {exc}")

    try:
        art = page(topic)
        print(f"\n== wikipedia: {art.title} ==")
        print(f"  summary: {art.summary[:160]}...")

        qid = wikidata_id(art.title)
        item = entity(qid, language="en")
        print(f"  wikidata {qid}: {item.labels.get('en')}")
        print(f"  description: {item.descriptions.get('en')}")
    except WikiError as exc:
        print(f"\n== wikipedia/wiki.data unavailable: {exc}")


def main():
    for topic in ["okapi", "fermentation"]:
        topic_research(topic)


if __name__ == "__main__":
    main()