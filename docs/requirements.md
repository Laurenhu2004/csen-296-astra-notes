# AstraNotes — Requirement Baseline

The canonical requirement IDs reused across every artifact and throughout the source and
tests. Full history is in [`artifacts/`](artifacts/) (refined baseline from Week 3.1).

## Functional Requirements

| ID | Requirement |
|----|-------------|
| **FR-1** | Create a text Note with a non-empty title (1–200 chars) and a UTF-8 markdown body (≤ 1 MB). On success, persist `created_at`/`updated_at` (ISO 8601 UTC) and return a stable UUID v4 `id`. |
| **FR-2** | Edit a Note's title/body atomically: either the new state fully persists (new `updated_at` + new version entry) or the original is preserved. |
| **FR-3** | Delete a Note to a recoverable trash for ≥ 7 days; permanent deletion afterward is irreversible and writes an audit entry. |
| **FR-4** | Mark any Note as a SecureNote with a passphrase ≥ 12 chars; the body becomes `encrypted_body`, and plaintext is never retained on disk or in logs. |
| **FR-5** | Persist all Notes (ciphertext, history, trash) locally and reload with no data loss absent disk corruption. |
| **FR-6** | Record an append-only version entry on every save; list and restore prior versions. Restore appends a new entry, never overwrites. |
| **FR-7** | Optional Cloud Sync mirroring Notes across authenticated devices; SecureNotes stay end-to-end encrypted; conflicts prompt the user rather than silently merging. |
| **FR-8** | Search Notes by title/body, ranked by recency. Locked SecureNote bodies do not contribute to results until unlocked. |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| **NFR-1** | With 10,000 Notes on commodity hardware: app opens < 1.5 s p95; search returns < 100 ms p95. |
| **NFR-2** | Follow MVC. The View must not import `astranotes.repository` or `astranotes.services.encryption`; detected by an automated import-graph check in CI. |

## Security, Privacy & Governance

| ID | Requirement |
|----|-------------|
| **SEC-1** | SecureNote bodies encrypted with authenticated symmetric encryption (Fernet); key derived from the passphrase via a memory-hard KDF (scrypt) with a per-note salt. Plaintext never persisted. |
| **SEC-2** | Handle invalid save/load/delete/sync without crashing; user-facing errors carry a short message; stack traces go to a debug log only. |
| **SEC-3** | Pin every dependency to an exact version, justified in writing; minimize the set. Phase-1 baseline: `cryptography` only. |
| **SEC-4** | Maintain an append-only local audit log of create/edit/delete/restore/sync/security events with `event_type`, `note_id`, `timestamp`, `source`; never contains plaintext. |
