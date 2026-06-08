"""Synthetic note generator for the NFR-1 performance spike (S0-11).

Usage:
    PYTHONPATH=src python tools/seed.py 10000

Generates N pseudo-random notes directly through the repository (fast bulk path) so the
search-latency spike can be reproduced against a realistic store.
"""

from __future__ import annotations

import random
import sys

from astranotes.config import Settings
from astranotes.models.note import Note
from astranotes.repository.sqlite_repo import LocalSQLiteRepository

_WORDS = (
    "alpha roadmap meeting budget design review sprint retro backlog spike encryption "
    "search sqlite note secure version history sync plugin audit validation latency "
    "quarterly planning standup demo refactor traceability requirement architecture"
).split()


def _sentence(rng: random.Random, n: int = 12) -> str:
    return " ".join(rng.choice(_WORDS) for _ in range(n))


def seed(repo: LocalSQLiteRepository, count: int, seed_value: int = 42) -> None:
    rng = random.Random(seed_value)
    for i in range(count):
        note = Note.new(title=f"Note {i} {rng.choice(_WORDS)}", body=_sentence(rng, 24))
        repo.save(note)


def main(argv: list[str]) -> int:
    count = int(argv[1]) if len(argv) > 1 else 10_000
    repo = LocalSQLiteRepository(Settings.load().store_path)
    print(f"Seeding {count} notes into {Settings.load().store_path} ...")
    seed(repo, count)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
