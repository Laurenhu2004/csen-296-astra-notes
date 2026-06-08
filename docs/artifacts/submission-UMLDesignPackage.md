# Submission — Lab 4.2: Complete UML Design Package for AstraNotes

**Project:** AstraNotes
**Lab:** Week 4.2
**Chosen Technical Path:** Python 3

This package presents one connected UML view of AstraNotes. Names, requirement IDs, and architectural responsibilities match the upstream artifacts (`submission-ArchitectureDecisionLog.md`, `submission-RefinedRequirements.md`, `submission-BacklogAndSprintZero.md`). Each diagram below is a Mermaid fenced block so it renders inline on GitHub and most markdown previewers; a short prose summary follows each diagram for viewers that don't render Mermaid.

---

## 1. Class Diagram

The structural backbone of AstraNotes. Model classes (`Note`, `SecureNote`, `VersionHistory`, `AuditLogEntry`) are isolated from view-layer code per NFR-2. The `NoteRepository` interface is what makes `LocalSQLiteRepository` and (future) `RemoteRepository` swappable for FR-7.

```mermaid
classDiagram
    direction LR

    class Note {
      +id: UUID
      +title: str
      +body: str
      +kind: NoteKind
      +created_at: datetime
      +updated_at: datetime
      +to_dict() dict
    }

    class SecureNote {
      +passphrase_hash: bytes
      +encrypted_body: bytes
      +unlock(passphrase) str
    }

    class NoteKind {
      <<enumeration>>
      TEXT
      VOICE
      SECURE
    }

    class NoteRepository {
      <<interface>>
      +save(note) Note
      +get(id) Note
      +list() List~Note~
      +delete(id) void
      +history(id) List~VersionEntry~
    }

    class LocalSQLiteRepository
    class RemoteRepository

    class VersionHistory {
      +note_id: UUID
      +version: int
      +changed_at: datetime
      +body_diff: bytes
    }

    class AuditLogEntry {
      +event_type: str
      +note_id: UUID
      +timestamp: datetime
      +source: str
    }

    class NoteService {
      +create(title, body, kind) Note
      +edit(id, fields) Note
      +delete(id) void
      +restore_version(id, version) Note
    }

    class EncryptionService {
      +derive_key(passphrase, salt) bytes
      +encrypt(plaintext, key) bytes
      +decrypt(ciphertext, key) bytes
    }

    class ValidationService {
      +validate(note) Result
    }

    class VersionHistoryService {
      +snapshot(before, after) VersionEntry
      +list(note_id) List~VersionEntry~
      +restore(note_id, version) Note
    }

    class SyncService {
      +enable(account) void
      +sync_now() SyncReport
      +resolve_conflict(local, remote, choice) Note
    }

    class PluginManager {
      +register(kind, handler) void
      +handler_for(kind) PluginHandler
    }

    class View {
      +render(note) void
      +prompt(message) str
    }

    Note <|-- SecureNote
    Note --> NoteKind
    NoteRepository <|.. LocalSQLiteRepository
    NoteRepository <|.. RemoteRepository
    NoteService --> NoteRepository
    NoteService --> ValidationService
    NoteService --> VersionHistoryService
    NoteService --> EncryptionService
    NoteService --> PluginManager
    NoteService --> AuditLogEntry : writes
    SyncService --> NoteRepository
    SyncService --> EncryptionService
    VersionHistoryService --> VersionHistory
    View --> NoteService : commands only
```

**Summary.** `Note` is the base entity; `SecureNote` extends it with the encryption fields required by SEC-1. `NoteRepository` is the persistence contract — `LocalSQLiteRepository` is the Phase-1 implementation, `RemoteRepository` is the slot Cloud Sync (FR-7) plugs into without rewriting callers. `NoteService` is the only entry point for the `View`, satisfying NFR-2.

---

## 2. Object Diagram

A runtime snapshot showing one user session with one ordinary Note and one SecureNote in flight, plus an active local repository and the pending sync.

```mermaid
classDiagram
    direction TB

    class noteService_1 {
      <<NoteService instance>>
    }
    class repo_1 {
      <<LocalSQLiteRepository instance>>
      file = ~/AstraNotes/store.db
    }
    class encSvc_1 {
      <<EncryptionService instance>>
      kdf = scrypt
      cipher = Fernet
    }
    class note_42 {
      <<Note>>
      id = 9f1c…42
      title = "Sprint Zero risks"
      kind = TEXT
    }
    class note_77 {
      <<SecureNote>>
      id = 1a3d…77
      title = "Encryption spike notes"
      kind = SECURE
      encrypted_body = <ciphertext bytes>
    }
    class sync_1 {
      <<SyncService instance>>
      state = idle
      last_sync = 2026-04-12T14:02Z
    }
    class auditLog_1 {
      <<AuditLogEntry>>
      event_type = "note.created"
      note_id = 1a3d…77
      timestamp = 2026-04-12T14:01Z
    }

    noteService_1 --> repo_1
    noteService_1 --> encSvc_1
    noteService_1 --> note_42 : managing
    noteService_1 --> note_77 : managing
    sync_1 --> repo_1
    noteService_1 --> auditLog_1 : wrote
```

**Summary.** Two notes exist — one TEXT, one SECURE. Only the SECURE note carries `encrypted_body`. The single `LocalSQLiteRepository` instance is shared by both `NoteService` and `SyncService`, demonstrating that Cloud Sync (FR-7) operates on the same data without bypassing the encryption boundary (SEC-1).

---

## 3. Use Case Diagram

User goals. Drawn as a Mermaid `flowchart` because the GitHub-flavored Mermaid does not have a native use-case diagram type; the actor / use-case relationship is preserved through grouping.

```mermaid
flowchart LR
    user(["User"])
    subgraph AstraNotes
      uc1(("Create note (FR-1)"))
      uc2(("Edit note (FR-2)"))
      uc3(("Delete note (FR-3)"))
      uc4(("Mark note as private (FR-4, SEC-1)"))
      uc5(("Unlock SecureNote"))
      uc6(("View / restore version history (FR-6)"))
      uc7(("Search notes (FR-8)"))
      uc8(("Enable Cloud Sync (FR-7)"))
      uc9(("Resolve sync conflict (FR-7)"))
      uc10(("Install plugin (Charter)"))
    end
    syncSvr["External: Sync server"]
    plugin["External: Plugin file on disk"]

    user --> uc1
    user --> uc2
    user --> uc3
    user --> uc4
    user --> uc5
    user --> uc6
    user --> uc7
    user --> uc8
    user --> uc9
    user --> uc10
    uc8 -. communicates with .-> syncSvr
    uc9 -. communicates with .-> syncSvr
    uc10 -. loads .-> plugin
```

**Summary.** Ten primary use cases, all initiated by the User. Two external actors are present: the sync server (only used when FR-7 is enabled) and a plugin file on disk (loaded by `PluginManager`). Use cases for SecureNotes (`uc4`, `uc5`) cleanly separate "marking" from "unlocking" because the two actions touch different services.

---

## 4. Activity Diagram — "Create and Save a SecureNote"

The most security-sensitive workflow in the system; shows where ValidationService, EncryptionService, VersionHistoryService, and AuditLog hook in.

```mermaid
flowchart TD
    A([User chooses 'New SecureNote']) --> B[View prompts for title, body, passphrase]
    B --> C{Passphrase ≥ 12 chars?}
    C -- No --> C1[Show user-facing error<br/>SEC-2] --> B
    C -- Yes --> D[NoteService.create kind=SECURE]
    D --> E[ValidationService.validate]
    E --> E1{Valid?}
    E1 -- No --> E2[Return error to View<br/>SEC-2] --> Z([End])
    E1 -- Yes --> F[EncryptionService.derive_key<br/>scrypt + per-note salt]
    F --> G[EncryptionService.encrypt body → encrypted_body]
    G --> H[NoteRepository.save<br/>writes ciphertext only — SEC-1]
    H --> I[VersionHistoryService.snapshot<br/>FR-6]
    I --> J[Append AuditLogEntry<br/>'note.created' SEC-4]
    J --> K[View confirms save to user]
    K --> Z
```

**Summary.** Body plaintext exists only in memory between steps F and G; it is never passed to the Repository, never written to the audit log, and never returned to the View after save. Validation and SEC-2 graceful-failure paths are explicit.

---

## 5. Deployment Diagram

Where the system actually runs. AstraNotes is local-first; the Sync server is an optional component the user opts into.

```mermaid
flowchart TB
    subgraph UserDevice["User Device (e.g., laptop)"]
      direction TB
      App["AstraNotes Application<br/>(Python 3.12)"]
      App --> ViewLayer["View (CLI / desktop UI)"]
      App --> Services["Services<br/>NoteService, EncryptionService,<br/>ValidationService, VersionHistoryService,<br/>PluginManager, SyncService"]
      App --> RepoLayer["LocalSQLiteRepository"]
      RepoLayer --> DB[("Local SQLite store<br/>~/AstraNotes/store.db<br/>FTS5 index for FR-8")]
      RepoLayer --> AuditFile[("Append-only audit log<br/>SEC-4")]
      App --> PluginsDir[("Plugins directory<br/>(Text / Voice / Secure handlers)")]
    end

    subgraph CloudOptional["Optional Cloud (only if FR-7 enabled)"]
      SyncSvr["AstraNotes Sync Server<br/>(stores ciphertext only — SEC-1)"]
      RemoteDB[("Remote object store")]
      SyncSvr --> RemoteDB
    end

    Services -. TLS, end-to-end encrypted .-> SyncSvr
```

**Summary.** All required components run locally: View, Services, Repository, SQLite store, audit log, and plugin directory. The Sync server is shown as an optional zone — if the user does not enable FR-7, the cloud zone is unused. Even when sync is enabled, the server only ever holds ciphertext (SEC-1), so an FR-7 outage does not put SecureNote contents at risk.

---

## 6. Rationale — Why the Five Views Fit Together

These diagrams describe the same AstraNotes design from five complementary angles:

- The **class diagram** is the structural backbone; every later view names classes that appear here.
- The **object diagram** shows that backbone in motion — one concrete moment with one Note, one SecureNote, one Repository, and a queued sync — confirming that nothing in the runtime requires a class outside the structural model.
- The **use case diagram** shifts to user goals and confirms the requirement set (FR-1 through FR-8 plus SecureNote unlock and plugin install) is fully addressed by the structural backbone.
- The **activity diagram** zooms into the most security-sensitive workflow ("Create and Save a SecureNote") and shows where ValidationService, EncryptionService, VersionHistoryService, and the audit log hook in. Every requirement that touches that workflow (FR-1, FR-4, FR-5, FR-6, NFR-2, SEC-1, SEC-2, SEC-4) has a visible step.
- The **deployment diagram** anchors all of the above to physical reality: the User Device runs everything required, and the optional Cloud zone exists solely to serve FR-7 without ever holding plaintext.

A reader who looks at any one diagram can find the same component in the others under the same name. That consistency is the whole point of the package — the Week 5 traceability matrix in `submission-TraceabilityMatrix.md` exploits it directly.

---

## How AI helped

I used Copilot Chat to draft the initial class skeleton and the activity-diagram steps. Refinements I made:

- Renamed an AI-suggested `AuthManager` back to `EncryptionService` because it duplicated responsibilities and broke the locked vocabulary from `submission-ArchitectureDecisionLog.md`.
- Removed an AI-suggested `Database` god-class and replaced it with the `NoteRepository` interface + `LocalSQLiteRepository` / `RemoteRepository` pair — that split is what makes FR-7 a swap rather than a rewrite.
- Added the explicit "View → NoteService commands only" arrow because the AI's first draft had the View calling the Repository directly, which violates NFR-2.
- Wrote the activity diagram around SecureNote creation specifically (not generic "save") because the lab's "design must match scope" criterion is best satisfied by the workflow that combines the most requirements.
- Hand-wrote the rationale; the AI's first attempt was a generic "diagrams complement each other" summary that could have been written about any project.
