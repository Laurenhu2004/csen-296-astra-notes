"""NFR-1 / Sprint-Zero spike S0-11 — search latency at scale.

Seeds 10,000 notes into a real SQLite+FTS5 store and asserts the p95 search latency
stays under the 100 ms target. Kept out of the default unit/integration runs (it is
slower); run explicitly with `pytest tests/perf`.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from astranotes.config import ENV_HOME, Settings
from astranotes.repository.sqlite_repo import LocalSQLiteRepository

N_NOTES = 10_000
P95_BUDGET_MS = 100.0


@pytest.fixture
def big_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalSQLiteRepository:
    monkeypatch.setenv(ENV_HOME, str(tmp_path))
    from tools.seed import seed  # local import so the tool ships with the repo

    repo = LocalSQLiteRepository(Settings.load().store_path)
    seed(repo, N_NOTES)
    return repo


def test_search_p95_under_budget(big_store: LocalSQLiteRepository) -> None:
    samples_ms: list[float] = []
    for term in ["alpha", "roadmap", "meeting", "budget", "design", "review"] * 10:
        start = time.perf_counter()
        big_store.search(term)
        samples_ms.append((time.perf_counter() - start) * 1000)
    samples_ms.sort()
    p95 = samples_ms[int(len(samples_ms) * 0.95)]
    assert p95 < P95_BUDGET_MS, f"p95 {p95:.1f}ms exceeds {P95_BUDGET_MS}ms budget (NFR-1)"
