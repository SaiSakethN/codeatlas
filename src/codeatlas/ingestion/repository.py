"""Repository ingestion and workspace management."""

import hashlib
import os
import re
import shutil
import subprocess
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
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth=1",
                    "--no-tags",
                    "--",
                    canonical_url,
                    str(destination),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )

        except subprocess.TimeoutExpired as exc:
            shutil.rmtree(destination, ignore_errors=True)
            raise RuntimeError("Repository cloning timed out.") from exc

        except subprocess.CalledProcessError as exc:
            shutil.rmtree(destination, ignore_errors=True)
            raise RuntimeError(f"Repository cloning failed: {exc.stderr}") from exc

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
