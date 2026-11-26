"""Persistent repository catalog and bounded single-worker indexing jobs."""

import json
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

from codeatlas.config import WORKSPACE_DIR, settings
from codeatlas.indexing.pipeline import get_repository_id, index_repository
from codeatlas.indexing.vector_store import VectorStore
from codeatlas.ingestion.repository import clone_repository
from codeatlas.models import Repository


class RepositoryService:
    def __init__(self, catalog: Path | None = None):
        self.catalog = catalog or WORKSPACE_DIR / "catalog.json"
        self.lock = threading.RLock()
        self.compute = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="index")
        self.jobs: dict[str, dict] = {}
        self.records: dict[str, dict] = {}
        if self.catalog.exists():
            self.records = json.loads(self.catalog.read_text(encoding="utf-8"))

    def save(self):
        self.catalog.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.catalog.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.records), encoding="utf-8")
        temporary.replace(self.catalog)

    def list(self):
        with self.lock:
            return [{k: v for k, v in r.items() if k != "path"} for r in self.records.values()]

    def repository(self, identifier: str):
        with self.lock:
            record = self.records[identifier]
            return Repository(record["name"], Path(record["path"]), record["source"])

    def submit(self, url: str):
        with self.lock:
            if any(j["status"] in {"queued", "indexing"} for j in self.jobs.values()):
                raise RuntimeError("An indexing job is already running.")
            if len(self.records) >= settings.max_repositories:
                raise RuntimeError("Repository limit reached. Remove a repository first.")
            identifier = uuid.uuid4().hex
            # Bound retained job history as well as queued work.
            if len(self.jobs) >= 100:
                self.jobs.pop(next(iter(self.jobs)))
            self.jobs[identifier] = {"id": identifier, "status": "queued", "progress": 0}
            self.executor.submit(self.run, identifier, url)
            return dict(self.jobs[identifier])

    def update(self, identifier, **values):
        with self.lock:
            self.jobs[identifier].update(values)

    def run(self, identifier: str, url: str):
        phase = "preflight"
        try:
            self.update(identifier, status="indexing")
            with self.compute:
                self.preflight(url)
                phase = "clone"
                repository = clone_repository(url)
                phase = "index"
                _, statistics = index_repository(
                    repository,
                    progress_callback=lambda done, total: self.update(
                        identifier, progress=round(done / total * 100)
                    ),
                )
                repository_id = get_repository_id(repository)
                phase = "catalog"
                with self.lock:
                    self.records[repository_id] = {
                        "id": repository_id,
                        "name": repository.name,
                        "source": repository.source,
                        "path": str(repository.path),
                        "statistics": statistics,
                    }
                    self.save()
            self.update(identifier, status="completed", progress=100, repository_id=repository_id)
        except Exception as exc:
            # Provider and Git exceptions can contain credentials or local paths.
            logging.getLogger(__name__).error(
                "Repository job failed: phase=%s exception_type=%s", phase, type(exc).__name__
            )
            messages = {
                "preflight": (
                    "GitHub could not approve this import. "
                    "Check public access, repository size, and GitHub rate limits."
                ),
                "clone": "GitHub cloning failed or timed out. Check the repository URL and retry.",
                "index": (
                    "Embedding or indexing failed. "
                    "Check the backend logs for its failure stage, then retry the import."
                ),
                "catalog": "The index could not be saved. Check the writable data directory.",
            }
            self.update(
                identifier,
                status="failed",
                error=messages[phase],
                error_code=f"{phase}_failed",
            )

    def preflight(self, url: str):
        slug = url.removeprefix("https://github.com/").removesuffix(".git")
        response = httpx.get(
            f"https://api.github.com/repos/{slug}",
            timeout=15,
            headers={"Accept": "application/vnd.github+json"},
            follow_redirects=False,
        )
        response.raise_for_status()
        metadata = response.json()
        if metadata.get("private") or metadata.get("size", 0) > settings.max_repository_size_kb:
            raise ValueError("Repository is private or exceeds the configured size limit.")

    def remove(self, identifier: str):
        with self.lock:
            self.repository(identifier)
            VectorStore(identifier).reset()
            del self.records[identifier]
            self.save()
        # Clones are retained as a local cache; never recursively delete a user path.
