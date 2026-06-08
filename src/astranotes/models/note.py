"""Domain entities: NoteKind, Note, SecureNote.

These are the Model in MVC (NFR-2). They hold no persistence or encryption logic and
import nothing from ``repository`` or ``services`` — they are plain data with small,
defensible invariants (factory + serialization).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


def now_iso() -> str:
    """Current time as an ISO-8601 UTC timestamp with microseconds.

    Microsecond precision (e.g. 2026-06-07T18:04:00.123456Z) keeps "ranked by recency"
    (FR-8) deterministic even when notes are created/edited within the same second.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class NoteKind(StrEnum):
    """The kind of a note. SECURE bodies are encrypted at rest (FR-4 / SEC-1).

    VOICE is reserved for the plugin extensibility story (US-6) and is treated as a
    text-bodied note by the core until a Voice handler is registered.
    """

    TEXT = "TEXT"
    VOICE = "VOICE"
    SECURE = "SECURE"


@dataclass
class Note:
    """A text note (FR-1).

    Invariants are enforced by ValidationService, not here, so the model stays a
    transparent data carrier. ``new`` is the only blessed constructor for fresh notes
    (it stamps id and timestamps); reconstruction from storage uses the dataclass
    constructor directly.
    """

    id: UUID
    title: str
    body: str
    kind: NoteKind = NoteKind.TEXT
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    # None while live; an ISO timestamp once soft-deleted to trash (FR-3).
    deleted_at: str | None = None

    @classmethod
    def new(cls, title: str, body: str, kind: NoteKind = NoteKind.TEXT) -> Note:
        """Factory for a brand-new note: fresh UUID v4 and matching timestamps."""
        ts = now_iso()
        return cls(id=uuid4(), title=title, body=body, kind=kind, created_at=ts, updated_at=ts)

    def to_dict(self) -> dict[str, object]:
        """Serialize for display/JSON. Never includes SecureNote plaintext."""
        return {
            "id": str(self.id),
            "title": self.title,
            "body": self.body,
            "kind": self.kind.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }


@dataclass
class SecureNote(Note):
    """A note whose body is encrypted at rest (FR-4 / SEC-1).

    The plaintext ``body`` is blanked once encrypted; the ciphertext lives in
    ``encrypted_body`` and the per-note ``salt`` feeds the scrypt KDF. ``passphrase_hash``
    is a cheap pre-check; the real authentication is the Fernet auth tag on decrypt.
    Plaintext is never persisted to disk, audit, or debug logs.
    """

    kind: NoteKind = NoteKind.SECURE
    salt: bytes = b""
    encrypted_body: bytes = b""
    passphrase_hash: bytes = b""

    def to_dict(self) -> dict[str, object]:
        d = super().to_dict()
        # Do not leak plaintext; SecureNote bodies are blank in serialized form.
        d["body"] = ""
        d["encrypted"] = True
        return d
