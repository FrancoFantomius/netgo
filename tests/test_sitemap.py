import gzip
import requests

from netgo.sitemap import (
    Sitemap,
    SitemapEntry,
    SitemapFetchError,
    SitemapParseError,
    crawl,
    discover,
    filter_by_prefix,
    load,
    parse,
)

URLSET = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    "<url><loc>/</loc><lastmod>2026-01-01</lastmod>"
    "<changefreq>daily</changefreq><priority>1.0</priority></url>"
    "<url><loc>/about</loc></url>"
    "</urlset>"
)

INDEX = (
    '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    "<sitemap><loc>/posts/sitemap.xml</loc></sitemap>"
    "<sitemap><loc>https://cdn.example.com/static/sitemap.xml</loc></sitemap>"
    "</sitemapindex>"
)


class _FakeResponse:
    def __init__(self, content, url, status=200):
        self.content = content.encode("utf-8") if isinstance(content, str) else content
        self.text = self.content.decode("utf-8", errors="replace")
        self.url = url
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)


class _FakeSession:
    def __init__(self, content, url="https://example.org/sitemap.xml", status=200):
        self.response = _FakeResponse(content, url, status)
        self.last_url = None

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        self.response.raise_for_status()
        return self.response


def test_parse_urlset():
    sm = parse(URLSET, base_url="https://example.org/sitemap.xml")
    assert isinstance(sm, Sitemap)
    assert sm.kind == "urlset"
    assert sm.urls == ["https://example.org/", "https://example.org/about"]
    first = sm.entries[0]
    assert isinstance(first, SitemapEntry)
    assert first.lastmod == "2026-01-01"
    assert first.changefreq == "daily"
    assert first.priority == 1.0
    assert sm.entries[1].priority == 0.0


def test_parse_resolves_protocol_relative():
    xl = '<urlset><url><loc>//cdn.example.com/x</loc></url></urlset>'
    sm = parse(xl, base_url="https://example.org/sitemap.xml")
    assert sm.urls == ["https://cdn.example.com/x"]


def test_parse_urlset_absolute_locs_unchanged():
    xl = '<urlset><url><loc>https://other.org/page</loc></url></urlset>'
    sm = parse(xl, base_url="https://example.org/sitemap.xml")
    assert sm.urls == ["https://other.org/page"]


def test_parse_index():
    sm = parse(INDEX, base_url="https://example.org/sitemap.xml")
    assert sm.kind == "sitemapindex"
    assert sm.entries == []
    assert sm.children == [
        "https://example.org/posts/sitemap.xml",
        "https://cdn.example.com/static/sitemap.xml",
    ]
    assert not sm.urls


def test_parse_plain_text():
    body = "# a comment\n\nhttps://example.org/\nhttps://example.org/about\n"
    sm = parse(body, base_url="")
    assert sm.kind == "text"
    assert sm.urls == ["https://example.org/", "https://example.org/about"]


def test_parse_accepts_bytes():
    sm = parse(URLSET.encode("utf-8"), base_url="https://example.org/sitemap.xml")
    assert sm.urls == ["https://example.org/", "https://example.org/about"]


def test_parse_raises_on_empty():
    for empty in ("", "   ", b""):
        try:
            parse(empty)
        except SitemapParseError:
            pass
        else:
            raise AssertionError("expected SitemapParseError")


def test_parse_raises_on_malformed_xml():
    try:
        parse("<urlset><url><loc>broken", base_url="https://x.org")
    except SitemapParseError:
        pass
    else:
        raise AssertionError("expected SitemapParseError")


def test_parse_raises_on_unknown_root():
    try:
        parse("<feed><entry>one</entry></feed>", base_url="https://x.org")
    except SitemapParseError:
        pass
    else:
        raise AssertionError("expected SitemapParseError")


def test_parse_raises_on_empty_text():
    try:
        parse("   \n\n  ", base_url="https://x.org")
    except SitemapParseError:
        pass
    else:
        raise AssertionError("expected SitemapParseError")


def test_load_returns_sitemap_with_final_url():
    sm = load("https://example.org/start.xml", session=_FakeSession(URLSET))
    assert sm.url == "https://example.org/sitemap.xml"
    assert sm.urls == ["https://example.org/", "https://example.org/about"]


def test_load_gunzips_bare_gzip_body():
    payload = gzip.compress(URLSET.encode("utf-8"))
    session = _FakeSession(payload, url="https://example.org/sitemap.xml.gz")
    sm = load("https://example.org/sitemap.xml.gz", session=session)
    assert sm.kind == "urlset"
    assert sm.urls == ["https://example.org/", "https://example.org/about"]


def test_load_raises_on_http_error():
    session = _FakeSession("forbidden", url="https://example.org/x", status=403)
    try:
        load("https://example.org/x", session=session)
    except SitemapFetchError as exc:
        assert exc.status == 403
    else:
        raise AssertionError("expected SitemapFetchError")


def test_load_raises_on_non_sitemap_body():
    session = _FakeSession("<html><body>hello</body></html>", url="https://example.org/x")
    try:
        load("https://example.org/x", session=session)
    except SitemapParseError:
        pass
    else:
        raise AssertionError("expected SitemapParseError")


class _RobotsSession:
    def __init__(self, robots_body, status=200):
        self.response = _FakeResponse(robots_body, url="https://example.org/robots.txt", status=status)
        self.last_url = None

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        self.response.raise_for_status()
        return self.response


def test_discover_reads_robots_txt():
    robots = (
        "User-agent: *\n"
        "Disallow: /private/\n"
        "Sitemap: https://example.org/sitemap.xml\n"
        "Sitemap: https://example.org/sitemap-index.xml\n"
    )
    session = _RobotsSession(robots)
    urls = discover("https://example.org/any/path", session=session)
    assert session.last_url == "https://example.org/robots.txt"
    assert urls == [
        "https://example.org/sitemap.xml",
        "https://example.org/sitemap-index.xml",
    ]


def test_discover_accepts_bare_domain():
    session = _RobotsSession("Sitemap: https://example.org/sitemap.xml\n")
    urls = discover("example.org", session=session)
    assert session.last_url == "https://example.org/robots.txt"
    assert urls == ["https://example.org/sitemap.xml"]


def test_discover_returns_empty_on_missing_robots():
    session = _RobotsSession("nope", status=404)
    assert discover("https://example.org", session=session) == []


def test_discover_returns_empty_when_no_sitemap_lines():
    session = _RobotsSession("User-agent: *\nDisallow: /\n")
    assert discover("https://example.org", session=session) == []


def test_discover_is_case_insensitive():
    session = _RobotsSession("sitemap:  https://example.org/sitemap.xml\n")
    assert discover("https://example.org", session=session) == [
        "https://example.org/sitemap.xml"
    ]


class _TreeSession:
    """Returns a different body for each requested URL."""

    def __init__(self):
        self.bodies = {}
        self.last_url = None

    def get(self, url, headers=None, timeout=None):
        self.last_url = url
        body, final = self.bodies[url]
        return _FakeResponse(body, url=final or url)


def test_crawl_follows_index_tree_and_dedupes():
    session = _TreeSession()
    session.bodies = {
        "https://example.org/sitemap.xml": (
            '<sitemapindex><sitemap><loc>https://example.org/a.xml</loc></sitemap>'
            "<sitemap><loc>https://example.org/b.xml</loc></sitemap></sitemapindex>",
            None,
        ),
        "https://example.org/a.xml": (
            '<urlset><url><loc>https://example.org/a1</loc></url>'
            "<url><loc>https://example.org/a2</loc></url></urlset>",
            None,
        ),
        "https://example.org/b.xml": (
            '<urlset><url><loc>https://example.org/a2</loc></url>'
            "<url><loc>https://example.org/b1</loc></url></urlset>",
            None,
        ),
    }
    urls = crawl("https://example.org/sitemap.xml", session=session)
    assert [e.loc for e in urls] == [
        "https://example.org/a1",
        "https://example.org/a2",
        "https://example.org/b1",
    ]
    assert session.last_url == "https://example.org/b.xml"


def test_sitemap_iteration_and_boolean():
    sm = parse(URLSET, base_url="https://example.org/sitemap.xml")
    assert len(sm) == 2
    assert [e.loc for e in sm] == sm.urls
    assert bool(sm)
    assert str(sm) == "https://example.org/sitemap.xml"

    empty = parse(INDEX, base_url="https://example.org/sitemap.xml")
    assert not bool(empty.entries)


def test_sitemap_by_prefix_filters_entries():
    xl = (
        '<urlset><url><loc>https://example.org/page_1</loc></url>'
        "<url><loc>https://example.org/page_2</loc></url>"
        "<url><loc>https://example.org/about</loc></url></urlset>"
    )
    sm = parse(xl, base_url="https://example.org/sitemap.xml")
    pages = sm.by_prefix("https://example.org/page_")
    assert [e.loc for e in pages] == [
        "https://example.org/page_1",
        "https://example.org/page_2",
    ]
    assert sm.by_prefix("https://example.org/missing") == []


def test_filter_by_prefix_crawls_tree_and_filters():
    session = _TreeSession()
    session.bodies = {
        "https://example.org/sitemap.xml": (
            '<sitemapindex><sitemap><loc>https://example.org/a.xml</loc></sitemap>'
            "<sitemap><loc>https://example.org/b.xml</loc></sitemap></sitemapindex>",
            None,
        ),
        "https://example.org/a.xml": (
            '<urlset><url><loc>https://example.org/page_1</loc></url>'
            "<url><loc>https://example.org/about</loc></url></urlset>",
            None,
        ),
        "https://example.org/b.xml": (
            '<urlset><url><loc>https://example.org/page_2</loc></url>'
            "<url><loc>https://example.org/page_3</loc></url></urlset>",
            None,
        ),
    }
    pages = filter_by_prefix(
        "https://example.org/sitemap.xml", "https://example.org/page_", session=session
    )
    assert [e.loc for e in pages] == [
        "https://example.org/page_1",
        "https://example.org/page_2",
        "https://example.org/page_3",
    ]
    assert filter_by_prefix(
        "https://example.org/sitemap.xml", "https://example.org/nope", session=session
    ) == []
