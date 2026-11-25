"""Opt-in real CPU embedding/index/retrieval smoke check; no chat-provider calls."""

from codeatlas.config import WORKSPACE_DIR, settings
from codeatlas.indexing import vector_store
from codeatlas.indexing.pipeline import index_repository
from codeatlas.llm.fastembed_provider import FastEmbedProvider
from codeatlas.models import Repository
from codeatlas.retrieval.hybrid import HybridRetriever


def main():
    root = WORKSPACE_DIR / "verification-fixture"
    root.mkdir(parents=True, exist_ok=True)
    (root / "application.py").write_text(
        'def retry_delay(attempt):\n    """Exponential retry backoff."""\n'
        "    return min(2 ** attempt, 60)\n\n"
        'def greet(name):\n    return f"Hello {name}"\n',
        encoding="utf-8",
    )
    settings.llm_provider = "fastembed"
    vector_store.INDEXES_DIR = WORKSPACE_DIR / "verification-indexes"
    provider = FastEmbedProvider()
    store, stats = index_repository(
        Repository("verification", root, "fixture://codeatlas-verification"),
        provider=provider,
        rebuild=True,
    )
    results = HybridRetriever(store).search("exponential retry backoff", top_k=1)
    assert results and results[0]["symbol_name"] == "retry_delay"
    assert len(provider.embed_query("retry")) == 384
    print({"chunks": stats["chunks"], "top_symbol": results[0]["symbol_name"], "dimensions": 384})


if __name__ == "__main__":
    main()
