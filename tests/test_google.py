from bs4 import BeautifulSoup

from netgo.search.google import _parse_results

SERP_HTML = """
<html><body>
<div class="g">
  <div class="tF2Cxc">
    <a href="/url?q=https%3A%2F%2Fwww.example.org%2Fpage%3Fa%3D1%26b%3D2&amp;sa=U&amp;ved=2ahUKEw">
      <h3 class="LC20lb">Example Page</h3>
    </a>
    <div class="VwiC3b">This is a short snippet about the page.</div>
  </div>
</div>
<div class="g">
  <div class="tF2Cxc">
    <a href="/url?q=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FPython">
      <h3>Python - Wikipedia</h3>
    </a>
    <div class="VwiC3b">Python is an interpreted language.</div>
  </div>
</div>
</body></html>
"""


def test_parse_results_extracts_links():
    soup = BeautifulSoup(SERP_HTML, "html.parser")
    results = _parse_results(soup)

    assert len(results) == 2
    assert results[0].url == "https://www.example.org/page?a=1&b=2"
    assert results[0].title == "Example Page"
    assert results[0].snippet == "This is a short snippet about the page."
    assert results[0].position == 1
    assert results[1].position == 2


def test_parse_results_skips_non_http_links_and_google_links():
    html = """
    <a href="/url?q=/intl/en/about.html">google about</a>
    <a href="/url?q=javascript%3Avoid(0)">bad</a>
    <a href="https://google.com/maps">map</a>
    """
    soup = BeautifulSoup(html, "html.parser")
    assert _parse_results(soup) == []