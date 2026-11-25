"""Persistent vector storage for repository code."""

import hashlib

import chromadb

from codeatlas.config import INDEXES_DIR, settings
from codeatlas.llm.factory import get_ai_provider
from codeatlas.models import CodeChunk


class VectorStore:
    def __init__(self, repository_id: str, provider=None):
        INDEXES_DIR.mkdir(parents=True, exist_ok=True)

        self.provider = provider or get_ai_provider()

        self.client = chromadb.PersistentClient(path=str(INDEXES_DIR))

        embedding_model = (
            settings.ollama_embedding_model
            if settings.llm_provider == "ollama"
            else settings.fastembed_model
            if settings.llm_provider == "fastembed"
            else settings.openai_embedding_model
        )

        identity = f"{repository_id}:{settings.llm_provider}:{embedding_model}:v1"

        digest = hashlib.sha256(identity.encode()).hexdigest()[:32]

        self.collection_name = f"codeatlas_{digest}"

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self):
        self.client.delete_collection(self.collection_name)

        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=None,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        return self.collection.count()

    def add_chunks(self, chunks: list[CodeChunk]):
        batch_size = settings.embedding_batch_size

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]

            documents = [
                (
                    f"File: {chunk.file_path}\n"
                    f"Symbol: {chunk.symbol_name}\n"
                    f"Type: {chunk.symbol_type}\n"
                    f"{chunk.content}"
                )
                for chunk in batch
            ]

            embeddings = self.provider.embed_documents(documents)

            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in batch],
                documents=[chunk.content for chunk in batch],
                embeddings=embeddings,
                metadatas=[
                    {
                        "repository": chunk.repository,
                        "file_path": chunk.file_path,
                        "symbol_name": chunk.symbol_name,
                        "symbol_type": chunk.symbol_type,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    }
                    for chunk in batch
                ],
            )

    def search(self, query: str, top_k: int = 6):
        if not self.count() or top_k <= 0:
            return []

        embedding = self.provider.embed_query(query)

        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self.count()),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        return [
            {
                "chunk_id": chunk_id,
                "content": content,
                **metadata,
                "distance": distance,
            }
            for chunk_id, content, metadata, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
                strict=True,
            )
        ]

    def get_all_chunks(self):
        result = self.collection.get(include=["documents", "metadatas"])

        return [
            {
                "chunk_id": chunk_id,
                "content": content,
                **metadata,
            }
            for chunk_id, content, metadata in zip(
                result["ids"],
                result["documents"],
                result["metadatas"],
                strict=True,
            )
        ]
