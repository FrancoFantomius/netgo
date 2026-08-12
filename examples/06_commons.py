"""Find Wikimedia Commons files and inspect their metadata.

``search_images`` returns matching file names; ``file_info`` resolves a
name to its direct download URL, thumbnail, MIME type and licence.
"""

import netgo.wiki as wiki


def main():
    query = "sunflower"

    hits = wiki.search_images(query, limit=3)
    print(f"== files matching {query!r} ({len(hits)}) ==")
    for f in hits:
        print(f"  {f.name}")

    for hit in hits[:2]:
        info = wiki.file_info(hit.name, thumb_width=640)
        print(f"\n== {info.name} ==")
        print(f"  url     : {info.url}")
        print(f"  thumb   : {info.thumburl}")
        print(f"  {info.width}x{info.height}, {info.size} bytes, {info.mime}")
        print(f"  licence : {info.license}")
        print(f"  artist  : {info.artist}")
        print(f"  desc    : {info.description[:120]}")

    print("\n== one-liner: direct URL of the first hit ==")
    print(f"  {wiki.image_url(hits[0].name)}")

    print("\n== a random file, just for fun ==")
    for r in wiki.random_file(limit=1):
        print(f"  {r.name}")


if __name__ == "__main__":
    main()