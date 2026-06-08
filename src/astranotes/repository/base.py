"""NoteRepository — the persistence interface (port).

Services depend on this abstraction, not on a concrete store, so the local SQLite
backend can be swapped for the future RemoteRepository (FR-7) without touching callers.
"""

from __future__ import annotations

import builtins
from abc import ABC, abstractmethod
from uuid import UUID

from ..models.note import Note
from ..models.version import VersionEntry


class NoteRepository(ABC):
    @abstractmethod
    def save(self, note: Note) -> Note:
        """Insert or update a note atomically; return the persisted object."""

    @abstractmethod
    def get(self, note_id: UUID) -> Note | None:
        """Return a single note by id (including soft-deleted), or None."""

    @abstractmethod
    def list(self, include_trashed: bool = False) -> builtins.list[Note]:
        """Return notes ordered by recency (updated_at DESC)."""

    @abstractmethod
    def list_trashed(self) -> builtins.list[Note]:
        """Return only soft-deleted notes (FR-3 trash view)."""

    @abstractmethod
    def soft_delete(self, note_id: UUID, deleted_at: str) -> None:
        """Move a note to trash by stamping deleted_at (FR-3)."""

    @abstractmethod
    def restore_trashed(self, note_id: UUID) -> None:
        """Clear deleted_at, bringing a note back from trash (FR-3)."""

    @abstractmethod
    def purge(self, note_id: UUID) -> None:
        """Permanently delete a note and its history (irreversible, FR-3)."""

    @abstractmethod
    def search(self, query: str) -> builtins.list[Note]:
        """Full-text search over title and body, ranked by recency (FR-8)."""

    @abstractmethod
    def append_version(self, entry: VersionEntry) -> None:
        """Append an immutable version-history entry (FR-6)."""

    @abstractmethod
    def history(self, note_id: UUID) -> builtins.list[VersionEntry]:
        """Return the append-only version history for a note (FR-6)."""
