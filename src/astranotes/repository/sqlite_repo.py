"""LocalSQLiteRepository — local-first persistence on SQLite + FTS5.

Backs every functional requirement that needs durable state:
  FR-5 persist/reload, FR-3 trash (soft delete), FR-6 version history,
  FR-8 search (FTS5), and NFR-1 (FTS5 keeps search sub-100ms at 10k notes).

Writes are atomic via the connection's transaction context (``with self._conn:``);
a crash mid-write rolls back so the prior state survives intact. No ORM is used
(SEC-3 dependency hygiene): the stdlib ``sqlite3`` module only.
"""

from __future__ import annotations

import builtins
import sqlite3
from pathlib import Path
from uuid import UUID

from ..errors import RepositoryError
from ..models.note import Note, NoteKind, SecureNote
from ..models.version import VersionEntry
from .base import NoteRepository

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    body            TEXT NOT NULL,
    kind            TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    deleted_at      TEXT,
    salt            BLOB NOT NULL DEFAULT x'',
    encrypted_body  BLOB NOT NULL DEFAULT x'',
    passphrase_hash BLOB NOT NULL DEFAULT x''
);

-- FR-8 / NFR-1: full-text index over title + body. External-content table mirrors
-- `notes` and is kept in sync by triggers below. SecureNote bodies are stored blank
-- in `notes.body`, so locked ciphertext is never indexed (reinforces SEC-1).
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, body, content='notes', content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, body) VALUES (new.rowid, new.title, new.body);
END;
CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body)
        VALUES ('delete', old.rowid, old.title, old.body);
END;
CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, body)
        VALUES ('delete', old.rowid, old.title, old.body);
    INSERT INTO notes_fts(rowid, title, body) VALUES (new.rowid, new.title, new.body);
END;

CREATE TABLE IF NOT EXISTS version_history (
    note_id        TEXT NOT NULL,
    version        INTEGER NOT NULL,
    changed_at     TEXT NOT NULL,
    body_snapshot  TEXT NOT NULL DEFAULT '',
    encrypted_body BLOB NOT NULL DEFAULT x'',
    PRIMARY KEY (note_id, version)
);
"""


class LocalSQLiteRepository(NoteRepository):
    def __init__(self, store_path: Path) -> None:
        store_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(store_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)

    def close(self) -> None:
        self._conn.close()

    # ---- writes ---------------------------------------------------------------

    def save(self, note: Note) -> Note:
        if isinstance(note, SecureNote):
            salt, enc_body, pass_hash = note.salt, note.encrypted_body, note.passphrase_hash
        else:
            salt, enc_body, pass_hash = b"", b"", b""
        try:
            with self._conn:  # atomic transaction (FR-2/FR-5 robustness)
                self._conn.execute(
                    """
                    INSERT INTO notes
                        (id, title, body, kind, created_at, updated_at, deleted_at,
                         salt, encrypted_body, passphrase_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        body=excluded.body,
                        kind=excluded.kind,
                        updated_at=excluded.updated_at,
                        deleted_at=excluded.deleted_at,
                        salt=excluded.salt,
                        encrypted_body=excluded.encrypted_body,
                        passphrase_hash=excluded.passphrase_hash
                    """,
                    (
                        str(note.id),
                        note.title,
                        note.body,
                        note.kind.value,
                        note.created_at,
                        note.updated_at,
                        note.deleted_at,
                        salt,
                        enc_body,
                        pass_hash,
                    ),
                )
        except sqlite3.Error as exc:  # pragma: no cover - storage failure path (SEC-2)
            raise RepositoryError("Could not save the note to local storage.") from exc
        return note

    def soft_delete(self, note_id: UUID, deleted_at: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE notes SET deleted_at=? WHERE id=?", (deleted_at, str(note_id))
            )

    def restore_trashed(self, note_id: UUID) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE notes SET deleted_at=NULL WHERE id=?", (str(note_id),)
            )

    def purge(self, note_id: UUID) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM notes WHERE id=?", (str(note_id),))
            self._conn.execute(
                "DELETE FROM version_history WHERE note_id=?", (str(note_id),)
            )

    def append_version(self, entry: VersionEntry) -> None:
        with self._conn:
            self._conn.execute(
                """INSERT INTO version_history
                       (note_id, version, changed_at, body_snapshot, encrypted_body)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    str(entry.note_id),
                    entry.version,
                    entry.changed_at,
                    entry.body_snapshot,
                    entry.encrypted_body,
                ),
            )

    # ---- reads ----------------------------------------------------------------

    def get(self, note_id: UUID) -> Note | None:
        row = self._conn.execute(
            "SELECT * FROM notes WHERE id=?", (str(note_id),)
        ).fetchone()
        return _row_to_note(row) if row else None

    def list(self, include_trashed: bool = False) -> builtins.list[Note]:
        where = "" if include_trashed else "WHERE deleted_at IS NULL"
        rows = self._conn.execute(
            f"SELECT * FROM notes {where} ORDER BY updated_at DESC"
        ).fetchall()
        return [_row_to_note(r) for r in rows]

    def list_trashed(self) -> builtins.list[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC"
        ).fetchall()
        return [_row_to_note(r) for r in rows]

    def search(self, query: str) -> builtins.list[Note]:
        match = _to_fts_match(query)
        if not match:
            return []
        try:
            rows = self._conn.execute(
                """
                SELECT n.* FROM notes n
                JOIN notes_fts f ON f.rowid = n.rowid
                WHERE notes_fts MATCH ? AND n.deleted_at IS NULL
                ORDER BY n.updated_at DESC
                """,
                (match,),
            ).fetchall()
        except sqlite3.Error:
            # A malformed FTS expression should degrade to "no matches", not crash (SEC-2).
            return []
        return [_row_to_note(r) for r in rows]

    def history(self, note_id: UUID) -> builtins.list[VersionEntry]:
        rows = self._conn.execute(
            "SELECT * FROM version_history WHERE note_id=? ORDER BY version ASC",
            (str(note_id),),
        ).fetchall()
        return [
            VersionEntry(
                note_id=UUID(r["note_id"]),
                version=r["version"],
                changed_at=r["changed_at"],
                body_snapshot=r["body_snapshot"],
                encrypted_body=bytes(r["encrypted_body"]),
            )
            for r in rows
        ]


def _row_to_note(row: sqlite3.Row) -> Note:
    kind = NoteKind(row["kind"])
    common = dict(
        id=UUID(row["id"]),
        title=row["title"],
        body=row["body"],
        kind=kind,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row["deleted_at"],
    )
    if kind is NoteKind.SECURE:
        return SecureNote(
            **common,
            salt=bytes(row["salt"]),
            encrypted_body=bytes(row["encrypted_body"]),
            passphrase_hash=bytes(row["passphrase_hash"]),
        )
    return Note(**common)


def _to_fts_match(query: str) -> str:
    """Build a safe FTS5 MATCH expression from free-text input.

    Each whitespace-separated term is double-quoted (so punctuation can't be parsed as
    FTS operators) and given a prefix ``*`` for partial matches. Terms are ANDed.
    """
    terms = [t for t in query.strip().split() if t]
    if not terms:
        return ""
    quoted = ['"' + t.replace('"', '""') + '"*' for t in terms]
    return " ".join(quoted)
