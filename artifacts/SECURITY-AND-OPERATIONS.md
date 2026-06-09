# AstraNotes — Security, Deployment & Maintenance Notes

Operational companion to the design artifacts in this folder. It records the security
posture, how the app is deployed/run, and how it is kept healthy over time. Requirement IDs
(FR-/NFR-/SEC-) trace back to `RefinedRequirementBaselineforAstraNotes.pdf` and
`TraceabilityMatrix.pdf`.

## Security

- **Encryption at rest (SEC-1).** SecureNote bodies are encrypted with Fernet
  (AES-128-CBC + HMAC-SHA256). The key is derived from the user's passphrase with scrypt
  (`n=32768, r=8, p=1`) and a **per-note random salt**. Plaintext is never written to the
  database, audit log, or debug log. There is **no passphrase recovery** — a forgotten
  passphrase means the body is unrecoverable. This is a deliberate no-server-trust choice,
  surfaced to the user as a warning, not a TODO.
- **Audit log (SEC-4).** An append-only `audit.log` records create / edit / delete /
  restore / secure / unlock events, including failed unlock attempts. Entries carry
  `event_type`, `note_id`, `timestamp`, and `source`, and never contain plaintext.
- **Graceful failure (SEC-2).** All expected failures raise typed errors (`errors.py`); the
  View shows a short, actionable message and full stack traces go only to a debug log.
- **Dependency hygiene (SEC-3).** Exactly one runtime dependency (`cryptography`), pinned in
  `pyproject.toml`; the full transitive tree is locked in `uv.lock`, which is the review
  surface on any bump.
- **Architecture as a control (NFR-2).** The View (and plugins) cannot import the repository
  or the encryption service — enforced by a ruff import ban *and* a static test
  (`tests/test_mvc_boundary.py`), so a careless change can't route plaintext around the
  encryption boundary.

## Deployment

- **Local-first, no server.** AstraNotes runs entirely on the user's machine; there is no
  backend to provision. Cloud Sync (FR-7) is a designed stub, not a live service.
- **Install & run.** `uv sync` provisions Python 3.12 and the locked dependencies, then
  `uv run python -m astranotes` (CLI) or `uv run python -m astranotes --gui` (GUI). See the
  repo README for full setup.
- **Data location.** Everything lives under `ASTRANOTES_HOME` (default `~/AstraNotes/`):
  - `store.db` — SQLite: `notes`, `notes_fts` (FTS5), `version_history`
  - `audit.log` — append-only audit trail (SEC-4)
  - `settings.json` — trash retention, sync flag, KDF params, unlock-attempt limits
  - `plugins/` — optional note-kind handlers (US-6)
- **Isolation.** Set `ASTRANOTES_HOME` to a temp dir to run demos or tests without touching
  real notes.

## Maintenance

- **Dependency bumps.** Update the pin in `pyproject.toml`, re-run `uv lock`, and review the
  `uv.lock` diff for any new transitive package; CI must stay green before merge (SEC-3).
- **Audit-log growth.** The log is append-only; the design caps and rotates it (oldest
  entries archived) so it cannot fill the disk.
- **Backup / restore.** Back up by copying the `ASTRANOTES_HOME` directory; restore by
  copying it back. SecureNote ciphertext is portable, but the passphrase is not stored, so it
  must be remembered separately.
- **Before changing code.** Run `uv run pytest -q`, `uv run ruff check src tests`, and
  `uv run mypy src` (the same gates CI runs on every push/PR).
- **Known simplifications (honest scope).** Version history stores full snapshots rather than
  diffs (FR-6); unlock backoff is in-memory per process and resets on restart; Cloud Sync and
  rich plugins are interface stubs. Each is a documented, low-risk extension point, not a bug.
