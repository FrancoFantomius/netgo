"""Deep-dive into a Wikipedia article with ``netgo.wiki``.

Searches for the article, then walks its structure: summary, section
outline, outgoing links, backlinks, categories and embedded images.
"""

# Import the high-level Wikipedia API helpers
import netgo.wiki as wiki


def main():
    title = "Python (programming language)"

    # -------------------------------------------------------------
    # 1. Search Wikipedia articles
    # -------------------------------------------------------------
    # `wiki.search(query, limit=3)`: performs full-text title and content search
    hits = wiki.search(title, limit=3)
    print(f"== Search Hits ({len(hits)}) ==")
    for h in hits:
        print(f"  {h.title!r} (Word count: {h.wordcount}, Size: {h.size} bytes)")

    # -------------------------------------------------------------
    # 2. Retrieve structured page details
    # -------------------------------------------------------------
    # `wiki.page(title)`: loads page summary, full text, sections, links, and categories
    page = wiki.page(title)
    print(f"\n== Page: {page.title} ==")
    print(f"  URL     : {page}")
    print(f"  Summary : {page.summary[:180]}...")

    # -------------------------------------------------------------
    # 3. Table of Contents & Sections
    # -------------------------------------------------------------
    # `page.sections`: list of `Section` objects containing heading title and nesting level
    print(f"\n== Table of Contents ({len(page.sections)} sections) ==")
    for s in page.sections[:8]:
        indent = "  " * (s.level - 1)
        print(f"  {indent}[{s.index}] {s.title}")

    # -------------------------------------------------------------
    # 4. Categories & Taxonomy
    # -------------------------------------------------------------
    # `page.categories`: list of Wikipedia categories the page belongs to
    print(f"\n== Categories ({len(page.categories)}) ==")
    for c in page.categories[:6]:
        print(f"  - {c.title}")

    # -------------------------------------------------------------
    # 5. Outgoing Links & Embedded Images
    # -------------------------------------------------------------
    # `page.links`: internal links to other Wikipedia articles
    print(f"\n== Outgoing Links ({len(page.links)}) ==")
    for l in page.links[:6]:
        print(f"  -> {l.title}")

    # `page.images`: file names of images referenced on the page
    print(f"\n== Embedded Images ({len(page.images)}) ==")
    for i in page.images[:5]:
        print(f"  - {i.title}")

    # -------------------------------------------------------------
    # 6. Backlinks (Pages linking to this article)
    # -------------------------------------------------------------
    # `wiki.backlinks(title, limit=5)`: queries which other articles reference this page
    print(f"\n== Backlinks (What links here) ==")
    for l in wiki.backlinks(title, limit=5):
        print(f"  <- {l.title}")


if __name__ == "__main__":
    main()