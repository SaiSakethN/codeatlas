"""Repository ingestion and workspace management."""

import hashlib
import re
from pathlib import Path

from git import Repo

from codeatlas.config import REPOSITORIES_DIR
from codeatlas.models import Repository


def clone_repository(url: str) -> Repository:
    """Clone a public GitHub repository."""

    pattern = (
        r"https://github\.com/"
        r"([A-Za-z0-9_.-]+)/"
        r"([A-Za-z0-9_.-]+)/?"
    )

    match = re.fullmatch(pattern, url.strip())

    if not match:
        raise ValueError("Provide a valid HTTPS GitHub repository URL.")

    owner, name = match.groups()
    name = name.removesuffix(".git")

    if owner in {".", ".."} or name in {"", ".", ".."}:
        raise ValueError("Invalid repository name.")

    canonical_url = f"https://github.com/{owner}/{name}.git"
    identifier = hashlib.sha256(canonical_url.encode()).hexdigest()[:12]

    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)

    destination = REPOSITORIES_DIR / f"{identifier}-{name}"

    if destination.is_symlink():
        raise ValueError("Invalid repository destination.")

    if not destination.exists():
        Repo.clone_from(
            canonical_url,
            destination,
            depth=1,
            multi_options=["--no-tags"],
            env={"GIT_TERMINAL_PROMPT": "0"},
            kill_after_timeout=120,
        )
    else:
        existing = Repo(destination)

        if existing.remotes.origin.url != canonical_url:
            raise ValueError("Repository origin mismatch.")

    return Repository(
        name=name,
        path=destination.resolve(),
        source=canonical_url,
    )


def load_local_repository(path: str) -> Repository:
    """Load an existing local directory."""

    directory = Path(path).expanduser().resolve()

    if not directory.is_dir():
        raise ValueError(f"Directory does not exist: {directory}")

    return Repository(
        name=directory.name,
        path=directory,
        source=str(directory),
    )
