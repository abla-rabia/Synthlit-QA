"""Reranker : un cross-encoder lit (question, passage) ENSEMBLE et donne un score de pertinence."""


class Reranker:
    def __init__(self, model="cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512):
        """`model` : un nom Hugging Face, ou un objet qui a .predict(paires) (utile pour les tests)."""
        if isinstance(model, str):
            from sentence_transformers import CrossEncoder
            model = CrossEncoder(model, max_length=max_length)
        self.model = model

    def rerank(self, query, hits, k):
        if not hits:
            return []
        pairs = [(query, f"{h.header}\n{h.embed_text}") for h in hits]
        scores = list(self.model.predict(pairs))
        order = sorted(range(len(hits)), key=lambda i: -float(scores[i]))   # tri stable
        return [hits[i] for i in order[:k]]
