"""Repository processing and indexing pipeline."""

import hashlib

from codeatlas.config import settings
from codeatlas.indexing.vector_store import VectorStore
from codeatlas.ingestion.explorer import discover_python_files
from codeatlas.models import Repository
from codeatlas.parsing.chunker import create_chunks
from codeatlas.parsing.parser import parse_python_file


def get_repository_id(repository: Repository) -> str:
    return hashlib.sha256(repository.source.encode()).hexdigest()


def index_repository(
    repository: Repository,
    rebuild: bool = False,
    progress_callback=None,
    provider=None,
):
    repository_id = get_repository_id(repository)

    store = VectorStore(
        repository_id,
        provider=provider,
    )

    if store.count() and not rebuild:
        return store, {
            "repository": repository.name,
            "repository_id": repository_id,
            "chunks": store.count(),
            "cached": True,
        }

    files = discover_python_files(repository.path)

    if sum(path.stat().st_size for path in files) > settings.max_source_bytes:
        raise ValueError("Repository exceeds the source size budget.")

    chunks = []
    failed_files = []
    symbol_count = 0

    for path in files:
        try:
            parsed = parse_python_file(
                path,
                repository.path,
            )

            symbol_count += len(parsed.symbols)

            chunks.extend(create_chunks(parsed, repository_id))

        except (
            SyntaxError,
            UnicodeError,
            OSError,
            ValueError,
        ):
            failed_files.append(path.relative_to(repository.path).as_posix())

        if len(chunks) > settings.max_index_chunks:
            raise ValueError("Repository exceeds the index chunk budget.")

    if not chunks:
        raise ValueError("No indexable Python code found.")

    store.reset()

    try:
        for start in range(0, len(chunks), 16):
            batch = chunks[start : start + 16]

            store.add_chunks(batch)

            if progress_callback:
                progress_callback(
                    start + len(batch),
                    len(chunks),
                )

    except Exception:
        store.reset()
        raise

    return store, {
        "repository": repository.name,
        "repository_id": repository_id,
        "python_files": len(files),
        "symbols": symbol_count,
        "chunks": store.count(),
        "failed_files": failed_files,
        "cached": False,
    }
