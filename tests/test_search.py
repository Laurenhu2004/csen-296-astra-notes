"""T-5 — FTS5 search correctness + SecureNote exclusion. Traces: FR-8, NFR-1, SEC-1.

This is the test the Test Improvement Log strengthened: it asserts *membership* of the
expected note in the results (not exact cardinality), exercises the real FTS5 index (no
mocking of the repository under test), and adds a dedicated SEC-1 case proving a locked
SecureNote body is not searchable.
"""

from __future__ import annotations

from astranotes.app import AppContext


def test_search_matches_body_text(app: AppContext) -> None:
    target = app.notes.create(title="Meeting", body="discuss the quarterly roadmap")
    app.notes.create(title="Lunch", body="tacos")
    results = app.notes.search("roadmap")
    assert target.id in {n.id for n in results}


def test_search_matches_title(app: AppContext) -> None:
    target = app.notes.create(title="Roadmap planning", body="")
    results = app.notes.search("roadmap")
    assert target.id in {n.id for n in results}


def test_results_ranked_by_recency(app: AppContext) -> None:
    older = app.notes.create(title="alpha note", body="shared keyword")
    newer = app.notes.create(title="beta note", body="shared keyword")
    app.notes.edit(newer.id, body="shared keyword refreshed")  # make newer the most recent
    results = [n.id for n in app.notes.search("shared")]
    assert results.index(newer.id) < results.index(older.id)


def test_locked_secure_body_not_searchable(app: AppContext) -> None:
    note = app.notes.create(title="Vault", body="treasure-coordinates-xyz")
    app.notes.make_secure(note.id, "longenoughpass123")
    # The unique body token must not surface a locked note (SEC-1)...
    assert app.notes.search("treasure-coordinates-xyz") == []
    # ...but the title still matches, so the note remains findable by name.
    assert note.id in {n.id for n in app.notes.search("Vault")}


def test_empty_query_lists_all(app: AppContext) -> None:
    app.notes.create(title="a", body="")
    app.notes.create(title="b", body="")
    assert len(app.notes.search("   ")) == 2
