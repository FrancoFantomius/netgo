"""Search Google and Bing through the same engine-agnostic API.

Every backend returns the same list of ``netgo.Result`` objects, so
switching engines never touches your data models or downstream code.
"""

# Import the unified search entry point from netgo
from netgo import search


def show(label, results):
    """Helper to display search results in a readable format.
    
    Each `Result` object has:
      - `position`: 1-based index on the search engine results page
      - `title`: Extracted title text
      - `url`: Direct link to the result
      - `snippet`: Text preview or snippet from the search engine
    """
    print(f"\n== {label} ==")
    for r in results:
        print(f"  #{r.position}: {r.title}")
        print(f"          {r.url}")
        print(f"          {r.snippet[:100]}")


def main():
    # -------------------------------------------------------------
    # 1. Standard Google Search (default engine)
    # -------------------------------------------------------------
    # `num`: number of search results to fetch (default is 10)
    query = "python web scraping"
    print("Executing standard Google search...")
    show("Google (default)", search(query, num=5))

    # -------------------------------------------------------------
    # 2. Bing Search using the identical interface
    # -------------------------------------------------------------
    # `engine="bing"`: select the Bing backend instead of Google
    print("Executing Bing search...")
    show("Bing", search(query, num=5, engine="bing"))

    # -------------------------------------------------------------
    # 3. Paginated Search
    # -------------------------------------------------------------
    # `start`: offset to begin results from (e.g., start=5 gets page 2 if num=5)
    print("Fetching paginated results...")
    show(
        "Google, paginated page 2",
        search(query, num=5, start=5),
    )

    # -------------------------------------------------------------
    # 4. Search with Safe Search and Language Filter
    # -------------------------------------------------------------
    # `safe=True`: enable strict safe search filtering
    # `lang="it"`: prioritize results in Italian
    print("Executing filtered search...")
    show(
        "Bing, safe search on, Italian",
        search(query, num=5, engine="bing", safe=True, lang="it"),
    )


if __name__ == "__main__":
    main()