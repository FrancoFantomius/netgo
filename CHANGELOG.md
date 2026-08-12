# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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