# Submission — Lab 6: AstraNotes Development Environment and First Realization Slices

**Project:** AstraNotes
**Lab:** Week 6 — Connecting Design to Prototype / Implementation
**Chosen Technical Path:** Python 3.12 (desktop, CLI shell first)

This submission moves AstraNotes from validated design into a defensible first realization. It chains directly off:

- `submission-ArchitectureDecisionLog.md` — Python path, module vocabulary.
- `submission-InitialRequirementSet.md` / `submission-RefinedRequirements.md` — stable FR / NFR / SEC IDs.
- `submission-BacklogAndSprintZero.md` — Sprint-Zero items S0-1…S0-14 are the source of every project-structure decision below.
- `submission-UMLDesignPackage.md` — every class/method name used in the code blocks below matches a name from this package.
- `submission-TraceabilityMatrix.md` — the slice traceability in §5 references the same FR/NFR/SEC IDs and the same UML elements.

---

## 1. Development Direction

**Language:** Python 3.12.
**Form factor:** Desktop, **CLI shell first**, with a Tkinter (stdlib) GUI reserved as the next slice once the create / list / edit / search backbone is stable.

**Defense.** The Project Charter says AstraNotes is local-first, and SEC-3 forbids unjustified third-party dependencies. The dependency-cheapest shell that still demonstrates the four UI surfaces the brief asks for (menu / profile / settings / notes workspace) is a stdlib CLI driven by `argparse` + `cmd`. A web app would force a web-framework dependency that violates SEC-3 and introduce a server attack surface that directly conflicts with the "local-first" stance from the Architecture Decision Log. Tkinter is the natural Phase-2 step because it is stdlib (no new dependency) and lets the same `NoteService` API back a windowed view without touching anything below the View layer (NFR-2).

I chose to build the CLI shell *as a real `View` that calls `NoteService`*, not a script that pokes the repository. That keeps NFR-2 honest from day one — when the GUI replaces the CLI, the View boundary is the only thing that changes.

---

## 2. Project Structure and Build/Run Environment

### Repository layout

```
astranotes/
├── README.md
├── DOD.md                        # Definition of Done at repo root (S0-5)
├── pyproject.toml                # build + tooling config
├── requirements.txt              # pinned deps per SEC-3
├── .pre-commit-config.yaml       # ruff / black / mypy (S0-3)
├── prompts/                      # one .md per significant prompt session (S0-6)
├── docs/
│   ├── architecture.md           # mirrors submission-ArchitectureDecisionLog.md
│   └── traceability.md           # mirrors submission-TraceabilityMatrix.md
├── src/astranotes/
│   ├── __init__.py
│   ├── __main__.py               # CLI entry: `python -m astranotes`
│   ├── models/
│   │   ├── note.py               # Note, SecureNote, NoteKind
│   │   └── audit.py              # AuditLogEntry
│   ├── repository/
│   │   ├── base.py               # NoteRepository (abstract)
│   │   └── sqlite_repo.py        # LocalSQLiteRepository + FTS5
│   ├── services/
│   │   ├── note_service.py       # NoteService (Slice A + B)
│   │   ├── validation.py         # ValidationService
│   │   ├── encryption.py         # EncryptionService (stub; FR-4 next slice)
│   │   ├── version_history.py    # VersionHistoryService
│   │   └── audit_log.py          # AuditLogService
│   ├── view/
│   │   └── cli.py                # menu loop, command dispatch
│   └── plugins/                  # Text/Voice/Secure handler registry
└── tests/
    ├── test_note_service_create.py
    └── test_note_service_list.py
```

Directory boundaries enforce **NFR-2** at the filesystem level (S0-1): the `view/` package is forbidden from importing `repository/` or `services.encryption`; this is checked by a CI import-graph rule (the `ruff` config below configures the relevant `flake8-tidy-imports` ban).

### `pyproject.toml` (excerpt)

```toml
[project]
name = "astranotes"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["cryptography==42.0.5"]   # only dep; SEC-3 justified below

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "TID"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"astranotes.repository".msg = "View layer must not import repository (NFR-2)."
"astranotes.services.encryption".msg = "View layer must not import encryption (NFR-2/SEC-1)."

[tool.mypy]
python_version = "3.12"
strict = true
```

### `requirements.txt`

```
# SEC-3: only one runtime dependency. cryptography provides the Fernet primitive
# locked in S0-10 for SEC-1; pinned to an exact version, justified in writing here.
cryptography==42.0.5
```

### `.pre-commit-config.yaml` (excerpt)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks: [{id: ruff}, {id: ruff-format}]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks: [{id: mypy, additional_dependencies: ["cryptography==42.0.5"]}]
```

### Run

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install
python -m astranotes            # launches the CLI shell
pytest                          # runs the two slice tests
```

---

## 3. UI Shell

The CLI shell exposes four surfaces. The names map 1:1 to the future Tkinter widgets so the migration is a View-only swap.

### Menu

```
AstraNotes >  help

Commands:
  new                Create a new note
  list               List notes (newest first)
  view  <id>         Open a note in detail view
  edit  <id>         Edit a note's title or body
  delete <id>        Delete (soft-delete to trash; FR-3)
  search <query>     Search by title / body (FR-8; deferred from this slice)
  settings           Show / edit settings
  profile            Show / edit profile
  quit
```

### Profile

Stored at `~/AstraNotes/profile.json`. Single-user, no auth (Phase 1).

```json
{
  "display_name": "Lauren",
  "default_kind": "TEXT",
  "created_at": "2026-05-11T18:04:00Z"
}
```

### Settings

Stored at `~/AstraNotes/settings.json`. Defaults track the refined requirements.

```json
{
  "store_path": "~/AstraNotes/store.db",
  "trash_retention_days": 7,                  // FR-3
  "kdf_params": {"n": 32768, "r": 8, "p": 1}, // SEC-1 scrypt
  "sync_enabled": false,                      // FR-7 opt-in
  "audit_log_path": "~/AstraNotes/audit.log"  // SEC-4
}
```

### Notes workspace

**List view** — title (truncated to 60 chars), `updated_at`, kind icon.

```
AstraNotes >  list

  ID        Updated              Kind  Title
  9f1c…42   2026-05-11 18:02     TEXT  Sprint Zero risks
  1a3d…77   2026-05-09 09:41     SEC   [locked SecureNote]
  4e88…03   2026-05-08 22:15     TEXT  Reading: Wirfs-Brock on responsibility
```

**Detail view** — `TEXT` renders the markdown body inline; `SECURE` shows a `[locked SecureNote]` placeholder until unlocked (FR-4, deferred slice); `VOICE` shows an audio-handle stub (Charter plugin, deferred slice).

---

## 4. First Functionality Slices

Two slices this week. Both are real code paths, not stubs.

### Slice A — Create a text note (FR-1)

Full happy path: `View` → `NoteService.create()` → `ValidationService.validate()` → `LocalSQLiteRepository.save()` → `AuditLogService.record()`.

**`models/note.py`**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class NoteKind(str, Enum):
    TEXT = "TEXT"
    VOICE = "VOICE"
    SECURE = "SECURE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Note:
    id: UUID
    title: str
    body: str
    kind: NoteKind
    created_at: str
    updated_at: str

    @classmethod
    def new(cls, title: str, body: str, kind: NoteKind = NoteKind.TEXT) -> "Note":
        ts = _now()
        return cls(id=uuid4(), title=title, body=body, kind=kind,
                   created_at=ts, updated_at=ts)
```

**`repository/sqlite_repo.py` (excerpt — `__init__`, schema, `save`)**

```python
import sqlite3
from pathlib import Path
from astranotes.models.note import Note


class LocalSQLiteRepository:
    def __init__(self, store_path: Path) -> None:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(store_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                  id          TEXT PRIMARY KEY,
                  title       TEXT NOT NULL,
                  body        TEXT NOT NULL,
                  kind        TEXT NOT NULL,
                  created_at  TEXT NOT NULL,
                  updated_at  TEXT NOT NULL
                );
            """)
            # FTS5 index for NFR-1; spike S0-11 measures actual p95.
            self._conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
                USING fts5(title, body, content='notes', content_rowid='rowid');
            """)

    def save(self, note: Note) -> Note:
        with self._conn:        # atomic transaction — partial writes impossible
            self._conn.execute(
                "INSERT OR REPLACE INTO notes "
                "(id, title, body, kind, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?);",
                (str(note.id), note.title, note.body, note.kind.value,
                 note.created_at, note.updated_at),
            )
        return note
```

**`services/validation.py`**

```python
from astranotes.models.note import Note

MAX_TITLE = 200
MAX_BODY_BYTES = 1 << 20   # 1 MB, per refined FR-1


class ValidationError(ValueError):
    """Typed error so callers can map it to a SEC-2 user-facing message."""


class ValidationService:
    def validate(self, note: Note) -> None:
        if not note.title.strip():
            raise ValidationError("Title cannot be empty.")
        if len(note.title) > MAX_TITLE:
            raise ValidationError(f"Title exceeds {MAX_TITLE} characters.")
        if len(note.body.encode("utf-8")) > MAX_BODY_BYTES:
            raise ValidationError("Body exceeds 1 MB.")
```

**`services/note_service.py` (`create`)**

```python
from astranotes.models.note import Note, NoteKind
from astranotes.repository.sqlite_repo import LocalSQLiteRepository
from astranotes.services.validation import ValidationService
from astranotes.services.audit_log import AuditLogService


class NoteService:
    def __init__(self, repo: LocalSQLiteRepository,
                 validator: ValidationService,
                 audit: AuditLogService) -> None:
        self._repo = repo
        self._validator = validator
        self._audit = audit

    def create(self, title: str, body: str,
               kind: NoteKind = NoteKind.TEXT) -> Note:
        note = Note.new(title=title, body=body, kind=kind)
        self._validator.validate(note)            # raises ValidationError -> SEC-2
        saved = self._repo.save(note)             # atomic write
        self._audit.record("note.created", saved.id)   # SEC-4
        return saved
```

**`view/cli.py` (dispatch for `new`)**

```python
def cmd_new(svc: NoteService) -> None:
    title = input("Title: ").strip()
    print("Body (end with a single '.' on its own line):")
    lines: list[str] = []
    while (line := input()) != ".":
        lines.append(line)
    try:
        note = svc.create(title=title, body="\n".join(lines))
    except ValidationError as e:                # SEC-2 user-facing path
        print(f"Could not save: {e}")
        return
    print(f"Saved note {note.id}.")
```

### Slice B — List notes (FR-1 + FR-5)

**`repository/sqlite_repo.py` (`list`)**

```python
def list(self) -> list[tuple[str, str, str, str]]:
    cur = self._conn.execute(
        "SELECT id, title, updated_at, kind FROM notes "
        "ORDER BY updated_at DESC;"
    )
    return cur.fetchall()
```

**`services/note_service.py` (`list`)**

```python
def list(self) -> list[tuple[str, str, str, str]]:
    return self._repo.list()
```

**`view/cli.py` (dispatch for `list`)**

```python
def cmd_list(svc: NoteService) -> None:
    rows = svc.list()
    if not rows:
        print("(no notes yet — try `new`)")
        return
    print(f"{'ID':<10} {'Updated':<20} {'Kind':<6} Title")
    for note_id, title, updated, kind in rows:
        short_id = note_id[:8] + "…"
        short_title = (title[:57] + "…") if len(title) > 60 else title
        print(f"{short_id:<10} {updated:<20} {kind:<6} {short_title}")
```

---

## 5. Traceability Note

| Slice | Requirements realized | UML elements realized |
|---|---|---|
| Slice A — Create text note | FR-1, FR-5, NFR-2 (View → Service → Repo), SEC-2 (validation-error path), SEC-4 (audit log append) | `Note`, `NoteKind`, `NoteService.create()`, `ValidationService.validate()`, `LocalSQLiteRepository.save()`, `AuditLogEntry`, `View` (CLI) |
| Slice B — List notes      | FR-1, FR-5, NFR-1 (foreshadows S0-11 spike), NFR-2 | `NoteService.list()`, `LocalSQLiteRepository.list()`, `View` (CLI) |

Honest gaps (deliberate this week, deferred not denied): FR-2 edit, FR-3 trash, FR-4 SecureNote, FR-6 version history, FR-7 cloud sync, FR-8 search are all wired into the menu and the schema but not implemented yet — exactly the "weakly traced" rows from `submission-TraceabilityMatrix.md`. The next slice closes FR-4 (SecureNote) because the gap analysis flagged it as the highest-value next move.

---

## 6. Slice Review (Slice A)

I reviewed Slice A specifically because it's the slice that combines the most boundaries (model + repository + service + audit + view) and is therefore where responsibility drift is most likely.

**Weakness 1 — Readability.** Copilot's first draft inlined `uuid4()` and `datetime.now(timezone.utc).isoformat()` *inside* `NoteService.create()`. The method became eight lines of mixed orchestration and construction. **Fix:** extracted `Note.new(title, body, kind)` as a factory on the model. `NoteService.create()` now reads top-to-bottom as four named steps (construct → validate → save → audit), which matches the activity diagram in `submission-UMLDesignPackage.md` exactly.

**Weakness 2 — Responsibility clarity.** Copilot's first draft had `NoteService.create()` calling `self._conn.execute("INSERT INTO audit_log …")` directly. That collapses two SEC-4 invariants into one method: now both *what* gets audited and *how* the log is written live in `NoteService`. **Fix:** introduced `AuditLogService.record(event_type, note_id)`. The View can't reach it (NFR-2), and the audit path is a single grep away — `grep -rn 'audit.record' src/` should enumerate every SEC-4 event.

**Weakness 3 — Failure handling.** Copilot's first draft wrapped the save in `try: ... except Exception: print("Error")`. That breaks SEC-2 in three ways: it swallows the typed `ValidationError` (no useful user message), it swallows `sqlite3.OperationalError` (user can't tell storage is broken), and it never writes a debug log. **Fix:**
- `ValidationService.validate()` raises a typed `ValidationError` *before* any DB work happens.
- `LocalSQLiteRepository.save()` wraps the write in `with self._conn:` — SQLite's context manager makes the write atomic; a crash mid-transaction rolls back rather than leaving a partial row.
- The CLI catches `ValidationError` and surfaces the message verbatim. `OperationalError` is allowed to propagate to a top-level handler in `__main__.py` which writes the trace to `~/AstraNotes/debug.log` and shows the user `"Storage unavailable — see ~/AstraNotes/debug.log"` (SEC-2 wording).

---

## 7. Debugging / Quality Lesson

The lesson from the slice review is that "failure handling" in the rubric is not "add `try / except` everywhere"; it's "let the right error type surface at the right boundary." The SEC-4 audit-log entry is *evidence* of what happened. The SEC-2 user-facing message is *recovery guidance*. The debug log is *post-mortem detail*. Copilot's bare `except Exception` collapsed all three into a single `print` and that's why audits would have become noisy and users uninformed. The Definition-of-Done item "logic explainable" only survives when each layer owns one concern — which is exactly why MVC separation (NFR-2) is in the requirements at all.

---

## 8. How AI Helped

I used Copilot Chat to scaffold `pyproject.toml`, the `CREATE VIRTUAL TABLE … USING fts5` statement, and a first pass at `NoteService.create()`. Refinements I made:

- **Rejected** Copilot's `pickle.dumps(note)` serialization — `pickle` is memory-unsafe and not auditable (SEC-3), and storing the body as a pickle blob would have made the FTS5 index unusable.
- **Rejected** Copilot's single-file `astranotes.py` monolith — it collapsed Model, Service, Repository, and View into one module, which violates NFR-2 at the import level. Replaced with the package layout in §2 and the `ruff.flake8-tidy-imports` ban that enforces it at CI time.
- **Rejected** the bare `except Exception` (see §6) in favor of typed errors at the right boundaries.
- **Kept and verified** the `pyproject.toml` scaffold and the FTS5 schema — I cross-checked the FTS5 `content_rowid` syntax against the SQLite docs because Copilot has hallucinated FTS5 column options in past sessions.
- The decision to **defer SecureNote (FR-4)** to the next slice is mine. The brief asks for "one or two first functionality slices," and a tighter slice with a real validation/audit path is more defensible than a wider slice that fakes the encryption boundary — exactly the rubric's "critical refinement over raw generation" framing from every prior lab.
