"""Composition root.

This is the one place that knows about every concrete service and wires them together.
Views receive only a ready-built ``NoteService`` (and a plugin list for the menu), so
they never import the repository or encryption modules themselves (NFR-2).
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .plugins.manager import PluginManager
from .repository.sqlite_repo import LocalSQLiteRepository
from .services.audit_log import AuditLogService
from .services.encryption import EncryptionService
from .services.note_service import NoteService
from .services.sync import SyncService
from .services.validation import ValidationService
from .services.version_history import VersionHistoryService


@dataclass
class AppContext:
    """Everything a View needs, with the wiring already done."""

    notes: NoteService
    plugins: PluginManager
    sync: SyncService
    settings: Settings


def build_app(settings: Settings | None = None) -> AppContext:
    settings = settings or Settings.load()

    repo = LocalSQLiteRepository(settings.store_path)
    validator = ValidationService()
    audit = AuditLogService(settings.audit_log_path)
    encryption = EncryptionService(settings.kdf_params)
    version = VersionHistoryService(repo)

    notes = NoteService(
        repo=repo,
        validator=validator,
        audit=audit,
        encryption=encryption,
        version=version,
        settings=settings,
    )

    plugins = PluginManager()
    plugins.discover(settings.plugins_dir)

    sync = SyncService(enabled=settings.sync_enabled)

    # Housekeeping on startup: empty the trash of anything past its retention window.
    notes.purge_expired()

    return AppContext(notes=notes, plugins=plugins, sync=sync, settings=settings)
