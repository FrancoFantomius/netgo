from bs4 import BeautifulSoup

from netgo.search.bing import _decode_bing_url, _parse_results

# base64url("https://www.python.org/") prefixed with a1
_CK_A = (
    "https://www.bing.com/ck/a?!&&p=deadbeef&ptn=3&ver=2&hsh=4&fclid=1"
    "&u=a1aHR0cHM6Ly93d3cucHl0aG9uLm9yZy8&ntb=1"
)

SERP_HTML = f"""
<ol id="b_results">
  <li class="b_algo">
    <h2><a href="{_CK_A}"><strong>Welcome to Python</strong>.org</a></h2>
    <div class="b_caption"><p>The mission of the Python Software Foundation.</p></div>
  </li>
  <li class="b_algo">
    <h2><a href="https://w3schools.com/python/">Python Tutorial - W3Schools</a></h2>
    <div class="b_caption"><p>Python is a popular programming language.</p></div>
  </li>
  <li class="b_algo">
    <h2><a href="https://www.bing.com/ck/a?!&&p=nou&ptn=3">Undecodable</a></h2>
  </li>
</ol>
"""


def test_decode_bing_url_ck_a_redirect():
    assert _decode_bing_url(_CK_A) == "https://www.python.org/"


def test_decode_bing_url_without_a1_prefix():
    # u=<base64url> without the a1 marker still decodes
    url = "https://www.bing.com/ck/a?foo=1&u=aHR0cHM6Ly9leGFtcGxlLm9yZy94"
    assert _decode_bing_url(url) == "https://example.org/x"


def test_decode_bing_url_direct_link():
    assert _decode_bing_url("https://example.org/x") == "https://example.org/x"
    assert _decode_bing_url("https://www.bing.com/search?q=x") is None
    assert _decode_bing_url("https://cc.bingj.com/cache.aspx?q=x") is None
    assert _decode_bing_url("/relative") is None


def test_decode_bing_url_avoids_partial_substring_matches():
    # External sites containing 'bing.com' in query or path should be returned as direct links
    url_with_query = "https://evil.com/page?ref=bing.com/ck/a"
    assert _decode_bing_url(url_with_query) == url_with_query

    # Sites with bing.com or bingj.com as a substring in hostname should be treated as external
    subdomain_attack = "https://evil-bing.com/article"
    assert _decode_bing_url(subdomain_attack) == subdomain_attack


def test_parse_results_extracts_bing_cards():
    soup = BeautifulSoup(SERP_HTML, "html.parser")
    results = _parse_results(soup)

    assert len(results) == 2
    assert results[0].url == "https://www.python.org/"
    assert "Python" in results[0].title
    assert results[0].snippet.startswith("The mission")
    assert results[0].position == 1
    assert results[1].url == "https://w3schools.com/python/"
    assert results[1].position == 2