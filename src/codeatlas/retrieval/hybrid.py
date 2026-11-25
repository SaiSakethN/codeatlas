"""Hybrid retrieval using reciprocal rank fusion."""

from codeatlas.retrieval.keyword import KeywordRetriever


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    top_k: int = 6,
    k: int = 60,
):
    scores = {}
    documents = {}

    for results in result_lists:
        seen = set()

        for rank, result in enumerate(results, start=1):
            chunk_id = result["chunk_id"]

            if chunk_id in seen:
                continue

            seen.add(chunk_id)

            documents.setdefault(chunk_id, {}).update(result)

            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (k + rank)

    ranked = sorted(
        scores,
        key=scores.get,
        reverse=True,
    )[:top_k]

    return [
        {
            **documents[chunk_id],
            "fusion_score": scores[chunk_id],
        }
        for chunk_id in ranked
    ]


class HybridRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store

        self.keyword_retriever = KeywordRetriever(vector_store.get_all_chunks())

    def search(self, query: str, top_k: int = 6):
        if not query.strip() or top_k <= 0:
            return []

        candidates = top_k * 3

        semantic = self.vector_store.search(
            query,
            top_k=candidates,
        )

        keyword = self.keyword_retriever.search(
            query,
            top_k=candidates,
        )

        return reciprocal_rank_fusion(
            [semantic, keyword],
            top_k=top_k,
        )
