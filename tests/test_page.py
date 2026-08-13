import requests

from bs4 import BeautifulSoup

from netgo.page import (
    Page,
    PageFetchError,
    PageParseError,
    fetch,
)
from netgo.page.extract import extract_content, extract_title, render

ART_GREETING = "An apple pie is a pie in which the principal filling ingredient is apples."
ART_BODY = "Apple pie is an unofficial state pie in three US states, brought over by English and Dutch settlers."

ARTICLE_HTML = (
    "<!doctype html><html><head>"
    "<title>Apple pie - Great Recipes</title>"
    "</head><body>"
    '<nav class="main-nav"><a href="/">Home</a><a href="/recipes">Recipes</a></nav>'
    '<header class="site-header"><h1>Great Recipes</h1><span>logo</span></header>'
    '<aside class="sidebar"><a href="#">Related recipes</a></aside>'
    '<div class="cookie-banner">We use cookies to improve your experience.</div>'
    '<article class="post-content">'
    "<h1>Apple pie</h1>"
    f"<p>{ART_GREETING}</p>"
    f"<p>{ART_BODY}</p>"
    '<div class="share-buttons"><a href="#">Share this</a></div>'
    "</article>"
    '<footer class="site-footer">Copyright 2024 Great Recipes</footer>'
    "</body></html>"
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


class _FakeResponse:
    def __init__(self, text, url, content_type="text/html; charset=utf-8", status=200):
        self.text = text
        self.url = url
        self.headers = {"Content-Type": content_type}
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class _FakeSession:
    def __init__(self, html, url="https://example.org/recipes/apple-pie", status=200):
        self.response = _FakeResponse(html, url, status=status)
        self.last_url = None

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        self.response.raise_for_status()
        return self.response


def test_fetch_returns_page_with_filtered_content():
    page = fetch("https://example.org/recipes/apple-pie", session=_FakeSession(ARTICLE_HTML))
    assert page.url == "https://example.org/recipes/apple-pie"
    assert page.site == "example.org"
    assert page.title == "Apple pie"
    assert page.paragraphs[0] == "Apple pie"
    assert ART_GREETING in page.text
    assert ART_BODY in page.text
    for junk in ("Home", "Recipes", "logo", "Related recipes", "cookies", "Copyright"):
        assert junk not in page.text
    assert isinstance(page, Page)


def test_fetch_exposes_raw_html():
    page = fetch("https://example.org/recipes/apple-pie", session=_FakeSession(ARTICLE_HTML))
    assert page.raw == ARTICLE_HTML


def test_fetch_uses_redirected_url():
    session = _FakeSession(ARTICLE_HTML, url="https://example.org/actual-page")
    page = fetch("https://example.org/recipes/apple-pie", session=session)
    assert page.url == "https://example.org/actual-page"


def test_fetch_raises_on_http_error():
    session = _FakeSession("forbidden", url="https://example.org/x", status=403)
    try:
        fetch("https://example.org/x", session=session)
    except PageFetchError as exc:
        assert exc.status == 403
    else:
        raise AssertionError("expected PageFetchError")


def test_fetch_raises_on_empty_page():
    empty = (
        "<html><body>"
        '<nav><a href="/">Home</a></nav>'
        "<footer>Copyright</footer>"
        "</body></html>"
    )
    try:
        fetch("https://example.org/empty", session=_FakeSession(empty))
    except PageParseError:
        pass
    else:
        raise AssertionError("expected PageParseError")


def test_extract_strips_template():
    soup = _soup(ARTICLE_HTML)
    content = extract_content(soup)
    text, paragraphs = render(content)
    assert ART_GREETING in text
    assert ART_BODY in text
    assert paragraphs[0] == "Apple pie"
    for junk in ("Home", "Recipes", "logo", "Related recipes", "cookies", "Copyright"):
        assert junk not in text
        assert junk not in " ".join(paragraphs)


def test_extract_title_prefers_og():
    html = (
        "<html><head>"
        '<meta property="og:title" content="The Real Title">'
        "<title>Fallback Title</title>"
        "</head><body></body></html>"
    )
    assert extract_title(_soup(html)) == "The Real Title"


def test_extract_title_strips_site_suffix():
    assert extract_title(_soup(ARTICLE_HTML)) == "Apple pie"


def test_extract_title_from_h1():
    html = "<html><body><h1>Bare heading</h1><p>Some prose here.</p></body></html>"
    assert extract_title(_soup(html)) == "Bare heading"