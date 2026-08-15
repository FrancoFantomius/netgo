"""Clean ignored files and directories defined in .gitignore.

Run from the repository root or any subdirectory:

    python scripts/clean_ignored.py
    python scripts/clean_ignored.py --dry-run
    python scripts/clean_ignored.py --force
    python scripts/clean_ignored.py --exclude .venv .vscode

Supports both Git-based detection (exact matches via git) and a pure Python
fallback parser when Git is not available.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple


def find_repo_root(start_path: Path | None = None) -> Path:
    """Find the repository root by looking for .git or .gitignore."""
    current = (start_path or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / ".gitignore").exists():
            return parent
    return current


def format_size(size_bytes: int) -> str:
    """Format bytes into a human-readable string."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024.0
    return f"{size_bytes} B"


def get_path_size(path: Path) -> int:
    """Calculate the total size of a file or directory in bytes."""
    if not path.exists():
        return 0
    if path.is_file() or path.is_symlink():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            file_path = Path(root) / name
            try:
                if not file_path.is_symlink():
                    total += file_path.stat().st_size
            except OSError:
                pass
    return total


def handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to remove read-only files on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def remove_path(path: Path) -> Tuple[bool, str]:
    """Safely remove a file or directory tree, handling permissions."""
    try:
        if not path.exists() and not path.is_symlink():
            return True, "already removed"
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(
                path,
                onexc=lambda func, p, exc: handle_remove_readonly(func, p, exc)
                if sys.version_info >= (3, 12)
                else None,
                onerror=handle_remove_readonly
                if sys.version_info < (3, 12)
                else None,
            )
        else:
            try:
                path.unlink()
            except PermissionError:
                os.chmod(path, stat.S_IWRITE)
                path.unlink()
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Git-based ignored paths discovery
# ---------------------------------------------------------------------------

def get_git_ignored_paths(root: Path) -> List[Path] | None:
    """Use `git ls-files` to list ignored directories and files."""
    try:
        cmd = ["git", "ls-files", "--others", "-i", "--exclude-standard", "--directory"]
        res = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return None
        
        ignored: List[Path] = []
        for line in res.stdout.splitlines():
            clean_line = line.strip().rstrip("/\\")
            if not clean_line:
                continue
            path = (root / clean_line).resolve()
            if path != root and path.exists():
                ignored.append(path)
        return ignored
    except (FileNotFoundError, PermissionError):
        return None


# ---------------------------------------------------------------------------
# Pure-Python .gitignore fallback parser
# ---------------------------------------------------------------------------

class GitIgnoreRule:
    """Represents a parsed pattern rule from a .gitignore file."""

    def __init__(self, pattern: str, base_dir: Path, is_negation: bool, is_dir_only: bool):
        self.pattern = pattern
        self.base_dir = base_dir
        self.is_negation = is_negation
        self.is_dir_only = is_dir_only
        self.regex = self._compile_pattern(pattern)

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        has_slash = "/" in pattern.rstrip("/")
        pattern_str = pattern.strip("/")

        # Convert gitignore glob syntax to regex
        parts = []
        i = 0
        n = len(pattern_str)
        while i < n:
            c = pattern_str[i]
            if c == "*":
                if i + 1 < n and pattern_str[i + 1] == "*":
                    if i + 2 < n and pattern_str[i + 2] == "/":
                        parts.append("(?:.+/)?")
                        i += 3
                        continue
                    else:
                        parts.append(".*")
                        i += 2
                        continue
                else:
                    parts.append("[^/]*")
            elif c == "?":
                parts.append("[^/]")
            elif c == "[":
                j = pattern_str.find("]", i)
                if j != -1:
                    parts.append(pattern_str[i : j + 1])
                    i = j + 1
                    continue
                else:
                    parts.append(re.escape(c))
            else:
                parts.append(re.escape(c))
            i += 1

        regex_str = "".join(parts)
        if has_slash:
            full_regex = f"^{regex_str}$"
        else:
            full_regex = f"(?:^|/){regex_str}$"

        return re.compile(full_regex, re.IGNORECASE if sys.platform == "win32" else 0)

    def matches(self, rel_path: str, is_dir: bool) -> bool:
        if self.is_dir_only and not is_dir:
            return False
        clean_rel = rel_path.replace("\\", "/").strip("/")
        return bool(self.regex.search(clean_rel))


def parse_gitignore_file(filepath: Path, base_dir: Path) -> List[GitIgnoreRule]:
    """Parse rules from a .gitignore file."""
    if not filepath.is_file():
        return []
    rules: List[GitIgnoreRule] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        is_negation = line.startswith("!")
        if is_negation:
            line = line[1:].strip()

        is_dir_only = line.endswith("/")
        pattern = line.rstrip("/")

        if pattern:
            rules.append(
                GitIgnoreRule(
                    pattern=pattern,
                    base_dir=base_dir,
                    is_negation=is_negation,
                    is_dir_only=is_dir_only,
                )
            )
    return rules


def get_python_ignored_paths(root: Path) -> List[Path]:
    """Walk repository and identify ignored paths using .gitignore rules."""
    root_gitignore = root / ".gitignore"
    rules = parse_gitignore_file(root_gitignore, root)

    ignored_paths: List[Path] = []
    
    # We walk the filesystem top-down
    for current_dir, dirs, files in os.walk(root, topdown=True):
        current_path = Path(current_dir)
        
        # Never enter or touch .git
        if ".git" in dirs:
            dirs.remove(".git")
        
        # Check sub-directory gitignore if present
        sub_gitignore = current_path / ".gitignore"
        if sub_gitignore != root_gitignore and sub_gitignore.is_file():
            rules.extend(parse_gitignore_file(sub_gitignore, current_path))

        # Check directories first so we can prune whole trees
        dirs_to_prune: List[str] = []
        for d in list(dirs):
            dir_full = current_path / d
            rel = dir_full.relative_to(root).as_posix()
            
            is_ignored = False
            for rule in rules:
                if rule.matches(rel, is_dir=True):
                    is_ignored = not rule.is_negation

            if is_ignored:
                dirs_to_prune.append(d)
                ignored_paths.append(dir_full)

        for d in dirs_to_prune:
            dirs.remove(d)

        # Check files
        for f in files:
            if f == ".gitignore":
                continue
            file_full = current_path / f
            rel = file_full.relative_to(root).as_posix()

            is_ignored = False
            for rule in rules:
                if rule.matches(rel, is_dir=False):
                    is_ignored = not rule.is_negation

            if is_ignored:
                ignored_paths.append(file_full)

    return ignored_paths


# ---------------------------------------------------------------------------
# Filter and Clean Operations
# ---------------------------------------------------------------------------

def is_excluded(path: Path, root: Path, exclude_patterns: Sequence[str]) -> bool:
    """Check if path matches any custom exclusion patterns."""
    if not exclude_patterns:
        return False
    rel_posix = path.relative_to(root).as_posix()
    name = path.name
    for pattern in exclude_patterns:
        clean_pat = pattern.rstrip("/\\")
        if fnmatch.fnmatch(name, clean_pat) or fnmatch.fnmatch(rel_posix, clean_pat):
            return True
        if fnmatch.fnmatch(rel_posix, f"*{clean_pat}*"):
            return True
    return False


def clean_ignored(
    root: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    exclude: Sequence[str] | None = None,
    prefer_pure_python: bool = False,
    quiet: bool = False,
) -> Tuple[int, int, int]:
    """Discover and delete ignored files and folders.

    Returns:
        (total_items_count, deleted_count, total_bytes_freed)
    """
    repo_root = find_repo_root(root)
    exclude_patterns = exclude or []

    if not quiet:
        print(f"Repository Root: {repo_root}")

    # Discover ignored paths
    ignored_paths: List[Path] | None = None
    engine = "Git"
    if not prefer_pure_python:
        ignored_paths = get_git_ignored_paths(repo_root)

    if ignored_paths is None:
        engine = "Pure Python (.gitignore parser)"
        ignored_paths = get_python_ignored_paths(repo_root)

    if not quiet:
        print(f"Discovery Engine: {engine}")

    # Filter out exclusions
    target_paths: List[Path] = []
    for p in ignored_paths:
        if is_excluded(p, repo_root, exclude_patterns):
            if not quiet:
                print(f"[EXCLUDED] {p.relative_to(repo_root)}")
            continue
        target_paths.append(p)

    # Sort so children appear before parents or independent trees
    target_paths.sort(key=lambda p: len(p.parts), reverse=True)

    if not target_paths:
        if not quiet:
            print("No ignored files or directories found. Everything is clean!")
        return 0, 0, 0

    total_size = sum(get_path_size(p) for p in target_paths)

    if not quiet:
        action_title = "Would remove" if dry_run else "Removing"
        print(f"\nFound {len(target_paths)} ignored item(s) ({format_size(total_size)}):")
        for p in sorted(target_paths, key=lambda x: str(x.relative_to(repo_root))):
            kind = "DIR " if p.is_dir() else "FILE"
            rel = p.relative_to(repo_root)
            size_str = format_size(get_path_size(p))
            print(f"  [{kind}] {rel} ({size_str})")

    if dry_run:
        if not quiet:
            print(f"\n[DRY RUN] {len(target_paths)} items would be removed ({format_size(total_size)}).")
        return len(target_paths), 0, total_size

    # Confirmation if not forced and in interactive terminal
    if not force and sys.stdin.isatty():
        try:
            confirm = input(f"\nPermanently delete these {len(target_paths)} item(s)? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Operation cancelled.")
                return len(target_paths), 0, 0
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return len(target_paths), 0, 0

    # Delete paths
    deleted_count = 0
    freed_bytes = 0
    for p in target_paths:
        if not p.exists() and not p.is_symlink():
            continue
        sz = get_path_size(p)
        success, err = remove_path(p)
        if success:
            deleted_count += 1
            freed_bytes += sz
            if not quiet:
                print(f"  ✓ Deleted: {p.relative_to(repo_root)}")
        else:
            print(f"  ✗ Failed to delete {p.relative_to(repo_root)}: {err}", file=sys.stderr)

    if not quiet:
        print(f"\nDone! Successfully deleted {deleted_count} item(s) and freed {format_size(freed_bytes)}.")

    return len(target_paths), deleted_count, freed_bytes


def main():
    parser = argparse.ArgumentParser(
        description="Auto-delete all files and folders ignored by .gitignore in the repository."
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="List files and directories that would be deleted without actually deleting them.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Delete files without asking for confirmation.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        metavar="PATTERN",
        default=[],
        help="Patterns/names to exclude from deletion (e.g. --exclude .venv .vscode).",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=None,
        help="Target directory (defaults to repository root).",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Force using the pure Python .gitignore parser instead of Git.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output.",
    )

    args = parser.parse_args()

    clean_ignored(
        root=args.directory,
        dry_run=args.dry_run,
        force=args.force,
        exclude=args.exclude,
        prefer_pure_python=args.no_git,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
