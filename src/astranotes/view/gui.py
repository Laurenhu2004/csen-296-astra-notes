"""Phase-2 Tkinter GUI (View).

Demonstrates the design's "swap the View only" promise: this window is built over the
exact same ``NoteService`` the CLI uses, and like the CLI it imports nothing from
``repository`` or ``services.encryption`` (NFR-2 / SEC-1).

Layout: a searchable note list on the left, a title+body editor on the right, and a
toolbar for new / save / secure / unlock / history / delete.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from uuid import UUID

from ..app import AppContext
from ..errors import AstraNotesError
from ..models.note import Note, SecureNote


class AstraGUI:
    def __init__(self, ctx: AppContext) -> None:
        self._notes = ctx.notes
        self._ctx = ctx
        self._rows: list[Note] = []
        self._current: UUID | None = None

        self.root = tk.Tk()
        self.root.title("AstraNotes")
        self.root.geometry("860x560")
        self._build()
        self._refresh()

    # ---- layout --------------------------------------------------------------

    def _build(self) -> None:
        # Toolbar
        bar = ttk.Frame(self.root, padding=6)
        bar.pack(side=tk.TOP, fill=tk.X)
        for label, cmd in [
            ("New", self._new),
            ("Save", self._save),
            ("Secure", self._secure),
            ("Unlock", self._unlock),
            ("History", self._history),
            ("Delete", self._delete),
        ]:
            ttk.Button(bar, text=label, command=cmd).pack(side=tk.LEFT, padx=2)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh())
        ttk.Label(bar, text="Search:").pack(side=tk.LEFT, padx=(16, 2))
        ttk.Entry(bar, textvariable=self._search_var, width=24).pack(side=tk.LEFT)

        # Body split: list (left) + editor (right)
        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body, padding=6)
        left.pack(side=tk.LEFT, fill=tk.Y)
        self._listbox = tk.Listbox(left, width=34, height=28)
        self._listbox.pack(fill=tk.Y, expand=True)
        self._listbox.bind("<<ListboxSelect>>", lambda _e: self._select())

        right = ttk.Frame(body, padding=6)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text="Title").pack(anchor=tk.W)
        self._title_var = tk.StringVar()
        ttk.Entry(right, textvariable=self._title_var).pack(fill=tk.X)
        ttk.Label(right, text="Body").pack(anchor=tk.W, pady=(8, 0))
        self._body = tk.Text(right, wrap=tk.WORD)
        self._body.pack(fill=tk.BOTH, expand=True)

        self._status = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self._status, relief=tk.SUNKEN, anchor=tk.W).pack(
            side=tk.BOTTOM, fill=tk.X
        )

    # ---- data binding --------------------------------------------------------

    def _refresh(self) -> None:
        query = self._search_var.get().strip()
        self._rows = self._notes.search(query) if query else self._notes.list()
        self._listbox.delete(0, tk.END)
        for n in self._rows:
            lock = " 🔒" if isinstance(n, SecureNote) else ""
            self._listbox.insert(tk.END, f"{n.title}{lock}")

    def _select(self) -> None:
        sel = self._listbox.curselection()
        if not sel:
            return
        note = self._rows[sel[0]]
        self._current = note.id
        self._title_var.set(note.title)
        self._body.delete("1.0", tk.END)
        if isinstance(note, SecureNote):
            self._body.insert("1.0", "🔒 Private note — click Unlock to read.")
        else:
            self._body.insert("1.0", note.body)

    def _editor_text(self) -> tuple[str, str]:
        return self._title_var.get().strip(), self._body.get("1.0", tk.END).rstrip("\n")

    # ---- actions -------------------------------------------------------------

    def _new(self) -> None:
        self._current = None
        self._title_var.set("")
        self._body.delete("1.0", tk.END)
        self._status.set("New note — type a title and body, then Save.")

    def _save(self) -> None:
        title, body = self._editor_text()
        try:
            if self._current is None:
                note = self._notes.create(title=title, body=body)
                self._current = note.id
                self._status.set("Created.")
            else:
                self._notes.edit(self._current, title=title, body=body)
                self._status.set("Saved.")
        except AstraNotesError as exc:
            messagebox.showerror("AstraNotes", str(exc))
            return
        self._refresh()

    def _secure(self) -> None:
        if not self._require_current():
            return
        passphrase = simpledialog.askstring(
            "Secure note", "Passphrase (>= 12 chars):", show="*", parent=self.root
        )
        if not passphrase:
            return
        try:
            self._notes.make_secure(self._current, passphrase)  # type: ignore[arg-type]
        except AstraNotesError as exc:
            messagebox.showerror("AstraNotes", str(exc))
            return
        self._status.set("Note encrypted at rest.")
        self._refresh()

    def _unlock(self) -> None:
        if not self._require_current():
            return
        passphrase = simpledialog.askstring(
            "Unlock note", "Passphrase:", show="*", parent=self.root
        )
        if not passphrase:
            return
        try:
            plaintext = self._notes.unlock(self._current, passphrase)  # type: ignore[arg-type]
        except AstraNotesError as exc:
            messagebox.showerror("AstraNotes", str(exc))
            return
        self._body.delete("1.0", tk.END)
        self._body.insert("1.0", plaintext)
        self._status.set("Unlocked (in memory only).")

    def _history(self) -> None:
        if not self._require_current():
            return
        entries = self._notes.history(self._current)  # type: ignore[arg-type]
        lines = [
            f"v{e.version}  {e.changed_at}  "
            f"{(e.body_snapshot[:40] if e.body_snapshot else '(encrypted)')}"
            for e in entries
        ]
        messagebox.showinfo("Version history", "\n".join(lines) or "(no history)")

    def _delete(self) -> None:
        if not self._require_current():
            return
        self._notes.delete(self._current)  # type: ignore[arg-type]
        self._current = None
        self._new()
        self._status.set("Moved to trash.")
        self._refresh()

    def _require_current(self) -> bool:
        if self._current is None:
            messagebox.showinfo("AstraNotes", "Select or save a note first.")
            return False
        return True

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_gui(ctx: AppContext) -> int:
    return AstraGUI(ctx).run()
