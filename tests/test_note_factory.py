"""T-2 — Note factory invariants. Traces: FR-1."""

from __future__ import annotations

from uuid import UUID

from astranotes.models.note import Note, NoteKind


def test_new_assigns_uuid4_and_matching_timestamps() -> None:
    note = Note.new(title="Spike", body="body")
    assert isinstance(note.id, UUID)
    assert note.id.version == 4
    assert note.created_at == note.updated_at  # fresh note: created == updated
    assert note.kind is NoteKind.TEXT
    assert note.deleted_at is None


def test_distinct_notes_get_distinct_ids() -> None:
    a = Note.new(title="a", body="")
    b = Note.new(title="b", body="")
    assert a.id != b.id


def test_to_dict_is_serializable_and_omits_no_core_field() -> None:
    note = Note.new(title="t", body="b")
    d = note.to_dict()
    assert set(d) >= {"id", "title", "body", "kind", "created_at", "updated_at"}
    assert d["id"] == str(note.id)
