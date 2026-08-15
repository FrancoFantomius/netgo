"""Unit tests for the clean_ignored.py script."""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path to import script functions
ROOT = Path(__file__).resolve().parent.parent
if ROOT not in map(Path, sys.path):
    sys.path.insert(0, str(ROOT))

from scripts.clean_ignored import (
    GitIgnoreRule,
    clean_ignored,
    find_repo_root,
    format_size,
    get_path_size,
    is_excluded,
    parse_gitignore_file,
    get_python_ignored_paths,
)


def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(500) == "500 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"
    assert format_size(1024 * 1024 * 1024) == "1.0 GB"


def test_gitignore_rule_matching():
    rule_dir = GitIgnoreRule(
        pattern="__pycache__",
        base_dir=Path("/root"),
        is_negation=False,
        is_dir_only=True,
    )
    assert rule_dir.matches("netgo/__pycache__", is_dir=True)
    assert not rule_dir.matches("netgo/__pycache__", is_dir=False)

    rule_wildcard = GitIgnoreRule(
        pattern="*.pyc",
        base_dir=Path("/root"),
        is_negation=False,
        is_dir_only=False,
    )
    assert rule_wildcard.matches("tests/foo.pyc", is_dir=False)
    assert not rule_wildcard.matches("tests/foo.py", is_dir=False)


def test_exclusion_matching():
    root = Path("/dummy/repo")
    path = root / ".venv" / "bin"
    assert is_excluded(path, root, [".venv"])
    assert not is_excluded(path, root, ["build"])


def test_clean_ignored_temp_directory(tmp_path: Path):
    # Setup test workspace
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    gitignore_file = repo_dir / ".gitignore"
    gitignore_file.write_text(
        "build/\n"
        "*.tmp\n"
        ".cache/\n"
        "!keep.tmp\n",
        encoding="utf-8",
    )

    # Tracked or regular files
    (repo_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    
    # Ignored files and folders
    build_dir = repo_dir / "build"
    build_dir.mkdir()
    (build_dir / "output.js").write_text("alert(1)", encoding="utf-8")

    cache_dir = repo_dir / ".cache"
    cache_dir.mkdir()
    (cache_dir / "data.bin").write_bytes(b"12345")

    temp_file = repo_dir / "test.tmp"
    temp_file.write_text("temporary", encoding="utf-8")

    ignored = get_python_ignored_paths(repo_dir)
    ignored_names = {p.relative_to(repo_dir).as_posix() for p in ignored}
    assert "build" in ignored_names
    assert ".cache" in ignored_names
    assert "test.tmp" in ignored_names
    assert "main.py" not in ignored_names

    # Test Dry Run
    total, deleted, freed = clean_ignored(
        root=repo_dir,
        dry_run=True,
        force=True,
        prefer_pure_python=True,
        quiet=True,
    )
    assert total >= 3
    assert deleted == 0
    assert build_dir.exists()
    assert temp_file.exists()

    # Test Real Clean
    total, deleted, freed = clean_ignored(
        root=repo_dir,
        dry_run=False,
        force=True,
        prefer_pure_python=True,
        quiet=True,
    )
    assert deleted >= 3
    assert not build_dir.exists()
    assert not cache_dir.exists()
    assert not temp_file.exists()
    assert (repo_dir / "main.py").exists()
    assert gitignore_file.exists()
