import pytest

from codeatlas.ingestion.explorer import discover_python_files
from codeatlas.ingestion.repository import (
    clone_repository,
    load_local_repository,
)


def test_load_local_repository(tmp_path):
    repository = load_local_repository(str(tmp_path))

    assert repository.path == tmp_path.resolve()


def test_invalid_repository_url():
    with pytest.raises(ValueError):
        clone_repository("https://example.com/repository")


def test_discover_python_files(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("Example")

    ignored = tmp_path / ".venv"
    ignored.mkdir()
    (ignored / "hidden.py").write_text("pass")

    files = discover_python_files(tmp_path)

    assert len(files) == 1
    assert files[0].name == "main.py"


def test_invalid_local_directory(tmp_path):
    with pytest.raises(ValueError):
        load_local_repository(str(tmp_path / "missing"))


def test_clone_repository_uses_subprocess(tmp_path, monkeypatch):
    from codeatlas.ingestion import repository

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr(repository, "REPOSITORIES_DIR", tmp_path)

    monkeypatch.setattr(repository.subprocess, "run", fake_run)

    result = repository.clone_repository("https://github.com/psf/requests")

    assert result.name == "requests"
    assert len(calls) == 1

    command, options = calls[0]

    assert command[:2] == ["git", "clone"]
    assert "--depth=1" in command
    assert options["timeout"] == 120
    assert options["check"] is True
