"""NoteService — the single entry point the View layer talks to.

Orchestrates validation, persistence, encryption, version history, and audit logging
so the View never touches those concerns directly (NFR-2). Each public method reads as
the named steps of the corresponding UML activity diagram.
"""

from __future__ import annotations

import builtins
from datetime import UTC, datetime, timedelta
from uuid import UUID

from ..config import Settings
from ..errors import NoteNotFoundError, UnlockError, ValidationError
from ..models.note import Note, NoteKind, SecureNote, now_iso
from ..models.version import VersionEntry
from ..repository.base import NoteRepository
from .audit_log import AuditLogService
from .encryption import EncryptionService
from .validation import ValidationService
from .version_history import VersionHistoryService


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp, tolerant of optional fractional seconds."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class NoteService:
    def __init__(
        self,
        repo: NoteRepository,
        validator: ValidationService,
        audit: AuditLogService,
        encryption: EncryptionService,
        version: VersionHistoryService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._validator = validator
        self._audit = audit
        self._encryption = encryption
        self._version = version
        self._settings = settings
        # In-memory wrong-passphrase counters for backoff (FR-4 / SEC-4).
        self._unlock_attempts: dict[UUID, int] = {}

    # ---- create / read (FR-1, FR-5, FR-8) ------------------------------------

    def create(self, title: str, body: str, kind: NoteKind = NoteKind.TEXT) -> Note:
        note = Note.new(title=title, body=body, kind=kind)
        self._validator.validate(note)          # SEC-2: reject before any DB write
        saved = self._repo.save(note)            # FR-5: atomic persist
        self._version.snapshot(saved)            # FR-6: record v1
        self._audit.record("note.created", saved.id)  # SEC-4
        return saved

    def get(self, note_id: UUID) -> Note:
        note = self._repo.get(note_id)
        if note is None:
            raise NoteNotFoundError(f"No note with id {note_id}.")
        return note

    def list(self) -> builtins.list[Note]:
        return self._repo.list()

    def search(self, query: str) -> builtins.list[Note]:
        """Search by title/body, ranked by recency (FR-8).

        An empty query lists everything. SecureNote bodies are stored blank, so locked
        notes can only match on title — they are never matched by their encrypted body
        (SEC-1).
        """
        if not query.strip():
            return self._repo.list()
        return self._repo.search(query)

    # ---- edit / version history (FR-2, FR-6) ---------------------------------

    def edit(self, note_id: UUID, title: str | None = None, body: str | None = None) -> Note:
        note = self.get(note_id)
        if title is not None:
            note.title = title
        if body is not None:
            if isinstance(note, SecureNote):
                # Re-encrypting requires the passphrase; route through make_secure.
                raise ValidationError("Unlock and re-secure the note to change a private body.")
            note.body = body
        note.updated_at = now_iso()
        self._validator.validate(note)
        saved = self._repo.save(note)            # FR-2: atomic update
        self._version.snapshot(saved)            # FR-6: append new version
        self._audit.record("note.edited", saved.id)
        return saved

    def history(self, note_id: UUID) -> builtins.list[VersionEntry]:
        return self._version.list(note_id)

    def restore_version(self, note_id: UUID, version: int) -> Note:
        note = self.get(note_id)
        entries = {e.version: e for e in self._version.list(note_id)}
        if version not in entries:
            raise NoteNotFoundError(f"Version {version} not found for this note.")
        entry = entries[version]
        if isinstance(note, SecureNote):
            note.encrypted_body = entry.encrypted_body
        else:
            note.body = entry.body_snapshot
        note.updated_at = now_iso()
        saved = self._repo.save(note)
        self._version.snapshot(saved)            # FR-6: restore appends, never overwrites
        self._audit.record("note.restored", saved.id)
        return saved

    # ---- delete / trash (FR-3) -----------------------------------------------

    def delete(self, note_id: UUID) -> None:
        note = self.get(note_id)
        self._repo.soft_delete(note.id, now_iso())  # recoverable trash, >= 7 days
        self._audit.record("note.deleted", note.id)

    def list_trash(self) -> builtins.list[Note]:
        return self._repo.list_trashed()

    def restore_from_trash(self, note_id: UUID) -> Note:
        self._repo.restore_trashed(note_id)
        self._audit.record("note.untrashed", note_id)
        return self.get(note_id)

    def purge_expired(self) -> int:
        """Permanently remove notes whose trash retention has elapsed (FR-3)."""
        cutoff = datetime.now(UTC) - timedelta(
            days=self._settings.trash_retention_days
        )
        purged = 0
        for note in self._repo.list_trashed():
            if note.deleted_at is None:
                continue
            when = _parse_iso(note.deleted_at)
            if when < cutoff:
                self._repo.purge(note.id)
                self._audit.record("note.purged", note.id)
                purged += 1
        return purged

    # ---- SecureNote: encrypt & unlock (FR-4 / SEC-1 / SEC-4) -----------------

    def make_secure(self, note_id: UUID, passphrase: str) -> SecureNote:
        """Convert an existing note into a SecureNote, encrypting its body at rest."""
        self._validator.validate_passphrase(passphrase)
        note = self.get(note_id)
        if isinstance(note, SecureNote):
            raise ValidationError("Note is already private.")
        salt = self._encryption.new_salt()
        key = self._encryption.derive_key(passphrase, salt)
        secure = SecureNote(
            id=note.id,
            title=note.title,
            body="",  # SEC-1: plaintext never persisted
            kind=NoteKind.SECURE,
            created_at=note.created_at,
            updated_at=now_iso(),
            salt=salt,
            encrypted_body=self._encryption.encrypt(note.body, key),
            passphrase_hash=self._encryption.passphrase_fingerprint(passphrase, salt),
        )
        saved = self._repo.save(secure)
        self._version.snapshot(saved)
        self._audit.record("note.secured", saved.id)
        return secure

    def unlock(self, note_id: UUID, passphrase: str) -> str:
        """Return the decrypted body of a SecureNote, with wrong-passphrase backoff."""
        note = self.get(note_id)
        if not isinstance(note, SecureNote):
            raise ValidationError("This note is not private.")

        attempts = self._unlock_attempts.get(note_id, 0)
        if attempts >= self._settings.max_unlock_attempts:
            self._audit.record("unlock.blocked", note_id)
            raise UnlockError(
                "Too many failed attempts. Unlocking is temporarily locked for this note."
            )
        try:
            key = self._encryption.derive_key(passphrase, note.salt)
            plaintext = self._encryption.decrypt(note.encrypted_body, key)
        except UnlockError:
            self._unlock_attempts[note_id] = attempts + 1
            self._audit.record("unlock.failed", note_id)  # SEC-4
            raise
        self._unlock_attempts.pop(note_id, None)
        self._audit.record("note.unlocked", note_id)
        return plaintext
