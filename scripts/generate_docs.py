"""Generate markdown API documentation and examples from netgo's codebase.

Run from the repository root:

    python scripts/generate_docs.py

This walks the ``netgo`` package with :func:`inspect`, extracts module,
class and function docstrings, and writes markdown documentation files
into ``docs/``, generates a comprehensive ``docs/examples.md`` page,
and produces an introductory ``docs/index.md``.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import re
import sys
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "docs"
EXAMPLES_DIR = ROOT / "examples"
GITHUB_REPO_URL = "https://github.com/FrancoFantomius/netgo"
GITHUB_EXAMPLES_URL = f"{GITHUB_REPO_URL}/tree/master/examples"

# Prefer the source tree over any installed copy of netgo, so the docs are
# always generated from this checkout, no matter where the script is run from.
if ROOT not in map(Path, sys.path):
    sys.path.insert(0, str(ROOT))

import netgo


def iter_modules(package: Any):
    """Yield ``(module_name, module_object)`` for a package and its submodules."""
    yield package.__name__, package
    for info in pkgutil.walk_packages(
        package.__path__, prefix=package.__name__ + "."
    ):
        try:
            yield info.name, importlib.import_module(info.name)
        except ImportError:
            continue


def _source_rank(obj: Any) -> int:
    """Return the source line of an object so members keep their code order."""
    try:
        return inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        return 0


def _members(module: Any) -> list[tuple[str, Any]]:
    """Return functions and classes defined in the module, in source order."""
    out: list[tuple[str, Any]] = []
    for name, obj in inspect.getmembers(module):
        if name.startswith("__"):
            continue
        if not (inspect.isfunction(obj) or inspect.isclass(obj)):
            continue
        if getattr(obj, "__module__", "") != module.__name__:
            continue
        if getattr(obj, "__doc__", None) is None:
            continue
        out.append((name, obj))
    out.sort(key=lambda item: _source_rank(item[1]))
    return out


def _signature(obj: Any) -> str:
    """Render a readable signature, falling back to the object name."""
    try:
        sig = inspect.signature(obj, eval_str=True)
    except (TypeError, ValueError):
        try:
            sig = inspect.signature(obj)
        except (TypeError, ValueError):
            return ""
    return str(sig)


def _heading(text: str, level: int) -> str:
    return f"{'#' * level} {text}"


_REST_ROLES = [
    (r":class:`([^`]+)`", r"`\1`"),
    (r":func:`([^`]+)`", r"`\1`"),
    (r":mod:`([^`]+)`", r"`\1`"),
    (r":data:`([^`]+)`", r"`\1`"),
    (r":meth:`([^`]+)`", r"`\1`"),
    (r"`~?([A-Za-z_\.]+)`", r"`\1`"),
]


def _clean_reST(text: str) -> str:
    """Convert simple reST roles and directives used in docstrings to markdown."""
    for pattern, repl in _REST_ROLES:
        text = re.sub(pattern, repl, text)
    return text


def _render_section(header: str, lines: list[str]) -> list[str]:
    """Render a docstring section (Args/Returns/Notes/Example) as markdown."""
    key = header.lower().rstrip("s")
    kind = "bullets"
    sub = f"**{header}:**"
    if key.startswith("exam"):
        kind, sub = "code", "**Example:**"
    elif key.startswith("note"):
        kind, sub = "paragraph", "**Notes:**"
    elif key.startswith(("arg", "kwarg", "param")):
        sub, kind = "**Args:**", "bullets"
    elif key.startswith(("ret", "yield", "return")):
        sub, kind = "**Returns:**", "bullets"
    elif key.startswith("raise"):
        sub, kind = "**Raises:**", "bullets"
    elif key.startswith("workaround"):
        sub, kind = "**Workarounds:**", "bullets"

    block = [sub]
    if kind == "code":
        code = [ln.strip() for ln in lines if ln.strip()]
        if code:
            block.extend(["```python", *code, "```"])
        return block

    text_lines = [ln.strip().rstrip() for ln in lines if ln.strip()]
    if kind == "paragraph":
        block.extend(text_lines)
        return block

    items: list[tuple[str | None, str]] = []
    cur_name: str | None = None
    cur_text: str = ""

    def flush() -> None:
        nonlocal cur_name, cur_text
        if cur_name is not None or cur_text:
            items.append((cur_name, cur_text))
        cur_name, cur_text = None, ""

    for line in text_lines:
        m = re.match(r"^~?\*{0,2}([A-Za-z_][A-Za-z0-9_.]*)\s*:\s*(.*)$", line)
        if m:
            flush()
            name = m.group(1).lstrip("~")
            cur_name = name if " " not in name else None
            cur_text = m.group(2)
        elif line.startswith("- "):
            flush()
            cur_name, cur_text = None, line.lstrip("- ").strip()
        elif cur_text or cur_name:
            cur_text = (cur_text + " " + line).strip()
        else:
            flush()
            cur_name, cur_text = None, line
    flush()

    for name, text in items:
        bullet = _clean_reST(text)
        if name:
            block.append(f"- `{name}`: {bullet}")
        else:
            block.append(f"- {bullet}  ")
    return block


def _render_docstring(doc: str) -> str:
    """Convert a plain docstring into markdown (reST roles, sections)."""
    doc = _clean_reST(doc.strip())
    lines = [ln.rstrip() for ln in doc.splitlines()]

    sections: dict[str, list[str]] = {}
    body: list[str] = []
    current: str | None = None

    for line in lines:
        stripped = line.strip()
        if stripped and stripped[0].isalpha() and stripped.endswith(":"):
            header = stripped[:-1]
            if any(
                header.lower().startswith(word)
                for word in ("arg", "ret", "raise", "return", "kwarg", "yield",
                             "note", "exam", "workaround")
            ):
                current = header
                sections.setdefault(header, [])
                continue
        if current:
            sections[current].append(line)
        else:
            body.append(line)

    paras: list[str] = []
    cur: list[str] = []
    for ln in body:
        stripped = ln.strip()
        if stripped == "" and cur:
            paras.append(" ".join(cur))
            cur = []
        elif stripped and stripped.startswith("- "):
            if cur:
                paras.append(" ".join(cur))
                cur = []
            paras.append(stripped)
        elif stripped:
            cur.append(stripped)
    if cur:
        paras.append(" ".join(cur))
    chunks = [ln.replace("*", "\\*") for ln in paras]
    for header, s_lines in sections.items():
        chunks.append("\n".join(_render_section(header, s_lines)))

    return "\n\n".join(chunks) or "_No documentation._"


def _render_class(cls: Any, name: str) -> list[str]:
    out = [f"{_heading(f'class `{name}`', 3)}"]
    try:
        sig = inspect.signature(cls)
    except (ValueError, TypeError):
        sig = None
    if sig:
        out.append(f"```python\n{name}{sig}\n```")
    doc = cls.__dict__.get("__doc__", "") or (cls.__doc__ or "")
    if doc and doc.strip():
        out.append(_render_docstring(inspect.cleandoc(doc)))

    if is_dataclass(cls):
        flds = fields(cls)
        if flds:
            out.append("**Fields:**")
            for f in flds:
                default = f.default if f.default is not MISSING else ""
                fdoc = f"- `{f.name}`"
                if default != "":
                    fdoc += f" = {default!r}"
                out.append(fdoc)
    return out


def _render_function(fn: Any, name: str) -> list[str]:
    sig = _signature(fn)
    out = [f"{_heading(f'`{name}{sig}`', 3)}"]
    doc = fn.__doc__
    if doc:
        out.append(_render_docstring(inspect.cleandoc(doc)))
    return out


def render_module(module: Any) -> tuple[str, int, int]:
    """Render a module to markdown and return (markdown_text, class_count, function_count)."""
    doc = inspect.cleandoc(module.__doc__ or "")
    lines = []
    if doc:
        doc_lines = doc.splitlines()
        title = doc_lines[0].strip()
        if title:
            lines.append(f"{_heading(title, 1)}")
        rest = "\n".join(doc_lines[1:]).strip()
        if rest:
            lines.append("")
            lines.append(_render_docstring(rest))

    members = _members(module)
    class_count = 0
    func_count = 0

    for name, obj in members:
        if lines and lines[-1] != "":
            lines.append("")
        if inspect.isclass(obj):
            class_count += 1
            lines.extend(_render_class(obj, name))
        else:
            func_count += 1
            lines.extend(_render_function(obj, name))

    return "\n".join(lines), class_count, func_count


def parse_examples() -> list[dict[str, Any]]:
    """Parse all example files from the examples directory."""
    examples: list[dict[str, Any]] = []
    if not EXAMPLES_DIR.exists():
        return examples

    for py_file in sorted(EXAMPLES_DIR.glob("*.py")):
        source_code = py_file.read_text(encoding="utf-8")
        docstring = ""
        try:
            tree = ast.parse(source_code)
            docstring = ast.get_docstring(tree) or ""
        except Exception:
            docstring = ""

        # Extract title and description from docstring
        doc_lines = [ln.strip() for ln in docstring.strip().splitlines() if ln.strip()]
        title = doc_lines[0] if doc_lines else py_file.stem.replace("_", " ").title()
        description = "\n".join(doc_lines[1:]) if len(doc_lines) > 1 else ""

        github_file_url = f"{GITHUB_REPO_URL}/blob/master/examples/{py_file.name}"

        examples.append({
            "filename": py_file.name,
            "stem": py_file.stem,
            "title": title,
            "description": description,
            "docstring": docstring,
            "code": source_code,
            "github_url": github_file_url,
        })
    return examples


def render_examples_page(examples: list[dict[str, Any]]) -> str:
    """Render the full examples markdown page."""
    lines = [
        "# Code Examples",
        "",
        "Runnable, end-to-end examples demonstrating how to use `netgo` for web search, "
        "parallel query execution, page content extraction, sitemap parsing, and Wikimedia integrations.",
        "",
        f"All source files are available in the **[GitHub Examples Directory]({GITHUB_EXAMPLES_URL})**.",
        "",
        "## Index of Examples",
        "",
        "| Example | Description | Source Link |",
        "| :--- | :--- | :--- |",
    ]

    for ex in examples:
        summary = ex["title"]
        anchor = ex["filename"].replace(".", "").replace("_", "-")
        lines.append(f"| [{ex['filename']}](#{anchor}) | {summary} | [View on GitHub]({ex['github_url']}) |")

    lines.append("")
    lines.append("---")
    lines.append("")

    for ex in examples:
        anchor = ex["filename"].replace(".", "").replace("_", "-")
        lines.append(f"## `{ex['filename']}`")
        lines.append("")
        lines.append(f"**Description:** {ex['title']}")
        if ex["description"]:
            lines.append("")
            lines.append(_clean_reST(ex["description"]))
        lines.append("")
        lines.append(f"**GitHub Source:** [{ex['filename']}]({ex['github_url']})")
        lines.append("")
        lines.append("```python")
        lines.append(ex["code"].strip())
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def render_index_page(
    module_stats: list[dict[str, Any]],
    examples: list[dict[str, Any]]
) -> str:
    """Render the home index.md page with VitePress home layout frontmatter."""
    lines = [
        "---",
        "layout: home",
        "",
        "hero:",
        '  name: "netgo"',
        '  text: "Python Search Toolkit & Wikimedia APIs"',
        "  tagline: Lightweight Python library for scraping search engines, extracting clean page content, parsing sitemaps, and querying Wikimedia APIs.",
        "  actions:",
        "    - theme: brand",
        "      text: Explore API Reference",
        "      link: /netgo",
        "    - theme: alt",
        "      text: Code Examples",
        "      link: /examples",
        "    - theme: alt",
        "      text: GitHub Repository",
        f"      link: {GITHUB_REPO_URL}",
        "",
        "features:",
        "  - title: Unified Search Engines",
        "    details: Engine-agnostic API querying Google and Bing, returning consistent Result objects with pagination and safe search.",
        "    link: /netgo.search",
        "  - title: Clean Page Extraction",
        "    details: Download any web page and extract the core article text, filtering out navigation, ads, headers, and footers.",
        "    link: /netgo.page",
        "  - title: XML & Text Sitemaps",
        "    details: Discover sitemaps via robots.txt, parse XML sitemap indexes, and crawl or filter URLs efficiently.",
        "    link: /netgo.sitemap",
        "  - title: Wikipedia & Commons",
        "    details: Full-text search, section outlines, summaries, backlinks, categories, and Commons media file inspection.",
        "    link: /netgo.wiki",
        "  - title: Wikidata & SPARQL",
        "    details: Resolve titles to QIDs, inspect claims, labels, descriptions, aliases, and run live SPARQL queries.",
        "    link: /netgo.wiki.wikidata",
        "  - title: Wiktionary",
        "    details: Look up parts of speech, numbered definitions, etymologies, and cross-language terms across editions.",
        "    link: /netgo.wiki.wiktionary",
        "---",
        "",
        "## Architecture Overview",
        "",
        "- **`netgo`**: Top-level package exports and convenient high-level functions (`search`, `search_many`, `fetch`).",
        "- **`netgo.search`**: Google and Bing backends, consistent `Result` models, pagination, error handling.",
        "- **`netgo.page`**: Article body extraction engine, HTML boilerplate filtering, and `Page` data model.",
        "- **`netgo.sitemap`**: Robots.txt discovery, XML/text sitemap parsing, index crawling, and prefix filtering.",
        "- **`netgo.wiki`**: MediaWiki Action API client, Wikipedia, Wikidata, Commons, and Wiktionary interfaces.",
        "",
        "## Submodule API Reference",
        "",
        "| Module | Documentation Link | Documented Classes | Documented Functions |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for stat in module_stats:
        mod_name = stat["name"]
        doc_link = f"[{mod_name}]({mod_name}.md)"
        lines.append(f"| `{mod_name}` | {doc_link} | {stat['classes']} | {stat['functions']} |")

    lines.append("")
    lines.append("## Runnable Examples")
    lines.append("")
    lines.append(
        f"End-to-end runnable scripts are located in the "
        f"[GitHub Examples Directory]({GITHUB_EXAMPLES_URL}) "
        f"and documented on the [Code Examples Page](/examples)."
    )
    lines.append("")
    lines.append("| Example File | Purpose / Feature | GitHub Source |")
    lines.append("| :--- | :--- | :--- |")

    for ex in examples:
        lines.append(f"| [`{ex['filename']}`](/examples#{ex['filename'].replace('.', '').replace('_', '-')}) | {ex['title']} | [View Source]({ex['github_url']}) |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Extract all documentation, examples, and write the markdown files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written_modules = 0
    module_stats: list[dict[str, Any]] = []

    # 1. Render all module API markdown files
    for module_name, module in sorted(iter_modules(netgo), key=lambda m: m[0]):
        text, n_classes, n_funcs = render_module(module)
        out_file = OUTPUT_DIR / f"{module_name}.md"
        out_file.write_text(text, encoding="utf-8")
        written_modules += 1
        module_stats.append({
            "name": module_name,
            "classes": n_classes,
            "functions": n_funcs,
        })

    # 2. Parse and render examples documentation
    examples = parse_examples()
    examples_text = render_examples_page(examples)
    (OUTPUT_DIR / "examples.md").write_text(examples_text, encoding="utf-8")

    # 3. Render home introduction index.md
    index_text = render_index_page(module_stats, examples)
    (OUTPUT_DIR / "index.md").write_text(index_text, encoding="utf-8")

    # Ensure docs/README.md is removed if it exists
    readme_path = OUTPUT_DIR / "README.md"
    if readme_path.exists():
        readme_path.unlink()

    print(f"Wrote {written_modules} module files, examples.md, and index.md to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()