"""Central application configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_DIR = PROJECT_ROOT / "workspace"
REPOSITORIES_DIR = WORKSPACE_DIR / "repositories"
INDEXES_DIR = WORKSPACE_DIR / "indexes"


def initialize_workspace() -> None:
    """Create required runtime directories."""
    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
    INDEXES_DIR.mkdir(parents=True, exist_ok=True)
