"""AuditLogService — append-only local audit trail (SEC-4).

Records create / edit / delete / restore / sync / security events to
``<home>/audit.log``. Entries never contain SecureNote plaintext. Separating "what
gets audited" (decided in NoteService) from "how the log is written" (here) keeps the
SEC-4 event set easy to enumerate (``grep -rn 'audit.record' src/``).
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from ..models.audit import AuditLogEntry


class AuditLogService:
    def __init__(self, log_path: Path) -> None:
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, note_id: UUID | None = None, source: str = "local") -> None:
        """Append one audit entry. Append-only: existing lines are never rewritten."""
        entry = AuditLogEntry.of(event_type, note_id, source)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_line() + "\n")

    def list(self) -> list[AuditLogEntry]:
        """Read back the audit log (newest last)."""
        if not self._path.exists():
            return []
        out: list[AuditLogEntry] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) != 4:
                continue
            ts, source, event_type, nid = parts
            out.append(
                AuditLogEntry(
                    event_type=event_type,
                    note_id=None if nid == "-" else UUID(nid),
                    timestamp=ts,
                    source=source,
                )
            )
        return out
