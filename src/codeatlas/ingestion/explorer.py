"""Discover supported source files."""

import os
from pathlib import Path

from codeatlas.config import settings

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    ".pytest_cache",
    ".ruff_cache",
    "site-packages",
    "workspace",
}

MAX_FILE_SIZE = 500_000
MAX_FILES = 2_000


def discover_python_files(root: Path) -> list[Path]:
    """Discover Python files without following symbolic links."""

    root = root.resolve()
    files = []

    for directory, subdirectories, filenames in os.walk(root, followlinks=False):
        current = Path(directory)

        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if name not in IGNORED_DIRECTORIES
            and not name.startswith(".")
            and not (current / name).is_symlink()
        )

        for filename in sorted(filenames):
            path = current / filename

            if path.suffix != ".py" or path.is_symlink():
                continue

            try:
                if not path.resolve().is_relative_to(root):
                    continue

                if path.stat().st_size > min(MAX_FILE_SIZE, settings.max_file_size):
                    continue

                files.append(path)

            except OSError:
                continue

            if len(files) >= min(MAX_FILES, settings.max_repository_files):
                return files

    return files
