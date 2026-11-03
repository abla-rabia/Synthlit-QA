"""Index : embeddings (modèle local) + Chroma persistant, et sauvegarde de chunks.jsonl.

Ce qui est embarqué (page_content) : "Dayarathna et al., 2024 · 3.1.1 Model design…" + embed_text.
Le texte d'origine (sans description de tableau) est gardé dans les métadonnées ("text"),
ainsi que le HTML des tableaux ("tables_json") : c'est ce que la génération utilisera.

Les imports lourds (langchain, chroma, modèle) sont faits dans les fonctions qui en ont besoin.
"""
import json
import shutil
from pathlib import Path

from rag.sources import short_citation


# --------------------------------------------------- un chunk -> un enregistrement
def build_header(chunk, source):
    """'Dayarathna et al., 2024 · 3.1.1 Model design…' : aide la recherche et la lecture."""
    citation = short_citation(source) if source else chunk.article_id
    return f"{citation} · {chunk.heading}" if chunk.heading else citation


def chunk_to_record(chunk, source):
    """Retourne (texte_à_embarquer, métadonnées).

    Les métadonnées de Chroma doivent être des valeurs simples (texte, nombre, booléen) :
    pas de liste, pas de dictionnaire, pas de None -> les tableaux sont stockés en JSON.
    """
    header = build_header(chunk, source)
    metadata = {
        "chunk_id": chunk.chunk_id,
        "article_id": chunk.article_id,
        "section": chunk.section or "",
        "sous_section": chunk.sous_section or "",
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "chunk_type": chunk.chunk_type,
        "header": header,
        "text": chunk.text,                                            # texte d'origine
        "tables_json": json.dumps(chunk.tables, ensure_ascii=False),   # tableaux d'origine (HTML)
    }
    return f"{header}\n{chunk.embed_text}", metadata


# ----------------------------------------------------------- chunks.jsonl
def save_chunks_jsonl(chunks, sources, path):
    """Une ligne JSON par chunk (pour BM25 et pour relire les chunks sans recalculer)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            record = chunk.to_dict()
            record["header"] = build_header(chunk, sources.get(chunk.article_id))
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_chunks_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ------------------------------------------------------------ Chroma
def make_embedding_model(model_name):
    """Le modèle d'embedding local (même modèle pour l'index et pour les questions)."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=model_name,
                                 encode_kwargs={"normalize_embeddings": True})


def _chroma_class():
    try:
        from langchain_chroma import Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma
    return Chroma


def build_index(chunks, sources, persist_directory, model_name, rebuild=True):
    """Calcule les embeddings et écrit l'index Chroma (distance cosinus)."""
    from langchain_core.documents import Document

    persist_directory = Path(persist_directory)
    if rebuild and persist_directory.exists():
        shutil.rmtree(persist_directory)          # évite les doublons d'une ancienne version

    documents, ids = [], []
    for chunk in chunks:
        text, metadata = chunk_to_record(chunk, sources.get(chunk.article_id))
        documents.append(Document(page_content=text, metadata=metadata))
        ids.append(chunk.chunk_id)

    vector_store = _chroma_class().from_documents(
        documents=documents,
        embedding=make_embedding_model(model_name),
        ids=ids,
        persist_directory=str(persist_directory),
        collection_metadata={"hnsw:space": "cosine"},
    )
    print(f"Index créé : {len(documents)} chunks dans {persist_directory}")
    return vector_store


def load_index(persist_directory, model_name):
    """Rouvre l'index déjà construit (pour l'application et l'évaluation)."""
    return _chroma_class()(
        persist_directory=str(persist_directory),
        embedding_function=make_embedding_model(model_name),
        collection_metadata={"hnsw:space": "cosine"},
    )