"""Dictionary data from Wiktionary.

Reads the part of speech, numbered definitions, etymology and the set of
languages a word exists in, for any requested Wiktionary edition.
"""

# Import Wiktionary helpers from netgo.wiki
import netgo.wiki as wiki


def main():
    word = "serendipity"

    # -------------------------------------------------------------
    # 1. Fetch structured definition entry
    # -------------------------------------------------------------
    # `wiktionary_definition(word, lang="en")`: fetches parsed dictionary entry
    entry = wiki.wiktionary_definition(word)
    print(f"== Entry: {entry.word} (Language Edition: {entry.lang}) ==")
    print(f"  Part of speech: {entry.pos or 'n/a'}")
    print("  Definitions:")
    for i, d in enumerate(entry.definitions, 1):
        print(f"    {i}. {d}")

    # -------------------------------------------------------------
    # 2. Extract word etymology
    # -------------------------------------------------------------
    # `wiki.etymology(word)`: retrieves origin and historical background
    etymology = wiki.etymology(word)
    if etymology:
        print(f"\n  Etymology: {etymology[:200]}...")

    # -------------------------------------------------------------
    # 3. Check language presence on Wiktionary
    # -------------------------------------------------------------
    # `wiki.languages(word)`: discovers all language sections defined for this entry
    langs = wiki.languages(word)
    print(f"\n  Defined in {len(langs)} language sections on en.wiktionary:")
    print(f"  {', '.join(langs[:8])}...")

    # -------------------------------------------------------------
    # 4. Search word titles with prefix matching
    # -------------------------------------------------------------
    # `wiki.wiktionary_search(prefix, limit=5)`: autocomplete/title suggestions
    prefix = word[:5]
    print(f"\n== Prefix search for {prefix!r} ==")
    for title in wiki.wiktionary_search(prefix, limit=5):
        print(f"  - {title}")

    # -------------------------------------------------------------
    # 5. Query non-English Wiktionary editions
    # -------------------------------------------------------------
    # `lang="it"`: query the Italian Wiktionary edition directly
    print("\n== Same word on Italian Wiktionary (lang='it') ==")
    it = wiki.wiktionary_definition(word, lang="it")
    print(f"  Part of speech: {it.pos or 'n/a'}")
    for d in it.definitions[:2]:
        print(f"    - {d}")


if __name__ == "__main__":
    main()