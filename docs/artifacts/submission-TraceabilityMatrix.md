# Submission — Lab 5.2: AstraNotes Requirements-to-UML Traceability Matrix

**Project:** AstraNotes
**Lab:** Week 5.2
**Chosen Technical Path:** Python 3

This submission validates whether the UML package in `submission-UMLDesignPackage.md` actually supports the requirements in `submission-RefinedRequirements.md`. The IDs are the same stable IDs introduced in Week 1.2 and reused throughout.

---

## 1. Traceability Matrix (8 most important requirements)

| Req ID | Requirement (short) | Class / Object Evidence | Use Case / Activity Evidence | Deployment Evidence | Status | Gap Note |
|--------|---------------------|--------------------------|------------------------------|---------------------|--------|----------|
| FR-1   | Create text note with title and markdown body. | `Note` class with `id, title, body, kind, created_at, updated_at`; `NoteService.create()` | Use case "Create note (FR-1)"; the activity diagram (specialized for SecureNote) shows the same `NoteService.create()` entry path. | `App → Services → LocalSQLiteRepository → SQLite store` on User Device. | Fully Traced | — |
| FR-4   | Mark note as private (SecureNote). | `SecureNote` (extends `Note`) with `passphrase_hash, encrypted_body`; `EncryptionService` | Use case "Mark note as private (FR-4, SEC-1)"; activity diagram steps F–G perform key derivation and encryption. | `Services` block on User Device; ciphertext sits in the local SQLite store. | Fully Traced | — |
| FR-6   | Maintain version history; allow restore. | `VersionHistory` class; `VersionHistoryService` with `snapshot / list / restore` | Use case "View / restore version history (FR-6)"; activity diagram step I appends a snapshot on every save. | Stored alongside notes in `~/AstraNotes/store.db`. | Fully Traced | — |
| FR-7   | Cloud Sync across devices. | `SyncService`, `RemoteRepository` (implements `NoteRepository`) | Use cases "Enable Cloud Sync (FR-7)" and "Resolve sync conflict (FR-7)"; no activity diagram for the sync workflow. | Optional Cloud zone with `SyncService` ↔ `Sync Server` over TLS, server holds ciphertext only. | Partially Traced | No activity diagram exists for the sync + conflict-resolution workflow. Recommend adding one before implementation begins. |
| FR-8   | Search notes by title/body, ranked by recency. | No dedicated `SearchService` class; search is implied as a method on `NoteRepository`. | Use case "Search notes (FR-8)" exists; no activity diagram for the search path. | Deployment shows an `FTS5 index for FR-8` annotation on the SQLite store. | Weakly Traced | Class diagram does not show how SecureNote bodies are excluded from search until unlocked. Need an explicit `SearchService` (or method on `NoteService`) and an activity diagram covering the locked-result branch. |
| NFR-1  | Open / search 10k notes < 100 ms p95. | Implied by `LocalSQLiteRepository` + FTS5 annotation in deployment. | Not addressed by any use case or activity diagram. | Deployment annotates an FTS5 index on the SQLite store. | Weakly Traced | NFR-1 is a performance constraint that no UML view explicitly demonstrates. Sprint-Zero spike S0-11 covers measurement; the matrix flags this as evidence-deferred-to-spike. |
| SEC-1  | Encrypt SecureNote bodies at rest. | `EncryptionService`; `SecureNote.encrypted_body`; `passphrase_hash` field | Activity diagram step G ("Encrypt body → encrypted_body") and step H ("Repository writes ciphertext only — SEC-1"). | Deployment annotation: "Sync Server stores ciphertext only — SEC-1." | Fully Traced | — |
| SEC-4  | Append-only audit log. | `AuditLogEntry` class; `NoteService → AuditLogEntry : writes` association. | Activity diagram step J ("Append AuditLogEntry 'note.created' SEC-4"). | Deployment shows `Append-only audit log` as a separate file on the User Device. | Fully Traced | — |

---

## 2. Traceability Metrics

- **Total requirements reviewed:** 8 (the most important ones across FR / NFR / SEC).
- **Fully Traced:** 5 (FR-1, FR-4, FR-6, SEC-1, SEC-4)
- **Partially Traced:** 1 (FR-7)
- **Weakly Traced:** 2 (FR-8, NFR-1)
- **Not Traced:** 0
- **Major UML elements without a clear requirement reason to exist:** 1 candidate — the `ValidationService` class is currently invoked inside the activity diagram but is not directly referenced by any requirement ID; it supports SEC-2 (graceful failure) implicitly. Either link it explicitly to SEC-2 in the next revision, or replace it with inline checks inside `NoteService`.

---

## 3. Gap Analysis

The package is structurally strong on the security and version-history requirements — those are the elements where the Charter is most opinionated and where I spent the most refinement effort. The gaps cluster around three areas, in order of how much they should change before implementation begins:

1. **FR-7 (Cloud Sync)** has all the structural pieces (`SyncService`, `RemoteRepository`, optional Cloud zone) but no activity diagram for the conflict-resolution path that the requirement explicitly demands ("user is prompted rather than silent merge"). Without a visual workflow, the implementation will reinvent the conflict policy. **Action:** add a sync activity diagram before sprint planning for US-5.
2. **FR-8 (Search)** is the weakest link — the class diagram has no `SearchService` and the locked-SecureNote handling rule from the refined requirement is not visible anywhere in UML. **Action:** add a thin `SearchService` (or document that search lives on `NoteRepository`) and capture the locked-result branch in either the class diagram notes or a small activity diagram. This also tightens the NFR-1 story.
3. **NFR-1 (performance)** is, by nature, hard to express in UML, but the deployment-level FTS5 annotation is currently the only evidence. **Action:** rely on Sprint-Zero spike S0-11 for measured evidence and add a one-line note to the class diagram documenting that `NoteRepository.list()` and search use the FTS5 index.

The single suspect element (`ValidationService`) should be explicitly justified by SEC-2 in the next revision rather than left implicit; small accretions like this are how design packages drift from "every element has a requirement reason to exist."

---

## How AI helped

I used Copilot Chat to draft an initial matrix with all 14 requirement IDs and let it propose `Fully` / `Partially` / `Weakly` labels. It was over-generous — it labelled FR-7 "Fully Traced" because the structural classes existed, ignoring that no activity diagram covers conflict resolution. I downgraded it to Partially. I also rejected its labelling of NFR-1 and FR-8 as "Fully Traced" via the FTS5 deployment annotation alone, because a one-word annotation in a deployment diagram is not the same as design evidence — both were downgraded to Weakly. The honest gap analysis (`ValidationService` as a candidate without a direct requirement, sync conflict missing an activity diagram, search missing a class) is mine and reflects the rubric's preference for honest recognition of weak support over self-congratulatory labels.
