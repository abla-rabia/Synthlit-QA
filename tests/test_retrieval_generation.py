"""Tests du retrieval, de la génération et de la conversation, avec de FAUX composants
(pas de modèle, pas de Chroma, pas de réseau).

Lancer : pytest -q
"""
from types import SimpleNamespace as NS

from rag.generation.answer import generate_answer
from rag.generation.citations import (find_citations, normalize_multi, remove_invalid,
                                      strip_citations)
from rag.generation.prompt import clean_passage, format_context
from rag.pipeline import Conversation, RagPipeline
from rag.retrieval.fusion import weighted_rrf
from rag.retrieval.queries import QueriesClass, generate_queries, rewrite_question
from rag.retrieval.rerank import Reranker
from rag.retrieval.retriever import RetrievalConfig, Retriever
from rag.retrieval.search import Bm25Searcher
from rag.sources import catalogue_text
from rag.types import Hit

REFUSAL = "I don't have enough information in the indexed papers to answer this question."


def rec(i, text, article="2024_dayarathna", tables=None):
    return {"chunk_id": f"{article}::{i:03d}", "article_id": article, "header": f"Dayarathna et al., 2024 · {i}",
            "section": "3. Methods", "sous_section": None, "page_start": i, "page_end": i,
            "text": text, "embed_text": text, "tables": tables or []}


RECORDS = [rec(1, "GANs translate MRI to CT with adversarial loss"),
           rec(2, "Diffusion models denoise images step by step"),
           rec(3, "PET attenuation correction uses CT priors"),
           rec(4, "Evaluation uses MAE and SSIM metrics"),
           rec(5, "Datasets include brain MRI scans of patients"),
           rec(6, "Transformers capture long range dependencies"),
           rec(7, "Training used the Adam optimizer"),
           rec(8, "Loss functions include L1 and perceptual loss")]
IDS = [r["chunk_id"] for r in RECORDS]
SOURCES = {"2024_dayarathna": {"article_id": "2024_dayarathna", "authors": "Sanuwani Dayarathna, Kh Islam",
                               "year": "2024", "title": "Deep learning based synthesis", "type": "revue",
                               "link": "https://doi.org/x", "license": "CC BY 4.0"}}


class FakeSearcher:
    def __init__(self, table):
        self.table, self.calls = table, []

    def search(self, query, k):
        self.calls.append(query)
        return self.table.get(query, IDS[:3])[:k]


class FakeLLM:
    """invoke() rend les réponses prévues dans l'ordre ; with_structured_output() rend `queries`."""

    def __init__(self, replies=(), queries=("alt one", "alt two")):
        self.replies, self.queries, self.prompts = list(replies), (queries if isinstance(queries, Exception) else list(queries)), []

    def invoke(self, messages):
        self.prompts.append(messages)
        return NS(content=self.replies.pop(0))

    def with_structured_output(self, schema, method=None):
        assert schema is QueriesClass and method == "json_schema"
        outer = self

        class S:
            def invoke(self, messages):
                if isinstance(outer.queries, Exception):
                    raise outer.queries
                return QueriesClass(queries=outer.queries)
        return S()


# ------------------------------------------------------------------ fusion / bm25 / rerank
def test_rrf_poids_et_doublons():
    fused = dict(weighted_rrf([["a", "b"], ["b", "a"]], [0.7, 0.3], k=60))
    assert fused["a"] > fused["b"]                                   # 0.7 pèse plus
    assert abs(fused["a"] - (0.7 / 61 + 0.3 / 62)) < 1e-12
    assert weighted_rrf([["x", "x", "y"]])[0][0] == "x" and len(weighted_rrf([["x", "x", "y"]])) == 2
    ids = [i for i, _ in weighted_rrf([["a", "b"], ["c", "b"]])]
    assert ids[0] == "b"                                             # présent dans les deux listes


def test_bm25_trouve_le_mot_cle():
    bm25 = Bm25Searcher(RECORDS)
    assert bm25.search("SSIM metrics", 3)[0] == IDS[3]
    assert bm25.search("the of", 3) == []                            # uniquement des mots vides


def test_reranker_garde_les_meilleurs():
    hits = [Hit.from_record(r) for r in RECORDS[:4]]
    model = NS(predict=lambda pairs: [0.1, 0.9, 0.5, 0.7])
    assert [h.chunk_id for h in Reranker(model).rerank("q", hits, 2)] == [IDS[1], IDS[3]]


# ------------------------------------------------------------------ requêtes
def test_requetes_et_historique():
    llm = FakeLLM(replies=["What generative models synthesize PET?"])
    assert rewrite_question(llm, "and for PET?", [], "p") == "and for PET?"       # sans historique : aucun appel
    assert not llm.prompts
    history = [NS(content="hi"), NS(content="hello")]
    assert rewrite_question(llm, "and for PET?", history, "p") == "What generative models synthesize PET?"
    assert llm.prompts[0][-1].content == "new question : and for PET?"

    assert generate_queries(FakeLLM(), "q", 2, "make {n}") == ["q", "alt one", "alt two"]
    assert generate_queries(FakeLLM(queries=["Q", "x", "x", "y"]), "q", 2, "p") == ["q", "x", "y"]
    assert generate_queries(FakeLLM(queries=RuntimeError("boom")), "q", 2, "p") == ["q"]   # repli
    assert generate_queries(FakeLLM(), "q", 0, "p") == ["q"]


# ------------------------------------------------------------------ retriever
def make_retriever(use_multiquery=True, use_hybrid=True, use_rerank=True, k_final=3):
    vec = FakeSearcher({"q": [IDS[0], IDS[1], IDS[2]], "alt one": [IDS[3], IDS[2]], "alt two": [IDS[2], IDS[4]]})
    kw = FakeSearcher({"q": [IDS[2]], "alt one": [IDS[3]], "alt two": [IDS[5]]})
    reranker = Reranker(NS(predict=lambda pairs: [-i for i, _ in enumerate(pairs)]))    # garde l'ordre
    cfg = RetrievalConfig(k_final=k_final, use_multiquery=use_multiquery, use_hybrid=use_hybrid,
                          use_rerank=use_rerank)
    return Retriever(RECORDS, vec, kw, reranker, FakeLLM(), cfg, "c", "m{n}"), vec, kw


def test_retriever_complet():
    retriever, vec, kw = make_retriever()
    result = retriever.retrieve("q")
    assert result.queries == ["q", "alt one", "alt two"]
    assert vec.calls == kw.calls == result.queries                    # 3 requêtes, 2 recherches chacune
    assert result.per_query["q"][0] == IDS[2]                         # 0.7 sém + 0.3 mots-clés : IDS[2] gagne
    assert result.candidates[0].chunk_id == IDS[2]                    # présent dans les 3 listes
    assert len(result.final) == 3 and result.final == result.candidates[:3]


def test_retriever_interrupteurs():
    r, vec, kw = make_retriever(use_multiquery=False)
    assert r.retrieve("q").queries == ["q"] and vec.calls == ["q"]
    r, vec, kw = make_retriever(use_hybrid=False)
    result = r.retrieve("q")
    assert kw.calls == [] and result.per_query["q"] == [IDS[0], IDS[1], IDS[2]]
    r, _, _ = make_retriever(use_rerank=False, k_final=2)
    assert len(r.retrieve("q").final) == 2


# ------------------------------------------------------------------ citations / prompt
def test_citations():
    assert find_citations("A [2] b [catalogue] c [2][5] d [70.8, 95.2]") == [2, "catalogue", 5]
    assert normalize_multi("x [1, 2] y [70, 95]", 5) == "x [1][2] y [70, 95]"
    assert remove_invalid("ok [1] bad [9]. fin", 5) == "ok [1] bad. fin"
    assert strip_citations("Réponse [1][catalogue] finie [2].") == "Réponse finie."


def test_prompt_nettoie_et_ajoute_les_tableaux():
    assert clean_passage("as in [12] and [6,10-13] but [70.8, 95.2] stays") == "as in and but [70.8, 95.2] stays"
    table = {"page": 3, "html": "<table><tr><td>MAE</td><td>80.1</td></tr></table>", "summary": "RESUME"}
    context = format_context([Hit.from_record(rec(3, "Results [4].", tables=[table]))])
    assert context.startswith("[1] Dayarathna et al., 2024 · 3 (p. 3)")
    assert "Results." in context and "MAE | 80.1" in context and "RESUME" not in context


def test_catalogue():
    assert catalogue_text(SOURCES) == "- Dayarathna et al., 2024 — Deep learning based synthesis (revue)"


# ------------------------------------------------------------------ génération
def hits(n):
    return [Hit.from_record(r) for r in RECORDS[:n]]


def gen(llm, n=3, **kw):
    return generate_answer(llm, "q?", hits(n), catalogue_text(SOURCES), SOURCES, "S {catalogue} {refusal}", REFUSAL, **kw)


def test_reponse_valide():
    llm = FakeLLM(replies=["GANs are used [1][3]. See also [catalogue]."])
    a = gen(llm)
    assert [c["n"] for c in a.citations] == [1, 3] and a.used_catalogue and a.retries == 0 and not a.refused
    assert a.citations[0]["citation"] == "Dayarathna et al., 2024" and a.citations[0]["pages"] == "p. 1"
    system = llm.prompts[0][0].content
    assert "Dayarathna et al., 2024 — Deep" in system and REFUSAL in system


def test_nouvel_essai_si_citation_invalide_ou_absente():
    a = gen(FakeLLM(replies=["Bad [7].", "Good [2]."]))
    assert a.retries == 1 and a.text == "Good [2]." and a.removed == []
    a = gen(FakeLLM(replies=["No citation here.", "Fixed [1]."]))
    assert a.retries == 1 and [c["n"] for c in a.citations] == [1]
    a = gen(FakeLLM(replies=["Bad [7].", "Still [1] bad [8]."]))               # échec : on retire les invalides
    assert a.text == "Still [1] bad." and a.removed == [8] and [c["n"] for c in a.citations] == [1]


def test_refus_sans_source():
    llm = FakeLLM(replies=[REFUSAL])
    a = gen(llm)
    assert a.refused and a.citations == [] and a.retries == 0 and len(llm.prompts) == 1


# ------------------------------------------------------------------ pipeline + conversation
def test_conversation_historique_sans_citations():
    retriever, _, _ = make_retriever()
    retriever.llm = FakeLLM(replies=["Standalone question q"], queries=["alt one", "alt two"])
    llm = FakeLLM(replies=["First answer [1].", "Second answer [2]."])
    settings = {"generation": {"refusal": REFUSAL, "max_retries": 1, "max_table_chars": 3000}}
    pipeline = RagPipeline(retriever, llm, SOURCES, "S {catalogue} {refusal}", settings)
    chat = Conversation(pipeline, max_turns=1)

    first = chat.ask("q")
    assert first.retrieval.standalone == "q"                             # pas d'historique : pas de réécriture
    assert [m.content for m in chat.history] == ["q", "First answer."]    # sans [1]
    second = chat.ask("and then?")
    assert second.question == "Standalone question q"                    # réécrite avec l'historique
    assert len(chat.history) == 2 and chat.history[0].content == "and then?"   # max_turns=1
    chat.reset()
    assert chat.history == []


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK ", name)
