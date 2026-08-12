from netgo.wiki import WikiClient, WikiNotFoundError
from netgo.wiki.wikidata import (
    aliases,
    claims,
    entity,
    labels,
    search,
    sitelinks,
    _claim_value,
    _parse_claims,
    wikidata_id,
)

from conftest import FakeSession


def _client(payload):
    return WikiClient(host="wikidata", session=FakeSession(payload))


def _wiki_client(payload):
    return WikiClient(session=FakeSession(payload))


def test_claim_value_mapping():
    assert _claim_value({"snaktype": "value", "datavalue": {"value": "Q5"}}) == "Q5"
    assert _claim_value({"snaktype": "value", "datavalue": {"value": "text"}}) == "text"
    assert _claim_value({"snaktype": "novalue"}) is None
    assert _claim_value({"snaktype": "value", "datavalue": {"value": {"amount": "+2"}}}) == "+2"


def test_parse_claims_with_qualifiers():
    raw = {
        "P31": [
            {
                "mainsnak": {
                    "snaktype": "value",
                    "datatype": "wikibase-item",
                    "datavalue": {"value": {"entity-type": "item", "numeric-id": 5}},
                },
                "qualifiers": {"P580": [{"snaktype": "value", "datavalue": {"value": "2020"}}]},
            }
        ]
    }
    out = _parse_claims(raw)
    assert out["P31"][0].value == "Q5"
    assert out["P31"][0].datatype == "wikibase-item"
    assert out["P31"][0].qualifiers["P580"] == ["2020"]


def test_wikidata_id_resolves_qid():
    payload = {
        "query": {"pages": {"1": {"title": "Python (programming language)", "pageprops": {"wikibase_item": "Q28865"}}}}
    }
    assert wikidata_id("Python (programming language)", client=_wiki_client(payload)) == "Q28865"


def test_wikidata_id_raises_when_absent():
    payload = {"query": {"pages": {"1": {"title": "X"}}}}
    try:
        wikidata_id("X", client=_wiki_client(payload))
    except WikiNotFoundError:
        pass
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_entity_parses_full_item():
    payload = {
        "entities": {
            "Q2": {
                "labels": {"en": {"value": "Earth"}, "it": {"value": "Terra"}},
                "descriptions": {"en": {"value": "third planet from the Sun"}},
                "aliases": {"en": [{"value": "the World"}]},
                "claims": {
                    "P31": [
                        {
                            "mainsnak": {
                                "snaktype": "value",
                                "datatype": "wikibase-item",
                                "datavalue": {"value": {"entity-type": "item", "numeric-id": 5}},
                            }
                        }
                    ]
                },
                "sitelinks": {"enwiki": {"title": "Earth"}},
            }
        }
    }
    item = entity("Q2", client=_client(payload))
    assert item.labels["en"] == "Earth"
    assert item.labels["it"] == "Terra"
    assert item.aliases["en"] == ["the World"]
    assert item.claims["P31"][0].value == "Q5"
    assert item.sitelinks["enwiki"] == "Earth"
    assert str(item) == "Q2"


def test_entity_raises_when_missing():
    payload = {"entities": {}}
    try:
        entity("Q999999", client=_client(payload))
    except WikiNotFoundError:
        pass
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_search_parses_hits():
    payload = {
        "search": [{"id": "Q5463", "label": "Mount Everest", "description": "mountain"}]
    }
    hits = search("Mount Everest", client=_client(payload))
    assert hits[0].qid == "Q5463"
    assert hits[0].labels["en"] == "Mount Everest"
    assert hits[0].descriptions["en"] == "mountain"


def test_claims_parses_flat_claims():
    payload = {
        "claims": {
            "P31": [
                {
                    "mainsnak": {
                        "snaktype": "value",
                        "datatype": "wikibase-item",
                        "datavalue": {"value": {"entity-type": "item", "numeric-id": 5}},
                    }
                }
            ]
        }
    }
    out = claims("Q2", client=_client(payload))
    assert out["P31"][0].value == "Q5"


def test_labels_aliases_sitelinks():
    label_payload = {
        "entities": {"Q2": {"labels": {"en": {"value": "Earth"}, "it": {"value": "Terra"}}}}
    }
    assert labels("Q2", client=_client(label_payload))["en"] == "Earth"

    alias_payload = {
        "entities": {"Q2": {"aliases": {"en": [{"value": "the World"}]}}}
    }
    assert aliases("Q2", client=_client(alias_payload))["en"] == ["the World"]

    link_payload = {"entities": {"Q2": {"sitelinks": {"enwiki": {"title": "Earth"}}}}}
    assert sitelinks("Q2", client=_client(link_payload))["enwiki"] == "Earth"