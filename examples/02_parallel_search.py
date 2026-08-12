"""Run many search queries at once with ``netgo.search_many``.

Queries execute in parallel in a thread pool. A failing query does not
abort the others: it maps to an empty list and stores its exception under
``"<query>_error"``.
"""

from netgo import search_many


def main():
    queries = [
        "python asyncio tutorial",
        "web scraping best practices",
        "rust vs go 2025",
        "sqlite full text search",
    ]

    out = search_many(queries, engine="bing", num=3, max_workers=4)

    for query, results in out.items():
        if query.endswith("_error"):
            print(f"  {query} raised {type(results).__name__}: {results}")
        elif results:
            print(f"{query!r}: {len(results)} results")
            for r in results:
                print(f"  {r.position}. {r.title}")
        else:
            print(f"{query!r}: no results (blocked or empty page)")


if __name__ == "__main__":
    main()