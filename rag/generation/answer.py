"""Génération de la réponse : passages numérotés + catalogue -> texte cité et validé."""
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from rag.generation.citations import (find_citations, normalize_multi, remove_invalid,
                                      split_valid)
from rag.generation.prompt import format_context
from rag.sources import short_citation
from rag.types import Answer


def _norm(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def is_refusal(text, refusal):
    return _norm(refusal) in _norm(text)


def _citation_info(number, hit, sources):
    source = sources.get(hit.article_id, {})
    return {"n": number, "article_id": hit.article_id, "citation": short_citation(source) or hit.article_id,
            "title": source.get("title", ""), "link": source.get("link", ""),
            "license": source.get("license", ""), "section": hit.sous_section or hit.section,
            "pages": hit.pages, "chunk_id": hit.chunk_id}


def generate_answer(llm, question, hits, catalogue, sources, system_prompt, refusal,
                    max_retries=1, max_table_chars=3000):
    """`question` est la question AUTONOME (déjà réécrite avec l'historique)."""
    system = system_prompt.replace("{catalogue}", catalogue).replace("{refusal}", refusal)
    human = f"Passages:\n\n{format_context(hits, max_table_chars)}\n\nQuestion: {question}"
    messages = [SystemMessage(content=system), HumanMessage(content=human)]
    n = len(hits)

    text, retries = "", 0
    while True:
        text = normalize_multi((llm.invoke(messages).content or "").strip(), n)
        refused = is_refusal(text, refusal)
        valid, invalid = split_valid(find_citations(text), n)
        problem = None
        if not refused and invalid:
            problem = (f"Your answer cites invalid numbers {invalid}. Only [1] to [{n}] and [catalogue] exist. "
                       "Rewrite it using only valid citations.")
        elif not refused and not valid:
            problem = ("Your answer has no citation. Rewrite it: every factual statement must end with "
                       f"[n] (n from 1 to {n}) or [catalogue].")
        if problem is None or retries >= max_retries:
            break
        retries += 1
        messages += [AIMessage(content=text), HumanMessage(content=problem)]

    removed = split_valid(find_citations(text), n)[1]
    if removed:
        text = remove_invalid(text, n)
    cited = split_valid(find_citations(text), n)[0]
    citations = [] if refused else [_citation_info(c, hits[c - 1], sources) for c in cited if c != "catalogue"]
    return Answer(text=text, question=question, citations=citations,
                  used_catalogue="catalogue" in cited, refused=refused, retries=retries,
                  removed=removed, hits=hits)
