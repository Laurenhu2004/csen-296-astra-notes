# Submission — Lab 7.2: AstraNotes Testing Strategy and First Test Set

**Project:** AstraNotes
**Lab:** Week 7.2
**Chosen Technical Path:** Python 3

This submission builds directly on:

- `submission-InitialRequirementSet.md` (`FR-*`, `NFR-*`, `SEC-*` IDs)
- `submission-BacklogAndSprintZero.md` (user stories `US-1..US-6`, Sprint Zero items `S0-1..S0-14`)
- `submission-UMLDesignPackage.md` (class and method names used in test code)
- `submission-ConnectingDesignToPrototype.md` (the Week 6 implementation slices that this lab tests)
- `submission-DefinitionOfDone.md` (DoD #11: "a unit or integration test exists" — this submission discharges that bar for Slice A and outlines it for the next slice)

---

## §1. AstraNotes Testing Strategy

**Shift-left framing.** Tests are not a phase at the end of coding — they are a design tool used while requirements and slices are still being shaped. The Week 7.1 architectural review showed AstraNotes had the right module boundaries (NFR-2); this strategy turns those boundaries into a *test pyramid*. Tests inform what to build next, not just confirm what was built.

**Pyramid for AstraNotes.** Unit-heavy at the base (`ValidationService`, the `Note.new()` factory, pure helpers); a narrow integration band where the boundary that actually fails in production lives (`NoteService` + `LocalSQLiteRepository` over a real temp-dir SQLite file); a small feature-level cap (one CLI smoke test that exercises `python -m astranotes` end-to-end). This mirrors the deck's "AstraNotes Test Mapping Example" almost line-for-line — *unit: validation + save request; integration: service + repository; feature: full create-note workflow.*

**When tests run.**

| Level | Where in dev flow | Trigger |
|---|---|---|
| Unit | Every save in editor; pre-commit | `pre-commit run pytest -k unit` (S0-3) |
| Integration | Every PR | Github Actions CI on push to feature branch |
| Feature | Before merge to `main` | CI required-check gate, plus manual smoke if the CLI shell changed |

**Tooling decision: `pytest`.** Pinned in `requirements.txt` as the second dependency after `cryptography`. Justified per **SEC-3**: `pytest` is the dominant Python test framework, the maintainer chain is well known, and the `pytest.ini` keeps configuration in one place. `unittest` (stdlib) would work but `pytest`'s `fixtures` and `parametrize` make the unit table read as a single test idea per row, which is what the rubric is grading on. Adding `pytest-cov` is **deferred** until Week 9 — the deck explicitly warns that coverage is "a clue, not a proof," so pulling it in this week would give the wrong signal.

**Scope discipline.** The Week 6 prototype delivered two slices: **Slice A — create text note** (FR-1, NFR-2, SEC-2) and **Slice B — list notes** (FR-1, FR-5). The first test set covers Slice A fully and outlines tests for Slice C — search (FR-8, NFR-1) — which is the next slice in the backlog and the natural next target for shift-left work.

---

## §2. Features Chosen

Two features, picked to satisfy the brief's "one or two" framing and to balance *implemented now* vs *outlined for next sprint*:

1. **Slice A — Create a text note** (FR-1, FR-5, NFR-2, SEC-2). Already implemented in Week 6. Tests are real and runnable.
2. **Slice C — Search notes** (FR-8, NFR-1, SEC-1). Not yet implemented. Test outlines exist so they can drive the implementation when the slice is picked up. The search outline is *deliberately weak in one spot* (see §3.5) — it becomes the target of the Week 9 Test Improvement Log.

These two together cover the test-pyramid base (validation), the integration boundary (service + repo), the feature level (CLI), and the not-yet-built slice (search outline). That is the spread the rubric calls "realistic first test choices rather than trying to test everything."

---

## §3. First Test Set

All files live under `astranotes/tests/` per the S0-1 package layout. Each test block is short and named for one observable behavior.

### 3.1 — `tests/test_validation_service.py` (unit, FR-1 + SEC-2)

```python
from __future__ import annotations
import pytest
from astranotes.models.note import Note, NoteKind
from astranotes.services.validation import ValidationService, ValidationError


@pytest.fixture
def svc() -> ValidationService:
    return ValidationService()


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_rejects_empty_or_whitespace_title(svc, title):
    note = Note.new(title=title, body="ok", kind=NoteKind.TEXT)
    with pytest.raises(ValidationError):
        svc.validate(note)


def test_rejects_title_over_200_chars(svc):
    note = Note.new(title="x" * 201, body="ok", kind=NoteKind.TEXT)
    with pytest.raises(ValidationError):
        svc.validate(note)


def test_rejects_body_over_1mib(svc):
    note = Note.new(title="ok", body="x" * (1 << 20 | 1), kind=NoteKind.TEXT)
    with pytest.raises(ValidationError):
        svc.validate(note)


def test_accepts_valid_note(svc):
    note = Note.new(title="Spike notes", body="### intro\n…", kind=NoteKind.TEXT)
    svc.validate(note)  # no exception
```

### 3.2 — `tests/test_note_factory.py` (unit, FR-1)

```python
from datetime import datetime
from uuid import UUID
from astranotes.models.note import Note, NoteKind


def test_factory_populates_id_and_timestamps():
    n = Note.new(title="t", body="b", kind=NoteKind.TEXT)
    assert UUID(n.id)
    assert datetime.fromisoformat(n.created_at).tzinfo is not None
    assert n.created_at == n.updated_at
    assert n.kind is NoteKind.TEXT
```

### 3.3 — `tests/test_note_service_create.py` (integration, FR-1 + FR-5 + SEC-4)

Real SQLite, real `LocalSQLiteRepository`, only `AuditLogService` mocked because audit-log behavior is orthogonal to "did the note save and reload."

```python
from unittest.mock import MagicMock
from astranotes.repository.sqlite_repo import LocalSQLiteRepository
from astranotes.services.validation import ValidationService
from astranotes.services.note_service import NoteService


def test_create_persists_and_reloads(tmp_path):
    repo = LocalSQLiteRepository(tmp_path / "notes.db")
    audit = MagicMock()
    svc = NoteService(repo=repo, validation=ValidationService(), audit=audit)

    n = svc.create(title="Hello", body="world", kind=None)

    rows = repo.list()
    assert (n.id, "Hello", n.updated_at, "TEXT") in rows
    audit.record.assert_called_once_with("note.created", n.id)
```

### 3.4 — `tests/test_cli_create_flow.py` (feature, FR-1 + FR-5 + NFR-2)

One end-to-end smoke test through the CLI entry point. Uses `subprocess` so the import-graph guard (`view` must not import `repository`) is exercised by the runtime rather than mocked away.

```python
import subprocess, sys, json
from pathlib import Path


def test_cli_new_then_list(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRANOTES_HOME", str(tmp_path))
    subprocess.run(
        [sys.executable, "-m", "astranotes", "new", "Title", "Body"],
        check=True,
    )
    out = subprocess.run(
        [sys.executable, "-m", "astranotes", "list"],
        check=True, capture_output=True, text=True,
    ).stdout
    assert "Title" in out
```

### 3.5 — `tests/test_search.py` (outline only — Slice C not yet built)

Slice C is unimplemented. The outline below is the *target* shape; the first assertion is **deliberately fragile** so the test fails in a way that surfaces the FR-8 acceptance criterion. This is the test the Week 9 Test Improvement Log will critique.

```python
# OUTLINE — to be implemented when Slice C lands.
# from astranotes.repository.sqlite_repo import LocalSQLiteRepository
# from astranotes.services.note_service import NoteService

def test_search_returns_matches_ranked_by_recency(tmp_path):
    """FR-8: search by title or body, ranked by recency."""
    # Seed 3 notes with bodies containing "alpha" at different timestamps.
    # results = svc.search("alpha")
    # NOTE: the assertion below is the weak draft on purpose — Week 9 target.
    # assert results == [note_3, note_2, note_1]   # asserts exact order
    pass
```

---

## §4. Test → Requirement Mapping

| Test ID | File | Requirement(s) | User Story | Test level |
|---|---|---|---|---|
| T-1 | `test_validation_service.py` | FR-1, SEC-2 | US-1 | unit |
| T-2 | `test_note_factory.py` | FR-1 | US-1 | unit |
| T-3 | `test_note_service_create.py` | FR-1, FR-5, NFR-2, SEC-4 | US-1 | integration |
| T-4 | `test_cli_create_flow.py` | FR-1, FR-5, NFR-2 | US-1 | feature |
| T-5 (outline) | `test_search.py` | FR-8, NFR-1, SEC-1 | US-3 | integration → perf |

Every test names at least one stable requirement ID. The mapping satisfies DoD #1 (trace to an objective) and DoD #11 (a unit or integration test exists for code artifacts).

---

## §5. Test Levels and Development-Flow Timing

| Level | What it proves | When it runs | What it does not prove |
|---|---|---|---|
| Unit (T-1, T-2) | Pure logic — validation rules, factory invariants | Editor save + pre-commit; <1 s | Persistence, transactions, audit wiring |
| Integration (T-3, T-5) | The seam between service and repository, including SQLite writes and audit calls | Every PR; <5 s on tmp_path SQLite | CLI argument parsing, user-facing error text |
| Feature (T-4) | End-to-end `python -m astranotes new … list` flow | Required check before merge to `main` | Performance at 10k notes (S0-11 spike, NFR-1) |

The unit tests live closest to the developer (sub-second feedback) and run continuously; the feature test is the slowest and runs once per PR. This matches the deck's diagram of testing distributed across *requirement → test design → build/code → test execution → maintenance → deploy*.

---

## §6. Scripted Automation vs AI-Native Testing

| | Scripted (pytest) | AI-native critique |
|---|---|---|
| **Strength** | Deterministic, fast, stable regression. T-1 through T-4 are scripted because their pass/fail signal needs to be reliable on every PR. | Drafts edge cases quickly; finds gaps a human would skim past; useful for the *first pass* of "what could I be missing here." |
| **Weakness** | Can give false confidence if the assertion is weak (T-5's draft is the example). | Will produce plausible-looking but low-value tests if not curated; cannot judge whether a missing test matters. |
| **Where I used each** | T-1..T-4: pytest, run locally and in CI. | T-5 outline drafting: AI proposed three candidate search tests; I kept one and added the SEC-1 SecureNote-exclusion assertion AI did not surface. |

The deck's exact framing: *scripted automation gives stable regression; AI helps draft and critique; human judgment decides what's worth keeping.* That split is reflected in the test set above.

---

## §7. How AI Helped

I asked Copilot Chat for a first cut at the validation tests using a deliberately weak prompt — *"write some pytest tests for the validation service."* It produced four tests, of which:

- **Kept (1).** The empty-title test idea was solid; I refined it into a `parametrize` over three whitespace variants so the rule is "no meaningful title," not just "no characters."
- **Refined (1).** The body-size test originally used `len(body) > 1_000_000` (decimal). I changed it to the `1 << 20` byte boundary that matches `MAX_BODY_BYTES` in `services/validation.py` — using a different number than the production constant defeats the point of the assertion.
- **Rejected (2).** A "test that creates a note and returns True" smoke test (asserts nothing); a fully-mocked `NoteService` test that mocked `repo.save` to return its argument — proves the mock works, not that the repository does.

For T-5 (search outline) I used a stronger prompt: *"Suggest one weak and one strong assertion for a search test that needs to verify FR-8 (ranked by recency) and SEC-1 (locked SecureNote bodies are not searched)."* AI proposed `assert results == [n_3, n_2, n_1]` — I **kept that as the deliberately weak version** because it illustrates the exact brittleness pattern the Week 9 deck calls out ("asserts ordering when only membership is guaranteed"). The stronger version (membership + SEC-1 exclusion) is what the test will become after Week 9.

The decision to put `pytest` in `requirements.txt` rather than as a dev-only extra is mine — AI suggested `requirements-dev.txt`, but the Week 6 submission only has one requirements file and splitting it adds a SEC-3 review surface (a second pinned list to keep justified) for marginal benefit at this scale.
