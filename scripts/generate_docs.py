"""Generate markdown API documentation from netgo's docstrings.

Run from the repository root:

    python scripts/generate_docs.py

This walks the ``netgo`` package with :func:`inspect`, extracts module,
class and function docstrings, and writes one markdown file per module
into ``docs/``, plus a ``docs/README.md`` index.
"""

from __future__ import annotations

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


def render_module(module: Any) -> str:
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
    for name, obj in _members(module):
        if lines and lines[-1] != "":
            lines.append("")
        if inspect.isclass(obj):
            lines.extend(_render_class(obj, name))
        else:
            lines.extend(_render_function(obj, name))
    return "\n".join(lines)


def main() -> None:
    """Extract all documentation and write the markdown files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index = ["# netgo API documentation", "",
             "Generated from docstrings with `scripts/generate_docs.py`.", "", ""]
    written = 0

    for module_name, module in sorted(iter_modules(netgo), key=lambda m: m[0]):
        text = render_module(module)
        out_file = OUTPUT_DIR / f"{module_name}.md"
        out_file.write_text(text, encoding="utf-8")
        index.append(f"- [{module_name}]({out_file.name})")
        written += 1

    (OUTPUT_DIR / "README.md").write_text("\n".join(index), encoding="utf-8")
    print(f"Wrote {written} module files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()