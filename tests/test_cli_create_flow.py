"""T-4 — end-to-end CLI smoke test. Traces: FR-1, FR-5, NFR-2.

Drives the real `python -m astranotes` process over stdin (subprocess), proving the
package runs as a module and the create -> list flow works through the View.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(home: Path, script: str) -> str:
    src = Path(__file__).resolve().parents[1] / "src"
    env = {"ASTRANOTES_HOME": str(home), "PYTHONPATH": str(src)}
    proc = subprocess.run(
        [sys.executable, "-m", "astranotes"],
        input=script,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    return proc.stdout


def test_cli_new_then_list(tmp_path: Path) -> None:
    script = "new\nMy First Note\nhello body\n.\nlist\nquit\n"
    out = _run(tmp_path, script)
    assert "Saved note" in out
    assert "My First Note" in out


def test_cli_persists_across_runs(tmp_path: Path) -> None:
    _run(tmp_path, "new\nPersisted Note\nbody\n.\nquit\n")
    out = _run(tmp_path, "list\nquit\n")  # fresh process, same store (FR-5)
    assert "Persisted Note" in out
