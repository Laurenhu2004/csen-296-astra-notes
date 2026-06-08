"""ValidationService — enforces note invariants before persistence (FR-1 / SEC-2).

Raised errors are typed (ValidationError) and carry user-safe messages, and they are
raised *before* any database work so a rejected note never partially persists.
"""

from __future__ import annotations

from ..errors import ValidationError
from ..models.note import Note

MAX_TITLE = 200
MAX_BODY_BYTES = 1 << 20  # 1 MB UTF-8 (FR-1)
MIN_PASSPHRASE = 12  # FR-4 / SEC-1


class ValidationService:
    def validate(self, note: Note) -> None:
        """Raise ValidationError if the note violates FR-1 limits."""
        if self.is_title_empty(note.title):
            raise ValidationError("Title cannot be empty.")
        if len(note.title) > MAX_TITLE:
            raise ValidationError(f"Title exceeds {MAX_TITLE} characters.")
        if len(note.body.encode("utf-8")) > MAX_BODY_BYTES:
            raise ValidationError("Body exceeds the 1 MB limit.")

    def validate_passphrase(self, passphrase: str) -> None:
        """Raise ValidationError if a SecureNote passphrase is too short (FR-4)."""
        if len(passphrase) < MIN_PASSPHRASE:
            raise ValidationError(
                f"Passphrase must be at least {MIN_PASSPHRASE} characters."
            )

    @staticmethod
    def is_title_empty(title: str) -> bool:
        """A title is empty if it is blank or only whitespace."""
        return not title.strip()
