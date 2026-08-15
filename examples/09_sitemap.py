"""Discover and read a site's XML sitemaps.

``netgo.sitemap`` finds the sitemaps a site declares in ``robots.txt``
(``discover``), parses a single sitemap URL (``load``/``parse``), crawls
a whole sitemap index tree down to every page URL (``crawl``) and filters
the crawled URLs by a prefix (``filter_by_prefix``).
"""

# Import sitemap tools and error classes
from netgo import SitemapError, sitemap

SITE = "https://www.example.com"


def main():
    # -------------------------------------------------------------
    # 1. Discover sitemaps declared in robots.txt
    # -------------------------------------------------------------
    # `sitemap.discover(site_url)`: parses robots.txt to find sitemap URLs
    print(f"Discovering sitemaps declared in robots.txt for: {SITE}")
    found = sitemap.discover(SITE)
    print(f"Found {len(found)} sitemap(s):")
    for url in found:
        print(f"  - {url}")

    if not found:
        print("No sitemaps advertised in robots.txt; ending demo.")
        return

    root_sitemap = found[0]

    # -------------------------------------------------------------
    # 2. Load and parse a specific sitemap
    # -------------------------------------------------------------
    # `sitemap.load(url)`: fetches and parses sitemaps, automatically
    # uncompressing .gz sitemaps and determining kind ("urlset" | "sitemapindex" | "text")
    try:
        sm = sitemap.load(root_sitemap)
    except SitemapError as exc:
        print(f"Could not load sitemap at {root_sitemap}: {exc}")
        return

    print(f"\nLoaded Sitemap: {sm.url}")
    print(f"  Type: {sm.kind} | Total entries: {len(sm)}")

    # If the sitemap is an index pointing to child sitemaps:
    if sm.kind == "sitemapindex":
        print("\nChild Sitemaps:")
        for child in sm.children:
            print(f"  - {child}")

    # -------------------------------------------------------------
    # 3. Crawl entire sitemap tree down to page URLs
    # -------------------------------------------------------------
    # `sitemap.crawl(url)`: recursively traverses sitemap indexes
    print("\nCrawling page URLs (first 5 shown):")
    for entry in sitemap.crawl(root_sitemap)[:5]:
        print(f"  - Loc: {entry.loc} (Last modified: {entry.lastmod})")

    # -------------------------------------------------------------
    # 4. Filter crawled URLs by prefix
    # -------------------------------------------------------------
    # `sitemap.filter_by_prefix(url, prefix)`: returns only URLs starting with prefix
    prefix = f"{SITE}/"
    print(f"\nFiltering URLs with prefix '{prefix}' (first 5 shown):")
    for entry in sitemap.filter_by_prefix(root_sitemap, prefix)[:5]:
        print(f"  - {entry.loc}")


if __name__ == "__main__":
    main()