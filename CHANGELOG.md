# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-08-15

### Fixed
- Fixed URL substring sanitization and hostname validation in Google and Bing search parsers (`netgo.search.google`, `netgo.search.bing`) to prevent partial host match vulnerabilities.
- Added explicit workflow permissions in GitHub Actions CI pipelines.

### Added
- Repository cleanup utility script (`scripts/clean_ignored.py`) with npm `clean` script integration and unit tests (`tests/test_clean_ignored.py`).
- Automated multi-platform and Python version matrix testing with code coverage reporting in CI.
- Comprehensive usage examples and documentation pages for search, Wikipedia, Wikidata, Wikimedia Commons, Wiktionary, page parsing, and sitemaps.

## [0.4.0] - 2026-08-13

### Added
- `netgo.sitemap` subpackage for XML sitemaps (`netgo.sitemap`).
- `parse` that reads URL sets, sitemap indexes and plain-text sitemaps,
  namespace-agnostic, resolving relative locations against a base URL
  (`netgo.sitemap.parse`).
- `load` that fetches a sitemap URL (plain or gzip-compressed) and parses
  it, `discover` that finds the `Sitemap:` URLs a site declares in its
  `robots.txt`, and `crawl` that follows a sitemap index recursively to
  collect every page URL (`netgo.sitemap.fetch`).
- `filter_by_prefix` that crawls a whole sitemap tree and keeps only the
  page URLs that start with a given prefix, plus `Sitemap.by_prefix` to
  filter a single parsed sitemap (`netgo.sitemap.fetch`,
  `netgo.sitemap.models`).
- `SitemapError`, `SitemapFetchError` and `SitemapParseError` exceptions
  (`netgo.sitemap.errors`).
- `Sitemap` and `SitemapEntry` dataclass models (`netgo.sitemap.models`).
- `Page.raw` carrying the untouched HTML exactly as the server sent it
  (`netgo.page.models`).
- Offline fixture-based test suite (`tests/test_sitemap.py`).
- Generated API documentation for the new modules (`docs/netgo.sitemap*.md`).
- README "Sitemaps" section and a runnable example
  (`examples/09_sitemap.py`).

## [0.3.0] - 2026-08-12

### Added
- `netgo.page` subpackage that fetches any web page and reduces it to its
  main content, skipping the site template (`netgo.page`).
- `netgo.fetch` top-level entry point returning a `Page` with the extracted
  title, domain, cleaned plain-text body (`text`, `paragraphs`) and content
  HTML.
- Readability-style extractor (`netgo.page.extract`): drops template chrome
  (nav, headers, footers, sidebars, banners, comment widgets, cookie
  consent), scores the remaining containers by prose and keeps the article.
- `PageError`, `PageFetchError` and `PageParseError` exceptions
  (`netgo.page.errors`).
- `Page` dataclass model (`netgo.page.models`).
- Offline fixture-based test suite (`tests/test_page.py`).
- Generated API documentation for the new modules (`docs/netgo.page*.md`).
- README "Viewing a page" section with examples.

## [0.2.0] - 2026-08-12

### Added
- `netgo.wiki` subpackage wrapping the MediaWiki Action API behind one shared
  `WikiClient` session (`netgo.wiki.client`).
- Wikipedia core (`netgo.wiki.core`): full-text `search`, `summary`,
  `paragraphs`, `sections`, `links`, `backlinks`, `categories`, `images`,
  `pageinfo`, aggregated `page`, `random` and `geo_search`, plus parallel
  `search_many`.
- Wikidata (`netgo.wiki.wikidata`): `wikidata_id` (title→QID), `entity`,
  label `search`, `claims`, `labels`, `aliases` and `sitelinks`.
- Wikimedia Commons (`netgo.wiki.wikimedia`): `search_images`, `file_info`
  with thumbnails and licensing metadata, `image_url` and `random_file`.
- Wiktionary (`netgo.wiki.wiktionary`): `definition`, `etymology`,
  `languages` and prefix `search`.
- `WikiError`, `WikiAPIError` and `WikiNotFoundError` exceptions
  (`netgo.wiki.errors`).
- Dataclass models for every response (`netgo.wiki.models`): `WikiResult`,
  `Article`, `Section`, `Link`, `Category`, `Image`, `GeoResult`, `Item`,
  `Claim`, `MediaFile` and `Entry`.
- Multi-language support: every wrapper accepts `lang=`, plus `timeout`,
  `delay` and a reusable `session`/`client`.
- Offline fixture-based test suite for all four wikis (`tests/test_wiki_*.py`).
- Generated API documentation for the new modules (`docs/netgo.wiki*.md`).
- README section with Wikipedia API examples.

## [0.1.0] - 2026-08-12

Initial release.

### Added
- `netgo.search` and `netgo.search_many` engine-agnostic entry points.
- Google backend (`netgo.search.google`) with `num`, `lang`, `start`, `safe`,
  `gbv`, `delay` and `timeout` options.
- Bing backend (`netgo.search.bing`) selectable via `engine="bing"`.
- `Result` and `SearchParams` dataclasses (`netgo.search.models`).
- `SearchError` and `SearchBlockedError` exceptions shared across backends
  (`netgo.search.errors`).
- Redirect URL decoding for Google and Bing result links.
- Parallel batch queries via `ThreadPoolExecutor`.
- Generated API documentation (`docs/`) from docstrings.
- GitHub Action (`docs.yml`) regenerates the API docs on every push to `master`.
- Test suite for both backends (`tests/`).

### Changed
- Doc generator keeps bullet lists on separate lines and drops the leading
  blank line from modules without a docstring.
- `SearchBlockedError` documentation covers both backends (Google and Bing).
- README rewritten as a broad project overview linking to the generated docs.