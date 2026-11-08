"""Le retrieval complet :

  historique -> question autonome -> 3 requêtes
  pour chaque requête : sémantique (0.7) + mots-clés (0.3), RRF pondéré -> 10
  les 3 listes -> RRF -> 10 candidats -> reranker -> 5

Trois interrupteurs (use_multiquery, use_hybrid, use_rerank) pour mesurer chaque brique.
"""
from dataclasses import dataclass

from rag.retrieval.fusion import weighted_rrf
from rag.retrieval.queries import generate_queries, rewrite_question
from rag.types import Hit, RetrievalResult


@dataclass
class RetrievalConfig:
    n_extra_queries: int = 2
    k_per_query: int = 10
    k_candidates: int = 10
    k_final: int = 5
    weight_semantic: float = 0.7
    weight_keyword: float = 0.3
    rrf_k: int = 60
    use_multiquery: bool = True
    use_hybrid: bool = True
    use_rerank: bool = True


class Retriever:
    def __init__(self, records, vector, keyword, reranker, llm, config, condense_prompt, multiquery_prompt):
        self.hits = {r["chunk_id"]: Hit.from_record(r) for r in records}
        self.vector, self.keyword, self.reranker = vector, keyword, reranker
        self.llm, self.cfg = llm, config
        self.condense_prompt, self.multiquery_prompt = condense_prompt, multiquery_prompt

    def _search_one(self, query):
        c = self.cfg
        semantic = self.vector.search(query, c.k_per_query)
        if not c.use_hybrid:
            return semantic[:c.k_per_query]
        keyword = self.keyword.search(query, c.k_per_query)
        fused = weighted_rrf([semantic, keyword], [c.weight_semantic, c.weight_keyword], c.rrf_k)
        return [chunk_id for chunk_id, _ in fused[:c.k_per_query]]

    def retrieve(self, question, history=None):
        c = self.cfg
        standalone = rewrite_question(self.llm, question, history, self.condense_prompt)
        n_extra = c.n_extra_queries if c.use_multiquery else 0
        queries = generate_queries(self.llm, standalone, n_extra, self.multiquery_prompt)

        per_query = {q: self._search_one(q) for q in queries}
        fused = weighted_rrf(list(per_query.values()), None, c.rrf_k)
        candidates = [self.hits[i] for i, _ in fused[:c.k_candidates] if i in self.hits]

        if c.use_rerank and self.reranker is not None:
            final = self.reranker.rerank(standalone, candidates, c.k_final)
        else:
            final = candidates[:c.k_final]
        return RetrievalResult(standalone, queries, per_query, candidates, final)
