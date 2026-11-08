"""Les objets échangés entre retrieval, génération et pipeline."""
from dataclasses import dataclass, field


@dataclass
class Hit:
    """Un chunk retrouvé (une ligne de data/chunks.jsonl)."""
    chunk_id: str
    article_id: str
    header: str
    section: str
    sous_section: str
    page_start: int
    page_end: int
    text: str                      # texte d'origine (sans description de tableau)
    embed_text: str                # texte + descriptions, utilisé pour BM25 / rerank
    tables: list = field(default_factory=list)

    @classmethod
    def from_record(cls, r):
        return cls(chunk_id=r["chunk_id"], article_id=r["article_id"], header=r.get("header", ""),
                   section=r.get("section") or "", sous_section=r.get("sous_section") or "",
                   page_start=r.get("page_start") or 0, page_end=r.get("page_end") or 0,
                   text=r["text"], embed_text=r.get("embed_text") or r["text"],
                   tables=r.get("tables") or [])

    @property
    def pages(self):
        if self.page_start and self.page_end and self.page_end != self.page_start:
            return f"pp. {self.page_start}-{self.page_end}"
        return f"p. {self.page_start}" if self.page_start else ""


@dataclass
class RetrievalResult:
    standalone: str                # question réécrite sans pronoms (grâce à l'historique)
    queries: list                  # [question, requête 2, requête 3]
    per_query: dict                # requête -> chunk_ids (après hybride)
    candidates: list               # les 10 après RRF
    final: list                    # les 5 après rerank


@dataclass
class Answer:
    text: str
    question: str                  # la question autonome utilisée
    citations: list                # sources réellement citées, dans l'ordre
    used_catalogue: bool
    refused: bool
    retries: int
    removed: list                  # numéros invalides retirés du texte
    hits: list                     # les passages envoyés au LLM ([1] = hits[0])
    retrieval: RetrievalResult = None
