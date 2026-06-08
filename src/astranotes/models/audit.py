"""AuditLogEntry — one entry in the append-only audit log (SEC-4).

Records create / edit / delete / restore / sync / security events. Never contains
SecureNote plaintext. Written by AuditLogService to ``<home>/audit.log``.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .note import now_iso


@dataclass
class AuditLogEntry:
    event_type: str  # e.g. "note.created", "note.edited", "unlock.failed"
    note_id: UUID | None  # None for system/sync events
    timestamp: str
    source: str = "local"  # "local" or "sync"

    @classmethod
    def of(
        cls, event_type: str, note_id: UUID | None = None, source: str = "local"
    ) -> AuditLogEntry:
        return cls(event_type=event_type, note_id=note_id, timestamp=now_iso(), source=source)

    def to_line(self) -> str:
        """Render as a single append-only log line."""
        nid = str(self.note_id) if self.note_id is not None else "-"
        return f"{self.timestamp}\t{self.source}\t{self.event_type}\t{nid}"
