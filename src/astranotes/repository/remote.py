"""RemoteRepository — placeholder for the optional Cloud Sync backend (FR-7).

Implements the same NoteRepository port so the local store can be mirrored to /
swapped with a remote one without rewriting callers. Sync is a "Could" item in the
backlog (US-5), deferred until the local-first baseline is stable, so every method
fails loudly and clearly rather than silently no-op'ing.

Design constraint (SEC-1): when implemented, this layer only ever transmits and
stores SecureNote *ciphertext* — the server never holds plaintext.
"""

from __future__ import annotations

import builtins
from uuid import UUID

from ..models.note import Note
from ..models.version import VersionEntry
from .base import NoteRepository

_MSG = "Cloud Sync (FR-7) is not enabled in this Phase-1 build. Notes are stored locally."


class RemoteRepository(NoteRepository):
    def save(self, note: Note) -> Note:
        raise NotImplementedError(_MSG)

    def get(self, note_id: UUID) -> Note | None:
        raise NotImplementedError(_MSG)

    def list(self, include_trashed: bool = False) -> builtins.list[Note]:
        raise NotImplementedError(_MSG)

    def list_trashed(self) -> builtins.list[Note]:
        raise NotImplementedError(_MSG)

    def soft_delete(self, note_id: UUID, deleted_at: str) -> None:
        raise NotImplementedError(_MSG)

    def restore_trashed(self, note_id: UUID) -> None:
        raise NotImplementedError(_MSG)

    def purge(self, note_id: UUID) -> None:
        raise NotImplementedError(_MSG)

    def search(self, query: str) -> builtins.list[Note]:
        raise NotImplementedError(_MSG)

    def append_version(self, entry: VersionEntry) -> None:
        raise NotImplementedError(_MSG)

    def history(self, note_id: UUID) -> builtins.list[VersionEntry]:
        raise NotImplementedError(_MSG)
