from rank_bm25 import BM25Okapi


class BM25Index:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        tokenized = [c.lower().split() for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 10) -> list[str]:
        scores = self.bm25.get_scores(query.lower().split())
        ranked = sorted(zip(self.chunks, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]