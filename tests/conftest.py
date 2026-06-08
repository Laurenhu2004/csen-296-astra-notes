"""Shared pytest fixtures.

Every test runs against an isolated temporary ASTRANOTES_HOME so suites never touch a
real user's notes (FR-5 isolation) and integration tests exercise a *real* SQLite store
on tmp_path rather than a mock (shift-left testing policy: don't mock the layer under test).
``config.data_home()`` reads the env var on each call, so setting it per-test is enough.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from astranotes.app import AppContext, build_app
from astranotes.config import ENV_HOME, Settings


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(ENV_HOME, str(tmp_path))
    return tmp_path


@pytest.fixture
def app(home: Path) -> Iterator[AppContext]:
    yield build_app(Settings.load())
