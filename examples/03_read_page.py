"""Fetch any web page and read just its main content.

``netgo.fetch`` strips the site template (navigation, headers, footers,
sidebars, banners) and leaves the actual article behind as a ``Page``.
"""

from netgo import PageError, fetch


def main():
    url = "https://www.bbc.co.uk/news/science-environment-56837908"

    try:
        page = fetch(url)
    except PageError as exc:
        print(f"could not read {url}: {exc}")
        return

    print(f"title : {page.title}")
    print(f"site  : {page.site}")
    print(f"url   : {page.url}\n")

    print(f"== first 3 paragraphs of {len(page.paragraphs)} ==")
    for para in page.paragraphs[:3]:
        print("\n" + para)

    print("\ncontainers of extracted html:", page.html[:120].replace("\n", " ") + "...")


if __name__ == "__main__":
    main()