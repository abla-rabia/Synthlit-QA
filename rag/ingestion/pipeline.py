"""Le pipeline d'ingestion : PDF -> extraction -> ordre -> nettoyage -> chunks -> tableaux -> index.

`run_ingestion` contient la logique ; scripts/build_index.py ne fait que la lancer.
Les paramètres facultatifs (partition, count_tokens, llm, index_fn) servent aux tests :
par défaut, ce sont les vrais composants.
"""
from pathlib import Path

from rag.sources import load_sources
from rag.ingestion.reorder import reorder_document
from rag.ingestion.clean import clean_document
from rag.ingestion.chunk_by_section import (chunk_by_section, find_long_embed_texts,
                                            make_token_counter, summarize_chunks)
from rag.ingestion.tables import make_llm, summarize_tables, embed_with_table_text
from rag.ingestion import index as index_module


def run_ingestion(settings, only=None, force=False, allow_partial=False, *,
                  partition=None, count_tokens=None, llm=None, index_fn=None):
    """Construit l'index de tous les articles de sources_clean.csv.

    only          : liste d'article_id pour un ESSAI (ni index ni chunks.jsonl n'est écrit).
    force         : refait aussi l'extraction hi_res (sinon le cache JSON est utilisé).
    allow_partial : construit l'index même si un article a échoué (déconseillé).
    Retourne un dictionnaire {"chunks": [...], "failures": [(article_id, erreur), ...]}.
    """
    paths, ing, emb = settings["paths"], settings["ingestion"], settings["embedding"]
    sources = load_sources(paths["sources"])

    ids = list(sources)
    if only:
        unknown = set(only) - set(sources)
        if unknown:
            raise ValueError(f"article_id inconnus : {sorted(unknown)}")
        ids = [i for i in ids if i in only]

    if partition is None:
        from rag.ingestion.extract import partition_document as partition
    if count_tokens is None:
        count_tokens = make_token_counter(emb["model"])

    # ---- 1. par article : extraction -> ordre -> nettoyage -> chunks
    all_chunks, failures = [], []
    for article_id in ids:
        pdf_path = Path(paths["pdfs"]) / sources[article_id]["file"]
        try:
            elements = partition(pdf_path, paths["raw_cache"], force)
            ordered, _ = reorder_document(elements)
            cleaned, _ = clean_document(ordered)
            chunks = chunk_by_section(cleaned, article_id, count_tokens,
                                      ing["max_tokens"], ing["overlap_tokens"],
                                      ing["min_headings"])
        except Exception as error:               # un article en échec n'arrête pas les autres
            failures.append((article_id, repr(error)))
            print(f"ÉCHEC {article_id} : {error!r}")
            continue
        print(f"{article_id} : {len(chunks)} chunks")
        all_chunks += chunks

    # ---- 2. tableaux : description pour l'embedding (ou texte brut en repli)
    if ing["use_table_summaries"]:
        if llm is None:
            llm = make_llm(ing["summary_llm"], temperature=0)
        prompt = Path(paths["table_prompt"]).read_text(encoding="utf-8")
        n_tables = sum(len(c.tables) for c in all_chunks)
        calls = summarize_tables(all_chunks, llm, prompt, paths["table_summaries"],
                                 delay=ing["summary_delay"])
        print(f"Tableaux : {n_tables} trouvés, {calls} appels au LLM (le reste vient du cache)")
    else:
        embed_with_table_text(all_chunks)

    # ---- 3. contrôles
    too_long = find_long_embed_texts(all_chunks, count_tokens,
                                     emb["max_seq_length"], emb["header_reserve"])
    if too_long:
        print(f"ATTENTION : {len(too_long)} chunks dépassent {emb['max_seq_length']} jetons "
              f"une fois les descriptions ajoutées (ex. {too_long[:3]}) : baisse max_tokens.")
    summarize_chunks(all_chunks, ing["max_tokens"])

    # ---- 4. index et chunks.jsonl
    if only:
        print("Mode essai (--only) : l'index et chunks.jsonl n'ont pas été modifiés.")
    elif failures and not allow_partial:
        print(f"{len(failures)} article(s) en échec : index NON construit. Corrige puis relance.")
    else:
        if index_fn is None:
            index_fn = index_module.build_index
        index_fn(all_chunks, sources, paths["index"], emb["model"])
        index_module.save_chunks_jsonl(all_chunks, sources, paths["chunks"])
        print(f"chunks.jsonl écrit : {paths['chunks']}")

    if failures:
        print("Échecs :", failures)
    return {"chunks": all_chunks, "failures": failures}