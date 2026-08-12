from netgo.wiki import WikiClient, WikiError, WikiNotFoundError
from netgo.wiki.wiktionary import (
    _clean,
    _parse_page,
    definition,
    etymology,
    languages,
    search,
)

from conftest import FakeSession

_WIKITEXT = """==English==

===Etymology===
From {{der|en|la|serenus}} + suffix.

===Noun===
{{en-noun}}
# The faculty of making fortunate discoveries by accident.
#* {{quote-book|en|Sometimes}} it strikes us.

===Derived terms===
* serendipitous

==Italian==

===Noun===
# fortuna inaspettata
"""


def _client(payload):
    return WikiClient(lang="en", host="wiktionary", session=FakeSession(payload))


def test_clean_strips_templates_links_and_bold():
    line = "From {{der|en|la|serenus}} + ''calme'' [[here|there]]."
    assert _clean(line) == "From + calme there."


def test_parse_page_extracts_pos_definitions_and_etymology():
    pos, defs, etym = _parse_page(_WIKITEXT, "English")
    assert pos == "Noun"
    assert defs == ["The faculty of making fortunate discoveries by accident."]
    assert etym[0].startswith("From")


def test_parse_page_targets_language_section():
    pos, defs, _ = _parse_page(_WIKITEXT, "Italian")
    assert pos == "Noun"
    assert defs == ["fortuna inaspettata"]


def test_definition_parses_entry():
    payload = {"parse": {"wikitext": {"*": _WIKITEXT}}}
    e = definition("serendipity", client=_client(payload))
    assert e.word == "serendipity"
    assert e.pos == "Noun"
    assert "fortunate" in e.definitions[0]


def test_definition_raises_when_language_section_missing():
    payload = {"parse": {"wikitext": {"*": _WIKITEXT}}}
    try:
        definition("serendipity", lang="xx", client=_client(payload))
    except WikiNotFoundError:
        pass
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_definition_raises_wiki_error_on_missing_word():
    payload = {"error": {"code": "missingtitle", "info": "no page"}}
    raised = False
    try:
        definition("zzzzzz", client=_client(payload))
    except WikiError:
        raised = True
    assert raised


def test_etymology_extracts_text():
    payload = {"parse": {"wikitext": {"*": _WIKITEXT}}}
    text = etymology("serendipity", client=_client(payload))
    assert text.startswith("From")


def test_languages_from_sections():
    payload = {
        "parse": {
            "sections": [
                {"level": "1", "index": "1", "line": "English"},
                {"level": "2", "index": "2", "line": "English"},
                {"level": "2", "index": "3", "line": "Italian"},
            ]
        }
    }
    langs = languages("serendipity", client=_client(payload))
    assert langs == ["English", "Italian"]


def test_search_uses_prefix_match():
    payload = {"query": {"prefixsearch": [{"title": "serendipity"}, {"title": "serendipitous"}]}}
    out = search("seren", client=_client(payload))
    assert "serendipity" in out
    assert "serendipitous" in out