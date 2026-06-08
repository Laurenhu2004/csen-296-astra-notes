"""T-3 — create persists, reloads, audits. Traces: FR-1, FR-5, NFR-2, SEC-4.

Integration test against a real SQLite store on tmp_path (no mocks of the layer
under test).
"""

from __future__ import annotations

from astranotes.app import AppContext
from astranotes.config import Settings
from astranotes.errors import ValidationError
from astranotes.services.audit_log import AuditLogService


def test_create_persists_and_reloads(app: AppContext) -> None:
    note = app.notes.create(title="Spike notes", body="hello world")
    # Reload from a fresh app context backed by the same on-disk store (FR-5).
    reloaded = build_fresh().notes.get(note.id)
    assert reloaded.title == "Spike notes"
    assert reloaded.body == "hello world"


def test_create_writes_audit_entry(app: AppContext) -> None:
    note = app.notes.create(title="Audited", body="x")
    events = AuditLogService(app.settings.audit_log_path).list()
    assert any(e.event_type == "note.created" and e.note_id == note.id for e in events)


def test_create_records_first_version(app: AppContext) -> None:
    note = app.notes.create(title="Versioned", body="v1 body")
    history = app.notes.history(note.id)
    assert len(history) == 1
    assert history[0].version == 1
    assert history[0].body_snapshot == "v1 body"


def test_empty_title_is_rejected_before_persist(app: AppContext) -> None:
    try:
        app.notes.create(title="   ", body="x")
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass
    assert app.notes.list() == []  # nothing partially persisted (SEC-2)


def build_fresh() -> AppContext:
    """A new AppContext over the same ASTRANOTES_HOME (simulates reopening the app)."""
    from astranotes.app import build_app

    return build_app(Settings.load())
