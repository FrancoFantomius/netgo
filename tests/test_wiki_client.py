from netgo.wiki import WikiClient, WikiNotFoundError
from netgo.wiki.client import default_client
from netgo.wiki.errors import WikiAPIError

from conftest import FakeSession


def _client(payload):
    return WikiClient(session=FakeSession(payload))


def test_base_url_for_each_host():
    assert WikiClient(lang="de", host="wikipedia").base_url == (
        "https://de.wikipedia.org/w/api.php"
    )
    assert WikiClient(host="wikidata").base_url == "https://www.wikidata.org/w/api.php"
    assert WikiClient(host="wikimedia").base_url == (
        "https://commons.wikimedia.org/w/api.php"
    )
    assert WikiClient(lang="it", host="wiktionary").base_url == (
        "https://it.wiktionary.org/w/api.php"
    )


def test_unknown_host_raises_value_error():
    try:
        WikiClient(host="nope").base_url
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_default_client_points_at_wikipedia():
    c = default_client("fr", delay=0.2)
    assert c.base_url == "https://fr.wikipedia.org/w/api.php"
    assert c.delay == 0.2


def test_api_call_adds_format_json():
    payload = {"query": {"pages": {"1": {"title": "A"}}}}
    session = FakeSession(payload)
    client = WikiClient(session=session)
    out = client.api_call({"action": "query", "titles": "A"})
    assert out is payload
    assert session.last_params["format"] == "json"
    assert session.last_params["titles"] == "A"


def test_api_call_raises_on_api_error_object():
    payload = {"error": {"code": "badvalue", "info": "nope"}}
    client = _client(payload)
    try:
        client.api_call({"action": "query"})
    except WikiAPIError as exc:
        assert exc.code == "badvalue"
        assert exc.info == "nope"
    else:
        raise AssertionError("expected WikiAPIError")


def test_api_call_raises_on_missing_page():
    payload = {"query": {"pages": {"-1": {"title": "Missing", "missing": ""}}}}
    client = _client(payload)
    try:
        client.api_call({"action": "query", "titles": "Missing"})
    except WikiNotFoundError as exc:
        assert exc.subject == "Missing"
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_api_call_ignore_missing_returns_payload():
    payload = {"query": {"pages": {"-1": {"title": "Gone", "missing": ""}}}}
    client = _client(payload)
    out = client.api_call({"action": "query"}, ignore_missing=True)
    assert out == payload


def test_api_call_raises_on_http_error():
    client = WikiClient(session=FakeSession(http_error=__import__("requests").HTTPError("500")))
    try:
        client.api_call({"action": "query"})
    except WikiAPIError as exc:
        assert "500" in str(exc)
    else:
        raise AssertionError("expected WikiAPIError")


def test_api_call_raises_on_non_json_body():
    client = WikiClient(session=FakeSession(non_json=True))
    try:
        client.api_call({"action": "query"})
    except WikiAPIError as exc:
        assert exc.status == 200
    else:
        raise AssertionError("expected WikiAPIError")