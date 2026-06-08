"""NFR-2 — the View layer must not import the repository or encryption modules.

This statically scans every module under astranotes/view and fails if it imports the
banned packages, double-checking the ruff flake8-tidy-imports ban configured in
pyproject.toml.
"""

from __future__ import annotations

import ast
from pathlib import Path

VIEW_DIR = Path(__file__).resolve().parents[1] / "src" / "astranotes" / "view"
BANNED = ("astranotes.repository", "astranotes.services.encryption")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:  # resolve `from ..repository import x` to absolute
                mod = "astranotes." + mod if mod else "astranotes"
            names.add(mod)
    return names


def test_view_does_not_import_repository_or_encryption() -> None:
    for path in VIEW_DIR.glob("*.py"):
        imported = _imports(path)
        for banned in BANNED:
            assert not any(name.startswith(banned) for name in imported), (
                f"{path.name} imports banned module '{banned}' (NFR-2 violation)"
            )
