"""Ensure local startup applies repository migrations before serving."""

from contextlib import nullcontext
from pathlib import Path

import pytest
import run as backend_run


class StubApp:
    """Minimal Flask-like app that records startup calls without a database."""

    def __init__(self, events):
        self.events = events
        self.config = {"ENV": "development"}

    def app_context(self):
        return nullcontext()

    def run(self, **kwargs):
        self.events.append(("run", kwargs))


def test_main_upgrades_repository_migrations_before_starting_server(monkeypatch):
    events = []
    app = StubApp(events)
    monkeypatch.setattr(backend_run, "create_app", lambda: app)
    monkeypatch.setattr(backend_run, "upgrade", lambda directory: events.append(("upgrade", directory)))

    backend_run.main()

    assert events == [
        ("upgrade", str(Path(backend_run.__file__).resolve().parent / "migrations")),
        ("run", {"host": "0.0.0.0", "static_files": "static", "port": 5000, "debug": True}),
    ]


def test_migration_failure_prevents_server_start(monkeypatch):
    events = []
    app = StubApp(events)

    def fail_upgrade(directory):
        events.append(("upgrade", directory))
        raise RuntimeError("migration failed")

    monkeypatch.setattr(backend_run, "create_app", lambda: app)
    monkeypatch.setattr(backend_run, "upgrade", fail_upgrade)

    with pytest.raises(RuntimeError, match="migration failed"):
        backend_run.main()

    assert len(events) == 1
    assert events[0][0] == "upgrade"


def test_production_environment_refuses_local_startup_migration(monkeypatch):
    events = []
    app = StubApp(events)
    app.config["ENV"] = "production"
    monkeypatch.setattr(backend_run, "create_app", lambda: app)

    with pytest.raises(RuntimeError, match="Refusing local startup migrations in production"):
        backend_run.main()

    assert events == []
