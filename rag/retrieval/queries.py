"""Historique -> question autonome ; question -> plusieurs requêtes (multi-query)."""
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class QueriesClass(BaseModel):
    queries: list[str] = Field(description="Alternative search queries, each on its own.")


def rewrite_question(llm, question, history, system_prompt):
    """Avec un historique, réécrit la question pour qu'elle se comprenne seule
    ("et sur le PET ?" -> "Quels modèles synthétisent le PET ?"). Sans historique : inchangée."""
    if not history:
        return question
    messages = [SystemMessage(content=system_prompt), *history,
                HumanMessage(content=f"new question : {question}")]
    rewritten = (llm.invoke(messages).content or "").strip()
    return rewritten or question


def generate_queries(llm, question, n_extra, system_prompt):
    """[question] + n_extra reformulations. Si le LLM échoue, on garde la question seule."""
    if n_extra <= 0:
        return [question]
    extras = []
    try:
        structured = llm.with_structured_output(QueriesClass, method="json_schema")
        result = structured.invoke([SystemMessage(content=system_prompt.replace("{n}", str(n_extra))),
                                    HumanMessage(content=question)])
        extras = result.queries if hasattr(result, "queries") else result["queries"]
    except Exception as error:                                 # réseau, schéma refusé, JSON invalide…
        log.warning("multi-query indisponible (%s) : on cherche avec la question seule", error)
    queries, seen = [question], {question.casefold()}
    for extra in extras:
        extra = (extra or "").strip()
        if extra and extra.casefold() not in seen:
            queries.append(extra)
            seen.add(extra.casefold())
    return queries[:1 + n_extra]
