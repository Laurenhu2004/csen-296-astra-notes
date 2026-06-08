"""Phase-1 CLI shell (View).

A thin ``cmd``-based front end. It reaches the system only through ``NoteService`` (and
reads the plugin/sync handles handed to it by the composition root); it imports nothing
from ``repository`` or ``services.encryption`` (NFR-2 / SEC-1). User-facing errors show a
short message; full tracebacks are never printed (SEC-2).
"""

from __future__ import annotations

import cmd
from uuid import UUID

from ..app import AppContext
from ..errors import AstraNotesError
from ..models.note import Note, NoteKind, SecureNote

BANNER = r"""
   _        _              _   _       _
  /_\   ___| |_ _ __ __ _ | \ | | ___ | |_ ___  ___
 //_\\ / __| __| '__/ _` ||  \| |/ _ \| __/ _ \/ __|
/  _  \\__ \ |_| | | (_| || |\  | (_) | ||  __/\__ \
\_/ \_/|___/\__|_|  \__,_||_| \_|\___/ \__\___||___/

  local-first, encrypted notes  ·  type `help` for commands
"""


class AstraShell(cmd.Cmd):
    intro = BANNER
    prompt = "astra> "

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._notes = ctx.notes
        for warning in ctx.plugins.warnings:
            print(f"[plugin warning] {warning}")

    # ---- helpers -------------------------------------------------------------

    def _resolve(self, prefix: str) -> UUID | None:
        """Resolve a short id prefix (as shown by `list`) to a full note id."""
        prefix = prefix.strip().lower()
        if not prefix:
            print("Please supply a note id (see `list`).")
            return None
        matches = [
            n for n in self._notes.list() + self._notes.list_trash()
            if str(n.id).lower().startswith(prefix)
        ]
        if not matches:
            print(f"No note matches id '{prefix}'.")
            return None
        if len(matches) > 1:
            print(f"Ambiguous id '{prefix}' — matches {len(matches)} notes. Use more characters.")
            return None
        return matches[0].id

    @staticmethod
    def _print_table(rows: list[Note]) -> None:
        if not rows:
            print("(no notes — try `new`)")
            return
        print(f"{'ID':<10} {'Updated':<22} {'Kind':<7} Title")
        print("-" * 70)
        for n in rows:
            short_id = str(n.id)[:8]
            lock = " 🔒" if isinstance(n, SecureNote) else ""
            title = (n.title[:45] + "…") if len(n.title) > 46 else n.title
            print(f"{short_id:<10} {n.updated_at:<22} {n.kind.value:<7} {title}{lock}")

    def _read_body(self) -> str:
        print("Body (finish with a single '.' on its own line):")
        lines: list[str] = []
        while True:
            line = input()
            if line == ".":
                break
            lines.append(line)
        return "\n".join(lines)

    # ---- commands ------------------------------------------------------------

    def do_new(self, arg: str) -> None:
        """new — create a text note (FR-1)."""
        title = input("Title: ").strip()
        body = self._read_body()
        try:
            note = self._notes.create(title=title, body=body)
        except AstraNotesError as exc:
            print(f"Could not save: {exc}")
            return
        print(f"Saved note {str(note.id)[:8]}.")

    def do_list(self, arg: str) -> None:
        """list — list all notes, newest first (FR-1/FR-5)."""
        self._print_table(self._notes.list())

    def do_view(self, arg: str) -> None:
        """view <id> — show a note's body (locked notes show only a hint)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        note = self._notes.get(note_id)
        print(f"\n# {note.title}  ({note.kind.value})")
        print(f"updated: {note.updated_at}\n")
        if isinstance(note, SecureNote):
            print("🔒 This note is private. Use `unlock <id>` to read it.")
        else:
            print(note.body or "(empty)")
        print()

    def do_edit(self, arg: str) -> None:
        """edit <id> — change a note's title and/or body (FR-2)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        note = self._notes.get(note_id)
        new_title = input(f"Title [{note.title}]: ").strip() or None
        print("Enter a new body, or just '.' to keep the current one.")
        body = self._read_body()
        new_body = body if body.strip() else None
        try:
            self._notes.edit(note_id, title=new_title, body=new_body)
        except AstraNotesError as exc:
            print(f"Could not edit: {exc}")
            return
        print("Updated.")

    def do_delete(self, arg: str) -> None:
        """delete <id> — move a note to trash (recoverable >= 7 days) (FR-3)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        self._notes.delete(note_id)
        print("Moved to trash. Use `trash` then `restore <id>` to recover.")

    def do_trash(self, arg: str) -> None:
        """trash — list notes currently in the trash (FR-3)."""
        self._print_table(self._notes.list_trash())

    def do_restore(self, arg: str) -> None:
        """restore <id> — bring a note back from the trash (FR-3)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        self._notes.restore_from_trash(note_id)
        print("Restored from trash.")

    def do_secure(self, arg: str) -> None:
        """secure <id> — encrypt a note's body with a passphrase (FR-4 / SEC-1)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        passphrase = input("Passphrase (>= 12 chars): ")
        try:
            self._notes.make_secure(note_id, passphrase)
        except AstraNotesError as exc:
            print(f"Could not secure: {exc}")
            return
        print("Note is now private. Its body is encrypted at rest.")

    def do_unlock(self, arg: str) -> None:
        """unlock <id> — decrypt and display a private note (FR-4)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        passphrase = input("Passphrase: ")
        try:
            body = self._notes.unlock(note_id, passphrase)
        except AstraNotesError as exc:
            print(f"Unlock failed: {exc}")
            return
        print("\n--- decrypted body ---")
        print(body or "(empty)")
        print("----------------------\n")

    def do_search(self, arg: str) -> None:
        """search <query> — full-text search by title/body, ranked by recency (FR-8)."""
        results = self._notes.search(arg)
        print(f"{len(results)} result(s):")
        self._print_table(results)

    def do_history(self, arg: str) -> None:
        """history <id> — list a note's version history (FR-6)."""
        note_id = self._resolve(arg)
        if note_id is None:
            return
        entries = self._notes.history(note_id)
        if not entries:
            print("(no history)")
            return
        for e in entries:
            preview = e.body_snapshot.replace("\n", " ")[:50] if e.body_snapshot else "(encrypted)"
            print(f"  v{e.version:<3} {e.changed_at}  {preview}")
        print("Use `revert <id> <version>` to restore one.")

    def do_revert(self, arg: str) -> None:
        """revert <id> <version> — restore a prior version (appends, FR-6)."""
        parts = arg.split()
        if len(parts) != 2 or not parts[1].isdigit():
            print("Usage: revert <id> <version>")
            return
        note_id = self._resolve(parts[0])
        if note_id is None:
            return
        try:
            self._notes.restore_version(note_id, int(parts[1]))
        except AstraNotesError as exc:
            print(f"Could not revert: {exc}")
            return
        print(f"Reverted to v{parts[1]} (recorded as a new version).")

    def do_plugins(self, arg: str) -> None:
        """plugins — list available note-kind handlers (US-6)."""
        print("Available note kinds:", ", ".join(self._ctx.plugins.available_kinds()))

    def do_sync(self, arg: str) -> None:
        """sync — run Cloud Sync if enabled (FR-7, Phase-1 stub)."""
        report = self._ctx.sync.sync_now()
        print(report.message)

    def do_quit(self, arg: str) -> bool:
        """quit — exit AstraNotes."""
        print("Goodbye.")
        return True

    do_EOF = do_quit

    def default(self, line: str) -> None:
        print(f"Unknown command: {line!r}. Type `help`.")


def run_cli(ctx: AppContext) -> int:
    try:
        AstraShell(ctx).cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye.")
    return 0


__all__ = ["run_cli", "AstraShell", "NoteKind"]
