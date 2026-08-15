"""The full journey in one script: search -> fetch -> enrich with Wikipedia.

1. Search a topic across web engines and select the top organic result.
2. Download the article content with ``netgo.fetch`` and clean the text.
3. Cross-reference the topic on Wikipedia and extract structured Wikidata facts.

This demonstrates how netgo's APIs combine into an end-to-end research pipeline.
"""

# Import the core netgo tools and Wikimedia client methods
from netgo import PageError, fetch, search
from netgo.wiki import WikiError, entity, page, wikidata_id


def topic_research(topic: str, engine: str = "bing", num: int = 3):
    """Run an automated research workflow for a given topic."""
    print(f"\n=======================================================")
    print(f" Researching topic: {topic.upper()}")
    print(f"=======================================================")

    # ---------------------------------------------------------
    # Step 1: Web Search
    # ---------------------------------------------------------
    print(f"\n[Step 1] Searching {engine.title()} for top {num} results...")
    results = search(topic, engine=engine, num=num)
    for r in results:
        print(f"  #{r.position} {r.title}")
        print(f"      {r.url}")

    # ---------------------------------------------------------
    # Step 2: Fetch and Clean Page Body
    # ---------------------------------------------------------
    best_url = results[0].url if results else None
    if best_url:
        print(f"\n[Step 2] Fetching and parsing top result ({best_url})...")
        try:
            web = fetch(best_url, timeout=15)
            print(f"  Title: {web.title}")
            print(f"  Site : {web.site}")
            if web.paragraphs:
                print(f"  Lead paragraph: {web.paragraphs[0][:200]}...")
        except PageError as exc:
            print(f"  Warning: Could not fetch page ({exc})")

    # ---------------------------------------------------------
    # Step 3: Wikipedia & Wikidata Knowledge Enrichment
    # ---------------------------------------------------------
    print(f"\n[Step 3] Cross-referencing Wikipedia & Wikidata...")
    try:
        art = page(topic)
        print(f"  Wikipedia Title   : {art.title}")
        print(f"  Article Summary   : {art.summary[:160]}...")

        # Resolve Wikidata entity
        qid = wikidata_id(art.title)
        item = entity(qid, language="en")
        print(f"  Wikidata Entity ID: {item.qid}")
        print(f"  Entity Label (EN) : {item.labels.get('en')}")
        print(f"  Description       : {item.descriptions.get('en')}")
    except WikiError as exc:
        print(f"  Warning: Wikipedia/Wikidata lookup error ({exc})")


def main():
    # Execute the research pipeline across two topics
    for topic in ["okapi", "fermentation"]:
        topic_research(topic)


if __name__ == "__main__":
    main()