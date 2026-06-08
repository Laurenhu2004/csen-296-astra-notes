"""Version history append-only + restore. Traces: FR-6."""

from __future__ import annotations

from astranotes.app import AppContext


def test_each_edit_appends_a_version(app: AppContext) -> None:
    note = app.notes.create(title="t", body="v1")
    app.notes.edit(note.id, body="v2")
    app.notes.edit(note.id, body="v3")
    history = app.notes.history(note.id)
    assert [e.version for e in history] == [1, 2, 3]
    assert [e.body_snapshot for e in history] == ["v1", "v2", "v3"]


def test_restore_appends_rather_than_overwrites(app: AppContext) -> None:
    note = app.notes.create(title="t", body="v1")
    app.notes.edit(note.id, body="v2")
    app.notes.restore_version(note.id, 1)  # restore the original
    history = app.notes.history(note.id)
    # Original entries are preserved; restore adds a new entry, never deletes.
    assert [e.version for e in history] == [1, 2, 3]
    assert app.notes.get(note.id).body == "v1"
    assert history[-1].body_snapshot == "v1"
