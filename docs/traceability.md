# AstraNotes — Requirements → Code → Test Traceability

Evidence-based mapping from each requirement to the source that realizes it and the test
that verifies it. File paths are relative to the repository root.

| Req | Realized by (source) | Verified by (test) | Status |
|-----|----------------------|--------------------|--------|
| **FR-1** create | `models/note.py::Note.new`, `services/note_service.py::NoteService.create`, `services/validation.py::ValidationService.validate`, `repository/sqlite_repo.py::LocalSQLiteRepository.save` | `test_note_factory.py`, `test_validation_service.py`, `test_note_service_create.py`, `test_cli_create_flow.py` | ✅ |
| **FR-2** edit (atomic) | `NoteService.edit` + `LocalSQLiteRepository.save` (`with conn:` transaction) | `test_note_service_list.py::test_edit_changes_persist` | ✅ |
| **FR-3** delete → trash | `NoteService.delete` / `list_trash` / `restore_from_trash` / `purge_expired`; `LocalSQLiteRepository.soft_delete` / `restore_trashed` / `purge` | `test_delete_trash.py` | ✅ |
| **FR-4** SecureNote | `models/note.py::SecureNote`, `NoteService.make_secure` / `unlock`, `services/encryption.py::EncryptionService` | `test_secure_note.py` | ✅ |
| **FR-5** persist/reload | `LocalSQLiteRepository` (atomic writes, WAL) | `test_note_service_create.py::test_create_persists_and_reloads`, `test_cli_create_flow.py::test_cli_persists_across_runs` | ✅ |
| **FR-6** version history | `models/version.py::VersionEntry`, `services/version_history.py::VersionHistoryService`, `NoteService.history` / `restore_version` | `test_version_history.py` | ✅ |
| **FR-7** cloud sync | `repository/remote.py::RemoteRepository`, `services/sync.py::SyncService` | — (interface only) | 🟡 stub |
| **FR-8** search | `LocalSQLiteRepository.search` (FTS5), `NoteService.search` (excludes locked bodies) | `test_search.py` | ✅ |
| **NFR-1** perf | FTS5 index in `sqlite_repo.py`; `tools/seed.py` | `tests/perf/test_search_perf.py` (p95 < 100 ms @ 10k) | ✅ |
| **NFR-2** MVC | `app.py` composition root; ruff ban in `pyproject.toml`; Views import only `NoteService` | `test_mvc_boundary.py` | ✅ |
| **SEC-1** encrypt at rest | `EncryptionService` (scrypt + Fernet, per-note salt); SecureNote `body` stored blank | `test_secure_note.py::test_make_secure_encrypts_body_at_rest`, `test_search.py::test_locked_secure_body_not_searchable` | ✅ |
| **SEC-2** graceful failure | `errors.py` typed errors; Views catch `AstraNotesError` and show a message; repo degrades on bad FTS / storage errors | `test_validation_service.py`, `test_note_service_create.py::test_empty_title_is_rejected_before_persist` | ✅ |
| **SEC-3** dependency hygiene | one pinned runtime dep in `pyproject.toml` (`[project.dependencies]`), full transitive set locked in `uv.lock` | reviewed in CI | ✅ |
| **SEC-4** audit log | `models/audit.py::AuditLogEntry`, `services/audit_log.py::AuditLogService.record` | `test_note_service_create.py::test_create_writes_audit_entry`, `test_secure_note.py::test_wrong_passphrase_raises_and_audits` | ✅ |

## Notes on partial / deferred items

- **FR-7 (Cloud Sync)** — a "Could" backlog item (US-5). The ports exist
  (`RemoteRepository`, `SyncService`) so it can be implemented without reshaping callers;
  no behavior is claimed beyond the documented stub.
- **FR-6 `body_diff`** — realized as a full per-version snapshot rather than a diff (see
  `docs/architecture.md` → "Known simplifications"). Behavior (list + restore any version,
  append-only) is fully satisfied and tested.
