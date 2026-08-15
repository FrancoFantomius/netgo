"""Fetch any web page and read just its main content.

``netgo.fetch`` strips the site template (navigation, headers, footers,
sidebars, banners) and leaves the actual article behind as a ``Page`` object.
"""

# Import the fetch helper and base error class
from netgo import PageError, fetch


def main():
    # Target URL to fetch and clean
    url = "https://www.bbc.co.uk/news/science-environment-56837908"

    # -------------------------------------------------------------
    # Fetch and parse the page content
    # -------------------------------------------------------------
    # `fetch(url)` downloads the HTML, detects encoding, strips boilerplate
    # tags (nav, footer, header, scripts, styles), and extracts the article.
    # Handles transport and parsing failures gracefully via `PageError`.
    try:
        page = fetch(url, timeout=15)
    except PageError as exc:
        print(f"Failed to fetch or parse {url}: {exc}")
        return

    # -------------------------------------------------------------
    # Inspect metadata and cleaned content
    # -------------------------------------------------------------
    # `page.title`: Extracted title of the document/article
    # `page.site`: Cleaned hostname/domain
    # `page.url`: Canonical or final fetched URL
    print(f"Title : {page.title}")
    print(f"Site  : {page.site}")
    print(f"URL   : {page.url}\n")

    # `page.paragraphs`: List of non-empty cleaned plain-text paragraphs
    print(f"== First 3 paragraphs of {len(page.paragraphs)} total ==")
    for idx, para in enumerate(page.paragraphs[:3], 1):
        print(f"\n[Paragraph {idx}]")
        print(para)

    # `page.html`: Extracted and cleaned main content HTML (excluding boilerplate)
    # `page.raw`: Raw HTML body returned by the HTTP server
    print("\n== Content HTML snippet ==")
    print(page.html[:160].replace("\n", " ") + "...")


if __name__ == "__main__":
    main()