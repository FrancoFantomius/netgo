"""Deep-dive into a Wikipedia article with ``netgo.wiki``.

Searches for the article, then walks its structure: summary, section
outline, outgoing links, backlinks, categories and embedded images.
"""

import netgo.wiki as wiki


def main():
    title = "Python (programming language)"

    hits = wiki.search(title, limit=3)
    print(f"== search hits ({len(hits)}) ==")
    for h in hits:
        print(f"  {h.title!r}, {h.wordcount} words, {h.size} bytes")

    page = wiki.page(title)
    print(f"\n== page: {page.title} ==")
    print(f"  full url: {page}")
    print(f"  summary : {page.summary[:160]}...")

    print(f"\n== sections ({len(page.sections)}) ==")
    for s in page.sections[:8]:
        print(f"  {'  ' * (s.level - 1)}[{s.index}] {s.title}")

    print(f"\n== categories ({len(page.categories)}) ==")
    for c in page.categories[:8]:
        print(f"  - {c.title}")

    print(f"\n== outgoing links ({len(page.links)}) ==")
    for l in page.links[:8]:
        print(f"  -> {l.title}")

    print(f"\n== embedded images ({len(page.images)}) ==")
    for i in page.images[:5]:
        print(f"  - {i.title}")

    print(f"\n== backlinks (what links here) ==")
    for l in wiki.backlinks(title, limit=5):
        print(f"  <- {l.title}")


if __name__ == "__main__":
    main()