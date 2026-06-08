"""PluginManager — note-kind handler registry (US-6 extensibility).

Lets new note kinds (e.g. a Voice handler) be added without modifying the core. Built-in
TEXT and SECURE handlers are always registered. External handlers are discovered from
the plugins directory; a handler that fails to load is skipped with a non-fatal warning
(SEC-2) so the app always starts.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..models.note import NoteKind

# A handler renders/normalizes a note body for its kind. Kept intentionally tiny for
# Phase 1 — the point is the extension seam, not a rich plugin API.
PluginHandler = Callable[[str], str]


def _identity(body: str) -> str:
    return body


class PluginManager:
    def __init__(self) -> None:
        self._handlers: dict[str, PluginHandler] = {}
        self.warnings: list[str] = []
        # Built-in kinds are always available.
        self.register(NoteKind.TEXT.value, _identity)
        self.register(NoteKind.SECURE.value, _identity)

    def register(self, kind: str, handler: PluginHandler) -> None:
        self._handlers[kind] = handler

    def handler_for(self, kind: str) -> PluginHandler:
        return self._handlers.get(kind, _identity)

    def available_kinds(self) -> list[str]:
        return sorted(self._handlers)

    def discover(self, plugins_dir: Path) -> None:
        """Load ``*.py`` handlers from a directory, degrading gracefully on error.

        Each plugin module may expose ``KIND: str`` and ``handle(body) -> str``.
        """
        if not plugins_dir.exists():
            return
        import importlib.util

        for path in sorted(plugins_dir.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(path.stem, path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                kind = getattr(module, "KIND", path.stem.upper())
                handler = getattr(module, "handle", _identity)
                self.register(kind, handler)
            except Exception as exc:  # SEC-2: a bad plugin must not stop startup
                self.warnings.append(f"Plugin '{path.name}' failed to load: {exc}")
