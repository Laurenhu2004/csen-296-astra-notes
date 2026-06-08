"""Runtime configuration and on-disk paths.

The data directory defaults to ``~/AstraNotes`` but is overridable via the
``ASTRANOTES_HOME`` environment variable. Tests and the seed tool point this at a
temporary directory so they never collide with a real user's notes.

Settings persist to ``<home>/settings.json`` (created with defaults on first run).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

ENV_HOME = "ASTRANOTES_HOME"


def data_home() -> Path:
    """Resolve the AstraNotes data directory, creating it if needed."""
    raw = os.environ.get(ENV_HOME) or "~/AstraNotes"
    home = Path(raw).expanduser()
    home.mkdir(parents=True, exist_ok=True)
    return home


@dataclass
class Settings:
    """User-tunable settings, persisted as JSON in the data home."""

    trash_retention_days: int = 7
    sync_enabled: bool = False
    # scrypt KDF parameters for SecureNote key derivation (SEC-1). Memory-hard.
    kdf_params: dict[str, int] = field(default_factory=lambda: {"n": 32768, "r": 8, "p": 1})
    max_unlock_attempts: int = 3

    @property
    def store_path(self) -> Path:
        return data_home() / "store.db"

    @property
    def audit_log_path(self) -> Path:
        return data_home() / "audit.log"

    @property
    def debug_log_path(self) -> Path:
        return data_home() / "debug.log"

    @property
    def plugins_dir(self) -> Path:
        d = data_home() / "plugins"
        d.mkdir(exist_ok=True)
        return d

    @classmethod
    def load(cls) -> Settings:
        """Load settings.json, writing defaults if the file is absent."""
        path = data_home() / "settings.json"
        if not path.exists():
            settings = cls()
            settings.save()
            return settings
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {f for f in cls().__dict__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self) -> None:
        path = data_home() / "settings.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
