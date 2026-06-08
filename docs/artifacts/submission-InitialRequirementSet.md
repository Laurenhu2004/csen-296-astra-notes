# Submission — Lab 1.2: Initial Requirement Set

**Project:** AstraNotes
**Lab:** Week 1.2 — Submission 2
**Chosen Technical Path:** Python 3

These IDs (`FR-*`, `NFR-*`, `SEC-*`) are stable and are reused verbatim in the Backlog, Refined Requirements, UML naming, and Traceability Matrix submissions.

---

## Functional Requirements (8)

- **FR-1 — Create text note.** The system shall allow a user to create a text note with a title, a markdown body, and auto-populated `created_at` / `updated_at` metadata.
- **FR-2 — Edit note.** The system shall allow a user to modify the title or body of an existing note and persist the change atomically.
- **FR-3 — Delete note.** The system shall allow a user to delete a note from the local collection and shall move the deleted note to a recoverable trash for at least 7 days before permanent removal.
- **FR-4 — Mark note as private (SecureNote).** The system shall allow a user to designate a note as a SecureNote, after which the note's body is encrypted at rest and accessible only after passphrase verification.
- **FR-5 — Persist and reload locally.** The system shall persist all notes to local storage and shall reload the user's collection on application start without data loss.
- **FR-6 — Version history.** The system shall maintain a version history of every note and shall allow the user to view and restore prior versions of a note.
- **FR-7 — Cloud Sync (change request from Week 1.1).** The system shall optionally synchronize the user's notes to a remote store so that the same notes are available across the user's devices.
- **FR-8 — Search notes.** The system shall allow a user to search notes by title or body text and shall return matching notes ranked by recency.

## Non-Functional Requirements (2)

- **NFR-1 — Responsiveness with 10k notes.** The system shall remain responsive when managing a collection of at least 10,000 notes; routine open and search operations shall complete in under 100 ms at the 95th percentile on commodity hardware.
- **NFR-2 — MVC separation.** The system architecture shall follow MVC; the View shall not import persistence or encryption modules directly, and the Model shall not depend on any view-layer code, so that components can be reviewed or tested independently.

## Security, Privacy, and Governance Requirements (4)

- **SEC-1 — Encryption at rest for SecureNotes.** SecureNote bodies shall be encrypted with authenticated symmetric encryption (e.g., Fernet / AES-GCM) before being written to disk; plaintext bodies shall never be persisted.
- **SEC-2 — Graceful failure.** The system shall handle invalid save, load, delete, or sync operations without crashing and shall surface user-facing errors with enough context for the user to recover.
- **SEC-3 — Dependency hygiene.** The project shall avoid unverified third-party dependencies; every external package shall be pinned, justified in writing, and reviewed before use.
- **SEC-4 — Audit log.** The system shall record an append-only audit log of create, edit, delete, and sync events with timestamp and source so that user actions are traceable for governance review.

---

## Why these requirements are ready for the next phase

Each requirement is written to support direct conversion downstream:

- **Backlog items** — FR-1 through FR-8 each map to one user story in `submission-BacklogAndSprintZero.md`.
- **Design decisions** — NFR-2 forces the MVC class boundaries used in `submission-UMLDesignPackage.md`. SEC-1 forces the existence of an `EncryptionService` and a `SecureNote` subtype.
- **Prototypes / spikes** — NFR-1 (10k notes, p95 < 100 ms) becomes a concrete Sprint Zero spike on SQLite indexing.
- **Tests** — every FR has an observable acceptance criterion ("after restart the same notes appear", "encrypted body is unreadable on disk", "search returns ranked results").
- **Acceptance criteria** — security requirements are verifiable (file inspection for SEC-1, fault-injection for SEC-2, lockfile review for SEC-3, log-format check for SEC-4).

---

## How AI helped

I generated a first pass with Copilot Chat using the stronger architecture prompt as context. Refinements I made:

- Rejected an AI-generated "FR — collaborative editing" requirement; it is out of scope for a local-first app and the Charter does not call for it.
- Strengthened "the system shall be fast" (vague) into NFR-1 with a concrete p95 latency target and a 10k-note volume.
- Added SEC-3 (dependency hygiene) and SEC-4 (audit log) — neither was in the AI's first pass but both follow directly from the Charter's auditability constraint.
- Promoted Cloud Sync to a stable functional requirement (FR-7) so the Week 1.1 change request flows through every later artifact rather than being a one-off discussion.
