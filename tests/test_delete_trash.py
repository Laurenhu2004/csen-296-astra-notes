"""Soft-delete to trash, restore, and retention purge. Traces: FR-3."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from astranotes.app import AppContext
from astranotes.models.note import now_iso


def test_delete_moves_to_trash_not_gone(app: AppContext) -> None:
    note = app.notes.create(title="temp", body="x")
    app.notes.delete(note.id)
    assert note.id not in {n.id for n in app.notes.list()}
    assert note.id in {n.id for n in app.notes.list_trash()}


def test_restore_from_trash(app: AppContext) -> None:
    note = app.notes.create(title="temp", body="x")
    app.notes.delete(note.id)
    app.notes.restore_from_trash(note.id)
    assert note.id in {n.id for n in app.notes.list()}


def test_purge_expired_removes_only_old_trash(app: AppContext) -> None:
    fresh = app.notes.create(title="fresh", body="x")
    old = app.notes.create(title="old", body="x")
    app.notes.delete(fresh.id)
    app.notes.delete(old.id)

    # Backdate the "old" note's deletion well past the retention window.
    past = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    app.notes._repo.soft_delete(old.id, past)  # type: ignore[attr-defined]

    purged = app.notes.purge_expired()
    assert purged == 1
    trash_ids = {n.id for n in app.notes.list_trash()}
    assert old.id not in trash_ids  # gone forever
    assert fresh.id in trash_ids  # still recoverable
    assert now_iso()  # sanity: timestamp helper available
