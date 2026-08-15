"""Find Wikimedia Commons files and inspect their metadata.

``search_images`` returns matching file names; ``file_info`` resolves a
name to its direct download URL, thumbnail, MIME type, dimensions, and licence.
"""

# Import Wikimedia Commons helpers from netgo.wiki
import netgo.wiki as wiki


def main():
    query = "sunflower"

    # -------------------------------------------------------------
    # 1. Search media files on Wikimedia Commons
    # -------------------------------------------------------------
    # `search_images(query, limit=3)`: finds files matching the search terms
    hits = wiki.search_images(query, limit=3)
    print(f"== Media files matching {query!r} ({len(hits)} returned) ==")
    for f in hits:
        print(f"  - {f.name}")

    # -------------------------------------------------------------
    # 2. Inspect detailed file metadata and image URLs
    # -------------------------------------------------------------
    # `file_info(name, thumb_width=640)`: retrieves resolution, licence,
    # author, and generates scaled thumbnail links.
    for hit in hits[:2]:
        info = wiki.file_info(hit.name, thumb_width=640)
        print(f"\n== File Details: {info.name} ==")
        print(f"  Direct URL     : {info.url}")
        print(f"  Thumbnail (640): {info.thumburl}")
        print(f"  Dimensions     : {info.width} x {info.height} px")
        print(f"  Size & MIME    : {info.size} bytes ({info.mime})")
        print(f"  Licence        : {info.license}")
        print(f"  Artist/Author  : {info.artist}")
        print(f"  Description    : {info.description[:120]}...")

    # -------------------------------------------------------------
    # 3. Direct Image URL convenience helper
    # -------------------------------------------------------------
    # `image_url(name)`: fast single-step URL resolution
    print("\n== Quick Direct URL ==")
    print(f"  {wiki.image_url(hits[0].name)}")

    # -------------------------------------------------------------
    # 4. Fetch random Commons files
    # -------------------------------------------------------------
    # `random_file(limit=1)`: retrieves randomly selected file entries
    print("\n== Random Commons File ==")
    for r in wiki.random_file(limit=1):
        print(f"  - {r.name}")


if __name__ == "__main__":
    main()