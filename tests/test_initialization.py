from codeatlas import __version__
from codeatlas.config import (
    INDEXES_DIR,
    PROJECT_ROOT,
    REPOSITORIES_DIR,
    initialize_workspace,
)


def test_package_version():
    assert __version__ == "0.1.0"


def test_project_root():
    assert PROJECT_ROOT.name == "codeatlas"
    assert (PROJECT_ROOT / "pyproject.toml").exists()


def test_workspace_initialization():
    initialize_workspace()

    assert REPOSITORIES_DIR.is_dir()
    assert INDEXES_DIR.is_dir()
