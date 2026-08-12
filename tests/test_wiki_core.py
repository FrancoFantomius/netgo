from netgo.wiki import WikiClient, WikiNotFoundError
from netgo.wiki.core import (
    backlinks,
    categories,
    geo_search,
    images,
    links,
    page,
    pageinfo,
    paragraphs,
    random,
    search,
    sections,
    summary,
)

from conftest import FakeSession


def _client(payload):
    return WikiClient(session=FakeSession(payload))


def test_search_parses_hits():
    payload = {
        "query": {
            "search": [
                {
                    "title": "Machine learning",
                    "pageid": 42,
                    "snippet": "a subset of AI",
                    "wordcount": 100,
                    "size": 2000,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "ns": 0,
                },
                {"title": "History of ML", "pageid": 43, "ns": 0},
            ]
        }
    }
    hits = search("machine learning", client=_client(payload))
    assert hits[0].title == "Machine learning"
    assert hits[0].pageid == 42
    assert hits[0].snippet == "a subset of AI"
    assert hits[0].wordcount == 100
    assert hits[1].title == "History of ML"


def test_summary_returns_extract():
    payload = {
        "query": {"pages": {"1": {"title": "Bread", "pageid": 1, "extract": "Bread is a food."}}}
    }
    assert summary("Bread", client=_client(payload)) == "Bread is a food."


def test_summary_raises_on_missing_page():
    payload = {"query": {"pages": {"-1": {"title": "Nope", "missing": ""}}}}
    try:
        summary("Nope", client=_client(payload))
    except WikiNotFoundError:
        pass
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_paragraphs_splits_on_blank_lines():
    payload = {
        "query": {
            "pages": {
                "1": {
                    "title": "Bread",
                    "extract": "Bread is a staple food.\n\nIt is baked.",
                }
            }
        }
    }
    pars = paragraphs("Bread", client=_client(payload))
    assert pars == ["Bread is a staple food.", "It is baked."]


def test_sections_parses_outline():
    payload = {
        "parse": {
            "sections": [
                {"index": "1", "line": "History", "level": "2"},
                {"index": "2", "line": "Recipes", "level": "3"},
            ]
        }
    }
    out = sections("Bread", client=_client(payload))
    assert out[0].title == "History"
    assert out[0].index == "1"
    assert out[0].level == 2
    assert out[1].level == 3


def test_links_and_backlinks():
    link_payload = {"query": {"pages": {"1": {"title": "Bread", "links": [{"ns": 0, "title": "Flour"}]}}}}
    assert links("Bread", client=_client(link_payload))[0].title == "Flour"

    bl_payload = {"query": {"backlinks": [{"ns": 0, "title": "Sourdough"}]}}
    assert backlinks("Bread", client=_client(bl_payload))[0].title == "Sourdough"


def test_categories_parses():
    payload = {
        "query": {
            "pages": {
                "1": {
                    "title": "Bread",
                    "categories": [{"ns": 14, "title": "Category:Breads"}],
                }
            }
        }
    }
    cats = categories("Bread", client=_client(payload))
    assert cats[0].title == "Category:Breads"
    assert cats[0].ns == 14


def test_images_parses():
    payload = {
        "query": {
            "pages": {"1": {"title": "Bread", "images": [{"title": "File:Bread.jpg"}]}}
        }
    }
    assert images("Bread", client=_client(payload))[0].title == "File:Bread.jpg"


def test_pageinfo_parses():
    payload = {
        "query": {
            "pages": {
                "1": {"title": "Bread", "pageid": 5, "fullurl": "https://en.wikipedia.org/wiki/Bread"}
            }
        }
    }
    info = pageinfo("Bread", client=_client(payload))
    assert info["fullurl"].endswith("/Bread")


def test_page_aggregates_single_call():
    payload = {
        "query": {
            "pages": {
                "1": {
                    "title": "Bread",
                    "pageid": 5,
                    "extract": "Bread is a staple.",
                    "sections": [{"index": "1", "line": "History", "level": "2"}],
                    "categories": [{"ns": 14, "title": "Category:Breads"}],
                    "links": [{"ns": 0, "title": "Flour"}],
                    "images": [{"title": "File:Bread.jpg"}],
                    "fullurl": "https://en.wikipedia.org/wiki/Bread",
                }
            }
        }
    }
    art = page("Bread", client=_client(payload))
    assert art.title == "Bread"
    assert art.summary == "Bread is a staple."
    assert art.sections[0].title == "History"
    assert art.categories[0].title == "Category:Breads"
    assert art.links[0].title == "Flour"
    assert art.images[0].title == "File:Bread.jpg"
    assert str(art).endswith("/Bread")


def test_random_parses():
    payload = {"query": {"random": [{"id": 7, "ns": 0, "title": "Serendipity"}]}}
    hits = random(client=_client(payload))
    assert hits[0].title == "Serendipity"
    assert hits[0].pageid == 7


def test_geo_search_parses():
    payload = {
        "query": {
            "geosearch": [
                {"pageid": 1, "ns": 0, "title": "Rome", "lat": 41.89, "lon": 12.49, "dist": 100}
            ]
        }
    }
    hits = geo_search(41.89, 12.49, client=_client(payload))
    assert hits[0].title == "Rome"
    assert hits[0].dist == 100