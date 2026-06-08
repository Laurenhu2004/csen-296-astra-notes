"""VersionHistoryService — append-only note history (FR-6).

Every save appends a new VersionEntry; restoring a prior version appends yet another
entry rather than overwriting, so a note's full lineage is always recoverable. For
SecureNotes the snapshot is the ciphertext at that version (SEC-1).
"""

from __future__ import annotations

from uuid import UUID

from ..models.note import Note, NoteKind, SecureNote
from ..models.version import VersionEntry
from ..repository.base import NoteRepository


class VersionHistoryService:
    def __init__(self, repo: NoteRepository) -> None:
        self._repo = repo

    def snapshot(self, note: Note) -> VersionEntry:
        """Append a version entry capturing the note's current state."""
        next_version = len(self._repo.history(note.id)) + 1
        if isinstance(note, SecureNote) or note.kind is NoteKind.SECURE:
            entry = VersionEntry.of(
                note.id,
                next_version,
                encrypted_body=getattr(note, "encrypted_body", b""),
            )
        else:
            entry = VersionEntry.of(note.id, next_version, body_snapshot=note.body)
        self._repo.append_version(entry)
        return entry

    def list(self, note_id: UUID) -> list[VersionEntry]:
        return self._repo.history(note_id)
