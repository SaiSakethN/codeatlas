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
