"""Entry point: ``python -m astranotes`` (CLI) or ``python -m astranotes --gui`` (Tkinter).

Both surfaces are built over the same NoteService composed in app.build_app(), which is
the Phase-1 → Phase-2 "swap the View only" story from the design.
"""

from __future__ import annotations

import argparse
import sys

from .app import build_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="astranotes",
        description="AstraNotes — local-first, encrypted note-taking.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Tkinter GUI (Phase 2) instead of the CLI (Phase 1).",
    )
    args = parser.parse_args(argv)

    ctx = build_app()

    if args.gui:
        from .view.gui import run_gui

        return run_gui(ctx)

    from .view.cli import run_cli

    return run_cli(ctx)


if __name__ == "__main__":
    sys.exit(main())
