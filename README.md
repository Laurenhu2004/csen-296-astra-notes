# AstraNotes

A **local-first, encrypted note-taking application**. AstraNotes keeps your notes on
your own machine in a SQLite database, encrypts private notes at rest with a passphrase,
keeps a full version history of every note, and lets you search thousands of notes in
milliseconds — all with a single third-party dependency.

This repository contains both the **working application** and the **SDLC artifacts** developed across the
quarter (requirements → design → traceability → implementation → testing).

---

## Features

| Feature | Requirement | Status |
|---------|-------------|--------|
| Create / list / view text notes | FR-1, FR-5 | ✅ working |
| Edit notes (atomic) | FR-2 | ✅ working |
| Delete to recoverable trash (7-day retention) | FR-3 | ✅ working |
| **SecureNotes** — passphrase-encrypted bodies, at rest | FR-4, SEC-1 | ✅ working |
| Persist & reload locally | FR-5 | ✅ working |
| Version history + restore (append-only) | FR-6 | ✅ working |
| Full-text search (FTS5), ranked by recency | FR-8, NFR-1 | ✅ working |
| Cloud Sync across devices | FR-7 | 🟡 designed stub (Phase 2) |
| Plugin handlers for new note kinds | US-6 | 🟡 registry + graceful load |

Cross-cutting guarantees: **MVC separation enforced by lint + tests** (NFR-2),
**graceful, typed errors** (SEC-2), **single pinned dependency** (SEC-3), and an
**append-only audit log** of every create/edit/delete/restore/security event (SEC-4).

---

## Architecture (MVC)

```
View  (CLI shell / Tkinter GUI)
  │  calls only NoteService — never the repository or encryption (NFR-2)
  ▼
Services  NoteService ─ ValidationService ─ EncryptionService
          VersionHistoryService ─ AuditLogService ─ SyncService ─ PluginManager
  │
  ▼
Repository  NoteRepository (port)  →  LocalSQLiteRepository (SQLite + FTS5)
  │                                    RemoteRepository (FR-7 placeholder)
  ▼
Models  Note · SecureNote · NoteKind · VersionEntry · AuditLogEntry
```

The composition root (`src/astranotes/app.py`) is the only place that wires concrete
services together; Views receive a ready-built `NoteService`. The design rationale and
requirement mapping live in [`artifacts/ArchitectureDecisionLog.pdf`](artifacts/ArchitectureDecisionLog.pdf)
and [`artifacts/TraceabilityMatrix.pdf`](artifacts/TraceabilityMatrix.pdf).

**Stack:** Python 3.12 · SQLite + FTS5 (stdlib `sqlite3`) · `cryptography` (Fernet +
scrypt) · stdlib `cmd`/`argparse` (CLI) · stdlib `tkinter` (GUI). No ORM, no web
framework — every other capability is standard library (SEC-3). `uv` provisions the pinned
Python 3.12 automatically (see Setup), so no system Python is required.

---

## Setup

This project uses [**uv**](https://docs.astral.sh/uv/) for environment and dependency
management. Install it once (`curl -LsSf https://astral.sh/uv/install.sh | sh`), then:

```bash
cd csen-296-astra-notes
uv sync          # creates .venv, fetches Python 3.12, installs cryptography + dev tools + the package
```

That single command provisions the pinned Python 3.12 (per `.python-version`), installs the
exact locked dependency set from `uv.lock`, and installs the `astranotes` package itself in
editable mode — so `python -m astranotes` and the `astranotes` console command resolve even
though the source lives under `src/`. Run anything inside the environment with `uv run …`
(no manual activation needed).

Notes are stored under `~/AstraNotes/` by default. Override with `ASTRANOTES_HOME` to
keep a demo or test run isolated:

```bash
export ASTRANOTES_HOME=$(mktemp -d)
```

## Usage

```bash
uv run python -m astranotes          # Phase-1 CLI shell
uv run python -m astranotes --gui    # Phase-2 Tkinter GUI (same NoteService backend)
```

CLI commands: `new`, `list`, `view <id>`, `edit <id>`, `delete <id>`, `trash`,
`restore <id>`, `secure <id>`, `unlock <id>`, `search <query>`, `history <id>`,
`revert <id> <version>`, `plugins`, `sync`, `quit`. (`<id>` accepts a short id prefix
shown by `list`.)


---

## Testing & quality gates

```bash
uv run pytest -q                 # unit + integration + MVC-boundary + CLI smoke (37 tests)
uv run pytest tests/perf -q      # NFR-1 latency spike (seeds 10k notes)
uv run ruff check src tests      # lint, incl. the NFR-2 View→repository/encryption import ban
uv run mypy src                  # strict typing
```

Every test references the requirement IDs it covers (see headers in `tests/`). CI runs
all of the above on push/PR (`.github/workflows/ci.yml`).

---

## Repository map

```
src/astranotes/      application source (models / repository / services / view / plugins)
tests/               pytest suite (+ tests/perf for the NFR-1 spike)
tools/seed.py        synthetic-note generator for the performance spike
artifacts/           documents (requirements, UML, ADR,
                     backlog, traceability, DoD, test improvement log) +
                     SECURITY-AND-OPERATIONS.md (security / deployment / maintenance notes)
pyproject.toml       project metadata, pinned runtime dep, dev group, tool config
uv.lock              fully resolved dependency lockfile (reproducible installs, SEC-3)
.python-version      pinned interpreter (3.12) uv selects automatically
```

## How AI was used

I used GitHub Copilot across the quarter to draft requirements, UML, and code, then reviewed everything by hand against the lab submissions and the Definition of Done. The AI would make drafts and I would review the output and decide what to keep or what to change. The code reflects that every requirement maps to a test, and the MVC boundary is enforced by lint and a test rather than taken on faith.