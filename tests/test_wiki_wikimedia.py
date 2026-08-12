from netgo.wiki import WikiClient, WikiNotFoundError
from netgo.wiki.wikimedia import file_info, image_url, random_file, search_images

from conftest import FakeSession


def _client(payload):
    return WikiClient(host="wikimedia", session=FakeSession(payload))


def test_search_images_parses():
    payload = {
        "query": {"search": [{"title": "File:Sunflower.jpg"}, {"ns": 6, "title": "File:Cat.png"}]}
    }
    hits = search_images("sunflower", client=_client(payload))
    assert hits[0].name == "File:Sunflower.jpg"
    assert hits[1].name == "File:Cat.png"


def test_file_info_parses_metadata():
    payload = {
        "query": {
            "pages": {
                "1": {
                    "title": "File:Earth.jpg",
                    "imageinfo": [
                        {
                            "url": "https://upload.wikimedia.org/.../Earth.jpg",
                            "thumburl": "https://upload.wikimedia.org/.../320px-Earth.jpg",
                            "size": 10000,
                            "width": 800,
                            "height": 600,
                            "mime": "image/jpeg",
                            "extmetadata": {
                                "ImageDescription": {"value": "<b>Planet</b> Earth"},
                                "LicenseShortName": {"value": "Public domain"},
                                "Artist": {"value": '<a href="/u/Nasa">NASA</a>'},
                            },
                        }
                    ],
                }
            }
        }
    }
    f = file_info("File:Earth.jpg", client=_client(payload))
    assert f.name == "File:Earth.jpg"
    assert f.mime == "image/jpeg"
    assert f.width == 800
    assert f.thumburl.startswith("https://")
    assert f.license == "Public domain"
    assert f.description == "Planet Earth"
    assert f.artist == "NASA"
    assert str(f) == "File:Earth.jpg"


def test_file_info_raises_on_missing():
    payload = {"query": {"pages": {"-1": {"title": "File:Gone.jpg", "missing": ""}}}}
    try:
        file_info("File:Gone.jpg", client=_client(payload))
    except WikiNotFoundError:
        pass
    else:
        raise AssertionError("expected WikiNotFoundError")


def test_image_url_returns_direct_link():
    payload = {
        "query": {
            "pages": {
                "1": {
                    "title": "File:Earth.jpg",
                    "imageinfo": [{"url": "https://upload.wikimedia.org/.../Earth.jpg"}],
                }
            }
        }
    }
    assert image_url("File:Earth.jpg", client=_client(payload)) == (
        "https://upload.wikimedia.org/.../Earth.jpg"
    )


def test_random_file_parses():
    payload = {"query": {"random": [{"ns": 6, "title": "File:Random.jpg"}]}}
    files = random_file(client=_client(payload))
    assert files[0].name == "File:Random.jpg"