"""Construction du contexte numéroté [1]..[5] envoyé au LLM de réponse."""
import re

from rag.ingestion.tables import table_to_text

# Marqueurs de références bibliographiques des articles : [12], [6,10-13]. On les retire pour
# qu'ils ne se confondent pas avec NOS numéros de passage. Les "[70.8, 95.2]" restent intacts.
_REF_MARKER = re.compile(r"\s?\[\d+(?:\s*[,–-]\s*\d+)*\]")


def clean_passage(text):
    return _REF_MARKER.sub("", text or "")


def format_passage(number, hit, max_table_chars=3000):
    """Un passage : en-tête numéroté, texte d'origine, puis ses tableaux d'origine (pas les résumés)."""
    where = f" ({hit.pages})" if hit.pages else ""
    parts = [f"[{number}] {hit.header}{where}", clean_passage(hit.text)]
    for table in hit.tables:
        body = table_to_text(table.get("html"), table.get("text", ""), max_table_chars)
        if body.strip():
            page = f" (p. {table['page']})" if table.get("page") else ""
            parts.append(f"Table{page}:\n{body}")
    return "\n".join(parts)


def format_context(hits, max_table_chars=3000):
    return "\n\n".join(format_passage(i, h, max_table_chars) for i, h in enumerate(hits, start=1))
