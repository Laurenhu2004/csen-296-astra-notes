"""List ordering + edit. Traces: FR-1, FR-2, FR-5."""

from __future__ import annotations

from astranotes.app import AppContext


def test_list_is_ordered_by_recency(app: AppContext) -> None:
    a = app.notes.create(title="first", body="")
    b = app.notes.create(title="second", body="")
    # Touch `a` so it becomes most-recently-updated.
    app.notes.edit(a.id, body="touched")
    titles = [n.title for n in app.notes.list()]
    assert titles.index("first") < titles.index("second")
    assert b.id in {n.id for n in app.notes.list()}


def test_edit_changes_persist(app: AppContext) -> None:
    note = app.notes.create(title="t", body="old")
    app.notes.edit(note.id, title="t2", body="new")
    reloaded = app.notes.get(note.id)
    assert reloaded.title == "t2"
    assert reloaded.body == "new"
