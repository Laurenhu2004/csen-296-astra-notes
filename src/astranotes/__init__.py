"""AstraNotes — a local-first, encrypted note-taking application.

Package layout follows the MVC separation required by NFR-2:

    models/       domain entities (Note, SecureNote, VersionEntry, AuditLogEntry)
    repository/   persistence (NoteRepository interface + LocalSQLiteRepository)
    services/     orchestration & cross-cutting concerns (NoteService et al.)
    view/         user interfaces (CLI shell + Tkinter GUI) — call NoteService only
    plugins/      note-kind handler registry (PluginManager)

The View layer reaches the rest of the system exclusively through ``NoteService``;
it must never import ``repository`` or ``services.encryption`` (enforced by ruff and
by tests/test_mvc_boundary.py).
"""

__version__ = "0.1.0"
