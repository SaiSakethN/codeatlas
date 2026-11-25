"""Real-model verification of CodeAtlas investigations."""

import json

from codeatlas.agents.service import CodeAtlasAgent
from codeatlas.indexing.pipeline import index_repository
from codeatlas.ingestion.repository import clone_repository
from codeatlas.llm.factory import get_ai_provider
from codeatlas.rag import CodeRAG
from codeatlas.retrieval.hybrid import HybridRetriever
from codeatlas.tools.registry import ToolRegistry
from codeatlas.tools.repository_tools import RepositoryTools


def main():
    provider = get_ai_provider()

    repository = clone_repository("https://github.com/psf/requests")

    store, stats = index_repository(
        repository,
        provider=provider,
    )

    print("Repository:", repository.name)
    print("Index statistics:", stats)

    retriever = HybridRetriever(store)

    tools = RepositoryTools(
        repository,
        retriever,
    )

    registry = ToolRegistry(tools)

    agent = CodeAtlasAgent(
        registry,
        provider,
    )

    rag = CodeRAG(
        retriever,
        provider,
    )

    question = (
        "Locate the HTTPAdapter class, inspect its source "
        "and explain how retry configuration is initialized. "
        "Find relevant tests if possible."
    )

    print("\nQUESTION:")
    print(question)

    print("\nRunning autonomous investigation...")

    result = agent.investigate(question)

    print("\nAGENT ANSWER:")
    print(result["answer"])

    print("\nEXECUTION TRACE:")

    for item in result["trace"]:
        print(json.dumps(item, indent=2))

    print("\nSOURCES:")

    for source in result["sources"]:
        print(f"[{source['id']}] {source['file_path']}:{source['start_line']}-{source['end_line']}")

    print("\nAgent steps:", result["steps"])

    print(
        "Citation identifiers valid:",
        result["citations_valid"],
    )

    print(
        "Termination:",
        result["termination_reason"],
    )

    print(
        "Duration:",
        result["duration_seconds"],
        "seconds",
    )

    print("\nRunning standard RAG...")

    quick_result = rag.ask("How does HTTPAdapter configure retries?")

    print("\nRAG ANSWER:")
    print(quick_result["answer"])

    print(
        "Citation identifiers valid:",
        quick_result["citations_valid"],
    )


if __name__ == "__main__":
    main()
