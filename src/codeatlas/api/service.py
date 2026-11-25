"""Persistent repository catalog and bounded single-worker indexing jobs."""

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
        try:
            self.update(identifier, status="indexing")
            with self.compute:
                repository = clone_repository(url)
                _, statistics = index_repository(
                    repository,
                    progress_callback=lambda done, total: self.update(
                        identifier, progress=round(done / total * 100)
                    ),
                )
                repository_id = get_repository_id(repository)
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
        except Exception:
            # Provider and Git exceptions can contain credentials or local paths.
            self.update(
                identifier,
                status="failed",
                error="Import failed. Check repository availability and provider readiness.",
            )

    def remove(self, identifier: str):
        with self.lock:
            self.repository(identifier)
            VectorStore(identifier).reset()
            del self.records[identifier]
            self.save()
        # Clones are retained as a local cache; never recursively delete a user path.
