# AstraNotes — Architecture & Decisions

Mirrors the Architecture Decision Log developed across the quarter (full text in
[`artifacts/`](artifacts/)). It records the decisions that shape the codebase and *why*.

## Architectural style: layered MVC

```
View ──▶ Services ──▶ Repository ──▶ SQLite
  │         │
  └─────────┴──▶ Models (plain data, no I/O)
```

- **Model** — `Note`, `SecureNote`, `NoteKind`, `VersionEntry`, `AuditLogEntry`
  (`src/astranotes/models/`). Pure data; imports nothing from `repository`/`services`.
- **Repository** — the `NoteRepository` port (`repository/base.py`) and its
  `LocalSQLiteRepository` implementation; `RemoteRepository` is the FR-7 placeholder.
- **Services** — `NoteService` orchestrates `ValidationService`, `EncryptionService`,
  `VersionHistoryService`, `AuditLogService`, plus `SyncService` and `PluginManager`.
- **View** — the `cmd` CLI (`view/cli.py`) and the Tkinter GUI (`view/gui.py`), both over
  the same `NoteService`.
- **Composition root** — `app.py` is the only module that constructs concrete services
  and hands the View a ready `NoteService`.

## ADR-1 — MVC boundary enforced at build time (NFR-2)

**Decision.** The View may reach the system only through `NoteService`. It must not import
`astranotes.repository` or `astranotes.services.encryption`.
**Enforcement.** Two independent checks:
1. ruff `flake8-tidy-imports.banned-api` in `pyproject.toml` (fails lint/CI).
2. `tests/test_mvc_boundary.py` statically parses the View modules and asserts neither
   banned package is imported.
**Why.** Keeps encryption and persistence swappable and prevents a View (or plugin) from
ever touching plaintext or raw storage.

## ADR-2 — SQLite + FTS5 as the persistence backend (FR-5, FR-8, NFR-1)

**Decision.** Use the stdlib `sqlite3` module with an FTS5 virtual table for search; no
ORM. Writes are atomic via the connection's transaction context (`with conn:`).
**Why.** Local-first, zero-server, full-text search that meets the < 100 ms p95 target at
10k notes (validated by `tests/perf`). SecureNote bodies are stored blank in `notes.body`,
so locked ciphertext is never indexed — reinforcing SEC-1 at the storage layer.

## ADR-3 — Fernet + scrypt for SecureNotes (FR-4, SEC-1)

**Decision.** Encrypt SecureNote bodies with Fernet (AES-128-CBC + HMAC-SHA256). Derive
the key from the passphrase with scrypt (`n=32768, r=8, p=1`) and a per-note random salt.
**Why.** Authenticated encryption + a memory-hard KDF, from a single vetted dependency.
There is **no passphrase recovery** — a forgotten passphrase means the body is
unrecoverable. This is a deliberate design choice (no server trust), documented as a
user-facing warning, not an oversight.

## ADR-4 — Single pinned dependency (SEC-3)

**Decision.** `cryptography` is the only runtime dependency, pinned exactly in
`pyproject.toml`; the full resolved tree is captured in `uv.lock` for reproducible,
review-able installs. Everything else (storage, CLI, GUI, JSON, UUIDs) is standard library.
New dependencies require a written justification tied to a requirement ID.

## Storage layout

```
$ASTRANOTES_HOME/  (default ~/AstraNotes/)
├── store.db        SQLite: notes, notes_fts (FTS5), version_history
├── audit.log       append-only audit trail (SEC-4)
├── settings.json   trash retention, sync flag, KDF params, unlock attempts
└── plugins/        optional note-kind handlers (US-6)
```

## Known simplifications (honest scope)

- **Version history stores full snapshots, not diffs.** The requirement names
  `body_diff`; a full per-version snapshot is a simpler, equally-correct realization of
  "list and restore any prior version" and is documented as such in the traceability.
- **Cloud Sync (FR-7) and rich plugins are designed stubs.** `RemoteRepository` and
  `SyncService` implement the interfaces and fail clearly; `PluginManager` loads handlers
  and degrades gracefully (SEC-2). These are "Could"/Phase-2 backlog items.
- **Backoff is in-memory per process.** Failed-unlock counting resets on restart; a
  persistent lockout would be a straightforward extension.
