"""Search Google and Bing through the same engine-agnostic API.

Every backend returns the same list of ``netgo.Result`` objects, so
switching engines never touches your code.
"""

from netgo import search


def show(label, results):
    print(f"\n== {label} ==")
    for r in results:
        print(f"  #{r.position}: {r.title}")
        print(f"          {r.url}")
        print(f"          {r.snippet[:100]}")


def main():
    query = "python web scraping"
    show("Google (default)", search(query, num=5))
    show("Bing", search(query, num=5, engine="bing"))

    show(
        "Google, paginated page 2",
        search(query, num=5, start=5),
    )

    show(
        "Bing, safe search on, Italian",
        search(query, num=5, engine="bing", safe=True, lang="it"),
    )


if __name__ == "__main__":
    main()