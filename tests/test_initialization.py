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


def test_installed_runtime_workspace_override(tmp_path):
    import os
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from codeatlas.config import WORKSPACE_DIR, initialize_workspace; "
                "initialize_workspace(); print(WORKSPACE_DIR)"
            ),
        ],
        env={**os.environ, "CODEATLAS_WORKSPACE_DIR": str(tmp_path)},
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == str(tmp_path)
    assert (tmp_path / "indexes").is_dir()
