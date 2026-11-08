"""Pipeline complet : question (+ historique) -> retrieval -> réponse citée.

    pipeline = load_pipeline(settings)
    chat = Conversation(pipeline)
    answer = chat.ask("Which GAN variants are used for MRI-to-CT?")
    print(answer.text); print(answer.citations)
"""
from langchain_core.messages import AIMessage, HumanMessage

from rag.generation.answer import generate_answer
from rag.generation.citations import strip_citations
from rag.retrieval.retriever import RetrievalConfig, Retriever
from rag.sources import catalogue_text


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


class RagPipeline:
    def __init__(self, retriever, llm, sources, answer_prompt, settings):
        self.retriever, self.llm, self.sources = retriever, llm, sources
        self.answer_prompt = answer_prompt
        self.catalogue = catalogue_text(sources)
        self.gen = settings["generation"]

    def ask(self, question, history=None):
        retrieval = self.retriever.retrieve(question, history)
        answer = generate_answer(self.llm, retrieval.standalone, retrieval.final, self.catalogue,
                                 self.sources, self.answer_prompt, self.gen["refusal"],
                                 self.gen["max_retries"], self.gen["max_table_chars"])
        answer.retrieval = retrieval
        return answer


class Conversation:
    """Garde les derniers échanges EN MÉMOIRE (rien n'est écrit sur disque).

    On stocke la réponse sans [n] / [catalogue] : les numéros changent à chaque question."""

    def __init__(self, pipeline, max_turns=4):
        self.pipeline, self.max_turns, self.history = pipeline, max_turns, []

    def ask(self, question):
        answer = self.pipeline.ask(question, list(self.history))
        self.history += [HumanMessage(content=question),
                         AIMessage(content=strip_citations(answer.text))]
        self.history = self.history[-2 * self.max_turns:]
        return answer

    def reset(self):
        self.history = []


def build_retrieval_config(settings):
    r = settings["retrieval"]
    return RetrievalConfig(
        n_extra_queries=r["n_extra_queries"], k_per_query=r["k_per_query"],
        k_candidates=r["k_candidates"], k_final=r["k_final"],
        weight_semantic=r["weight_semantic"], weight_keyword=r["weight_keyword"], rrf_k=r["rrf_k"],
        use_multiquery=r["use_multiquery"], use_hybrid=r["use_hybrid"], use_rerank=r["use_rerank"])


def load_pipeline(settings):
    """Charge tout (index, BM25, reranker, LLM). Long la 1re fois : à faire UNE fois par session."""
    from rag.ingestion.index import load_chunks_jsonl, load_index
    from rag.ingestion.tables import make_llm
    from rag.retrieval.rerank import Reranker
    from rag.retrieval.search import Bm25Searcher, VectorSearcher
    from rag.sources import load_sources

    paths, r = settings["paths"], settings["retrieval"]
    sources = load_sources(paths["sources"])
    records = load_chunks_jsonl(paths["chunks"])
    store = load_index(paths["index"], settings["embedding"]["model"])
    llm = make_llm(settings["llm"]["model"], settings["llm"]["temperature"])
    config = build_retrieval_config(settings)
    reranker = Reranker(r["rerank_model"]) if config.use_rerank else None
    retriever = Retriever(records, VectorSearcher(store, r.get("query_prefix", "")),
                          Bm25Searcher(records), reranker, llm, config,
                          _read(paths["condense_prompt"]), _read(paths["multiquery_prompt"]))
    return RagPipeline(retriever, llm, sources, _read(paths["answer_prompt"]), settings)
