"""VersionEntry — one append-only entry in a note's history (FR-6).

Every create / edit / restore appends a new entry; entries are never overwritten, so
the full lineage of a note is always recoverable. For SecureNotes the snapshot is the
ciphertext at that version (SEC-1); ``body_snapshot`` stays empty in that case.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .note import now_iso


@dataclass
class VersionEntry:
    note_id: UUID
    version: int  # monotonic, 1-based
    changed_at: str
    body_snapshot: str = ""  # plaintext snapshot for TEXT/VOICE notes
    encrypted_body: bytes = b""  # ciphertext snapshot for SECURE notes

    @classmethod
    def of(
        cls,
        note_id: UUID,
        version: int,
        body_snapshot: str = "",
        encrypted_body: bytes = b"",
    ) -> VersionEntry:
        return cls(
            note_id=note_id,
            version=version,
            changed_at=now_iso(),
            body_snapshot=body_snapshot,
            encrypted_body=encrypted_body,
        )
