"""Typed error hierarchy for AstraNotes.

SEC-2 (graceful failure) relies on these. User-facing layers catch ``AstraNotesError``
and show its short ``message``; the full stack trace goes only to the debug log.
"""

from __future__ import annotations


class AstraNotesError(Exception):
    """Base class for all AstraNotes errors carrying a user-safe message."""


class ValidationError(AstraNotesError):
    """Raised when a note fails validation (empty title, too long, bad passphrase).

    Raised before any database work so a rejected save never partially persists.
    """


class RepositoryError(AstraNotesError):
    """Raised when the persistence layer cannot complete an operation."""


class NoteNotFoundError(AstraNotesError):
    """Raised when a note id does not resolve to a stored note."""


class UnlockError(AstraNotesError):
    """Raised when a SecureNote cannot be decrypted (wrong passphrase / tampering)."""
