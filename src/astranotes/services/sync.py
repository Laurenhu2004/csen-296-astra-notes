"""SyncService — optional Cloud Sync across devices (FR-7), Phase-1 stub.

Sync is a "Could" backlog item (US-5), deferred until the local-first baseline is
stable. The interface is wired so the feature can be implemented later without
reshaping callers, and the three known failure modes (offline conflict, partial sync,
malicious server) are recorded as design risks (Sprint-Zero S0-13).

Design guarantees when implemented:
  * SecureNotes stay end-to-end encrypted in transit and at rest (SEC-1).
  * A detected conflict prompts the user — never a silent merge (FR-7 / US-5 AC-2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models.note import Note


@dataclass
class SyncReport:
    enabled: bool = False
    pushed: int = 0
    pulled: int = 0
    conflicts: list[str] = field(default_factory=list)
    message: str = ""


class SyncService:
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self, account: dict[str, str]) -> None:
        # Phase 1: opting in is recorded in settings but no remote is contacted.
        self._enabled = True

    def sync_now(self) -> SyncReport:
        if not self._enabled:
            return SyncReport(enabled=False, message="Sync is disabled (local-first).")
        return SyncReport(
            enabled=True,
            message="Cloud Sync is not implemented in this Phase-1 build (FR-7 deferred).",
        )

    def resolve_conflict(self, local: Note, remote: Note, choice: str) -> Note:
        """User chooses 'local' or 'remote'; both are preserved in version history."""
        return local if choice == "local" else remote
