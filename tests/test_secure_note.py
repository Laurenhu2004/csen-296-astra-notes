"""SecureNote round-trip + backoff. Traces: FR-4, SEC-1, SEC-4."""

from __future__ import annotations

import sqlite3

from astranotes.app import AppContext
from astranotes.config import Settings
from astranotes.errors import UnlockError, ValidationError
from astranotes.models.note import NoteKind, SecureNote
from astranotes.services.audit_log import AuditLogService

PASS = "correcthorsebattery"  # >= 12 chars


def test_make_secure_encrypts_body_at_rest(app: AppContext) -> None:
    note = app.notes.create(title="Diary", body="my secret plans")
    secure = app.notes.make_secure(note.id, PASS)
    assert isinstance(secure, SecureNote)
    assert secure.kind is NoteKind.SECURE

    # SEC-1: the plaintext must not appear anywhere in the raw DB bytes.
    raw = Settings.load().store_path.read_bytes()
    assert b"my secret plans" not in raw

    # And the stored row carries ciphertext, not plaintext.
    conn = sqlite3.connect(str(Settings.load().store_path))
    body, enc = conn.execute(
        "SELECT body, encrypted_body FROM notes WHERE id=?", (str(note.id),)
    ).fetchone()
    assert body == ""
    assert len(enc) > 0


def test_unlock_with_correct_passphrase_returns_plaintext(app: AppContext) -> None:
    note = app.notes.create(title="Diary", body="my secret plans")
    app.notes.make_secure(note.id, PASS)
    assert app.notes.unlock(note.id, PASS) == "my secret plans"


def test_wrong_passphrase_raises_and_audits(app: AppContext) -> None:
    note = app.notes.create(title="Diary", body="secret")
    app.notes.make_secure(note.id, PASS)
    try:
        app.notes.unlock(note.id, "totally-wrong-pass")
        raise AssertionError("expected UnlockError")
    except UnlockError:
        pass
    events = [e.event_type for e in AuditLogService(app.settings.audit_log_path).list()]
    assert "unlock.failed" in events


def test_backoff_blocks_after_max_attempts(app: AppContext) -> None:
    note = app.notes.create(title="Diary", body="secret")
    app.notes.make_secure(note.id, PASS)
    for _ in range(app.settings.max_unlock_attempts):
        try:
            app.notes.unlock(note.id, "nope-nope-nope")
        except UnlockError:
            pass
    # Even the correct passphrase is now refused until backoff clears.
    try:
        app.notes.unlock(note.id, PASS)
        raise AssertionError("expected backoff UnlockError")
    except UnlockError as exc:
        assert "locked" in str(exc).lower()


def test_short_passphrase_rejected(app: AppContext) -> None:
    note = app.notes.create(title="Diary", body="secret")
    try:
        app.notes.make_secure(note.id, "short")
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass
