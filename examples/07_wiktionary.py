"""Dictionary data from Wiktionary.

Reads the part of speech, numbered definitions, etymology and the set of
languages a word exists in, for any requested Wiktionary edition.
"""

import netgo.wiki as wiki


def main():
    word = "serendipity"

    entry = wiki.wiktionary_definition(word)
    print(f"== {entry.word} ({entry.lang}) ==")
    print(f"  part of speech: {entry.pos or 'n/a'}")
    print("  definitions:")
    for i, d in enumerate(entry.definitions, 1):
        print(f"    {i}. {d}")

    etymology = wiki.etymology(word)
    if etymology:
        print(f"\n  etymology: {etymology[:200]}...")

    langs = wiki.languages(word)
    print(f"\n  exists in {len(langs)} languages on en.wiktionary: {langs}")

    print(f"\n== prefix search for {word[:5]!r} ==")
    for title in wiki.wiktionary_search(word[:5], limit=5):
        print(f"  - {title}")

    print("\n== same word on the Italian edition ==")
    it = wiki.wiktionary_definition(word, lang="it")
    print(f"  pos: {it.pos or 'n/a'}")
    for d in it.definitions[:2]:
        print(f"    - {d}")


if __name__ == "__main__":
    main()