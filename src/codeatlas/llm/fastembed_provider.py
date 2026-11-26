"""Optional CPU ONNX embeddings for hosts without an Ollama service."""

from functools import lru_cache

from codeatlas.config import settings
from codeatlas.llm.base import AIProvider


@lru_cache(maxsize=1)
def embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.fastembed_model, threads=settings.fastembed_threads)


class FastEmbedProvider(AIProvider):
    def embed_documents(self, documents):
        return [
            vector.tolist()
            for vector in embedding_model().embed(
                documents, batch_size=settings.fastembed_batch_size
            )
        ]

    def embed_query(self, query):
        return next(iter(embedding_model().query_embed(query))).tolist()

    def chat(self, messages, tools=None):
        raise RuntimeError("FastEmbed requires a separate CHAT_PROVIDER.")
