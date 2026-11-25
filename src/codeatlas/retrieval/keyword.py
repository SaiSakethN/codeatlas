"""BM25 keyword retrieval for source code."""

import re

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    text = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        r"\1 \2",
        text,
    )

    text = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1 \2",
        text,
    )

    return re.findall(
        r"[a-z0-9]+",
        text.lower(),
    )


class KeywordRetriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks

        self.corpus = [
            tokenize(f"{chunk['file_path']} {chunk['symbol_name']} {chunk['content']}")
            for chunk in chunks
        ]

        self.token_sets = [set(tokens) for tokens in self.corpus]

        self.index = BM25Okapi(self.corpus) if self.corpus and any(self.corpus) else None

    def search(self, query: str, top_k: int = 6):
        tokens = tokenize(query)

        if self.index is None or not tokens or top_k <= 0:
            return []

        scores = self.index.get_scores(tokens)
        query_tokens = set(tokens)

        candidates = [
            index for index, words in enumerate(self.token_sets) if query_tokens.intersection(words)
        ]

        ranked = sorted(
            candidates,
            key=lambda index: scores[index],
            reverse=True,
        )[:top_k]

        return [
            {
                **self.chunks[index],
                "keyword_score": float(scores[index]),
            }
            for index in ranked
        ]
