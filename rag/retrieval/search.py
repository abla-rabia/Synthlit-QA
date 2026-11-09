"""Les deux recherches : sémantique (Chroma) et mots-clés (BM25). Elles retournent des chunk_id."""
import re

import numpy as np

_STOP = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "is", "are", "was",
         "were", "be", "by", "as", "at", "from", "that", "this", "it", "its", "which", "what",
         "how", "do", "does", "did", "than", "using", "used", "use"}


def tokenize(text):
    return [t for t in re.findall(r"\w+", (text or "").lower()) if t not in _STOP]

class VectorSearcher:
    """Recherche sémantique dans Chroma (le même modèle d'embedding qu'à l'ingestion)."""

    def __init__(self, store, query_prefix=""):
        self.store = store
        self.prefix = query_prefix

    def search(self, query, k, filter=None):
        """Recherche sémantique. `filter` = dict Chroma (ex. {"article_id": "..."})."""
        q = self.prefix + query
        if filter:
            found = self.store.similarity_search_with_score(q, k=k, filter=filter)
        else:
            found = self.store.similarity_search_with_score(q, k=k)
        return [doc.metadata["chunk_id"] for doc, _ in found]


class Bm25Searcher:
    """Recherche par mots-clés sur l'en-tête + embed_text de chaque chunk (donc aussi sur les
    descriptions de tableaux)."""

    def __init__(self, records):
        from rank_bm25 import BM25Okapi
        self.ids = [r["chunk_id"] for r in records]
        corpus = [tokenize(f"{r.get('header', '')} {r.get('embed_text') or r['text']}") for r in records]
        self.bm25 = BM25Okapi(corpus)

    def search(self, query, k):
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        order = np.argsort(-scores, kind="stable")[:k]
        return [self.ids[i] for i in order if scores[i] > 0]
