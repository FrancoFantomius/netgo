"""Run many search queries at once with ``netgo.search_many``.

Queries execute in parallel across a thread pool. A failing query does not
abort the others: it maps to an empty list and stores its exception under
``"<query>_error"``.
"""

# Import the parallel search utility from netgo
from netgo import search_many


def main():
    # Define a list of search queries to execute concurrently
    queries = [
        "python asyncio tutorial",
        "web scraping best practices",
        "rust vs go 2025",
        "sqlite full text search",
    ]

    # -------------------------------------------------------------
    # Execute batch search in parallel
    # -------------------------------------------------------------
    # `engine="bing"`: specify search engine backend ("google" or "bing")
    # `num=3`: number of results requested per query
    # `max_workers=4`: size of the concurrent thread pool
    print(f"Executing {len(queries)} queries in parallel...")
    out = search_many(queries, engine="bing", num=3, max_workers=4)

    # -------------------------------------------------------------
    # Process results and inspect possible errors
    # -------------------------------------------------------------
    for query, results in out.items():
        # netgo stores exceptions under `<query>_error` keys so the rest
        # of the batch continues without crashing
        if query.endswith("_error"):
            print(f"  [ERROR] {query} raised {type(results).__name__}: {results}")
        elif results:
            print(f"\nResults for {query!r} ({len(results)} found):")
            for r in results:
                print(f"  #{r.position} {r.title}")
                print(f"       URL: {r.url}")
        else:
            print(f"\n{query!r}: no results returned (blocked or empty page)")


if __name__ == "__main__":
    main()