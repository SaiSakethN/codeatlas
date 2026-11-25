"""Real repository intelligence integration test."""

import time

from codeatlas.indexing.pipeline import index_repository
from codeatlas.ingestion.repository import clone_repository
from codeatlas.retrieval.hybrid import HybridRetriever
from codeatlas.tools.registry import ToolRegistry
from codeatlas.tools.repository_tools import RepositoryTools


def progress(current, total):
    print(
        f"\rIndexing: {current}/{total} ({current / total:.1%})",
        end="",
        flush=True,
    )


def main():
    start = time.perf_counter()

    repository = clone_repository("https://github.com/psf/requests")

    print("Repository:", repository.name)

    store, stats = index_repository(
        repository,
        progress_callback=progress,
    )

    print("\nIndexing statistics:")

    for key, value in stats.items():
        print(f"{key}: {value}")

    retriever = HybridRetriever(store)

    tools = RepositoryTools(
        repository,
        retriever,
    )

    registry = ToolRegistry(tools)

    print("\nSymbol search:")

    results = registry.execute(
        "find_symbol",
        {"symbol_name": "HTTPAdapter"},
    )

    for result in results:
        print(result)

    print("\nHybrid retrieval:")

    results = registry.execute(
        "semantic_search",
        {
            "query": "How does Requests handle HTTP retries?",
            "top_k": 3,
        },
    )

    for result in results:
        print(
            result["file_path"],
            result["symbol_name"],
            result["start_line"],
            result["end_line"],
        )

    print("\nAvailable tools:", len(registry.schemas()))

    print(
        "Total execution time:",
        round(time.perf_counter() - start, 2),
        "seconds",
    )


if __name__ == "__main__":
    main()
