"""Discover and read a site's XML sitemaps.

``netgo.sitemap`` finds the sitemaps a site declares in ``robots.txt``
(``discover``), parses a single sitemap URL (``load``/``parse``), crawls
a whole sitemap index tree down to every page URL (``crawl``) and filters
the crawled URLs by a prefix (``filter_by_prefix``).
"""

from netgo import SitemapError, sitemap

SITE = "https://www.example.com"


def main():
    found = sitemap.discover(SITE)
    print(f"{len(found)} sitemap(s) declared in robots.txt of {SITE}")
    for url in found:
        print("  -", url)

    if not found:
        print("no sitemaps advertised; nothing else to do")
        return

    root = found[0]
    try:
        sm = sitemap.load(root)
    except SitemapError as exc:
        print(f"could not load {root}: {exc}")
        return

    print(f"\n{sm.url} -> kind={sm.kind}, {len(sm)} entries")

    if sm.kind == "sitemapindex":
        print("child sitemaps:")
        for child in sm.children:
            print("  -", child)

    print("\nfirst 5 page URLs:")
    for entry in sitemap.crawl(root)[:5]:
        print("  -", entry.loc, entry.lastmod)

    print("\nfilter all pages under a URL prefix:")
    prefix = f"{SITE}/"
    for entry in sitemap.filter_by_prefix(root, prefix)[:5]:
        print("  -", entry.loc)


if __name__ == "__main__":
    main()