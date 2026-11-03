"""Tableaux : HTML -> texte compact, et description par le LLM pour l'embedding.

Idée : le texte d'un chunk ne contient pas ses tableaux. Pour que la recherche les
retrouve, on demande au LLM une courte description de chaque tableau, et on l'ajoute au
texte qui sert à l'embedding (`chunk.embed_text`). Le tableau original reste dans
`chunk.tables[i]["html"]` et c'est lui (pas la description) qu'on donne au LLM de réponse.

Usage :
    from tables import make_llm, summarize_tables
    llm = make_llm("openai/gpt-oss-20b", temperature=0)        # après load_dotenv()
    prompt = open("config/prompts/table_summary.txt", encoding="utf-8").read()
    summarize_tables(chunks, llm, prompt, cache_path="data/table_summaries.json")
"""
import hashlib
import json
import time
from html.parser import HTMLParser
from pathlib import Path


# ------------------------------------------------------ HTML -> texte compact
class _TableParser(HTMLParser):
    """Lit un <table> et garde les lignes sous forme de listes de cellules."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            if self._row is None:
                self._row = []
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def table_to_text(html, fallback_text="", max_chars=6000):
    """HTML d'un tableau -> une ligne par rangée, cellules séparées par ' | '.

    Pas de balises (elles coûtent des jetons). Sans HTML, on utilise `fallback_text`.
    Un tableau trop long est coupé à `max_chars` caractères, à la fin d'une ligne.
    """
    text = ""
    if html:
        parser = _TableParser()
        parser.feed(html)
        parser.close()
        if parser._row:                                   # <tr> jamais fermé
            parser.rows.append(parser._row)
        rows = [r for r in parser.rows if any(r)]
        text = "\n".join(" | ".join(r) for r in rows)
    if not text.strip():
        text = fallback_text or ""
    if len(text) > max_chars:
        text = text[:max_chars].rsplit("\n", 1)[0] + "\n[… table truncated]"
    return text


# ----------------------------------------------------------------- LLM
def make_llm(model="openai/gpt-oss-20b", temperature=0):
    """Le modèle Groq (la clé GROQ_API_KEY vient de .env : appelle load_dotenv() avant)."""
    from langchain_groq import ChatGroq
    return ChatGroq(model=model, temperature=temperature)


def _invoke_with_retry(llm, prompt, tries=3, wait=5.0):
    """Appelle le LLM ; en cas d'erreur (limite de débit, réseau) attend puis réessaie."""
    for attempt in range(1, tries + 1):
        try:
            return llm.invoke(prompt).content.strip()
        except Exception:
            if attempt == tries:
                raise
            time.sleep(wait * attempt)


# --------------------------------------------------------------- cache
def load_cache(path):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {}


def save_cache(path, cache):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def _cache_key(prompt):
    """La clé est le prompt FINAL (modèle + section + tableau) : si l'un des trois change,
    la description est refaite ; sinon elle vient du cache."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


# ------------------------------------------------------- texte à embarquer
def build_embed_text(text, descriptions):
    """Texte du chunk + une ligne 'Table description: …' par tableau."""
    if not descriptions:
        return text
    lines = "\n".join(f"Table description: {d}" for d in descriptions)
    return f"{text}\n\n{lines}"


def summarize_tables(chunks, llm, prompt_template, cache_path=None, delay=0.0,
                     tries=3, wait=5.0, max_chars=6000):
    """Décrit chaque tableau avec le LLM et complète `chunk.embed_text`.

    - `prompt_template` contient {section} et {table} (remplacés tels quels).
    - Le cache est sauvegardé après CHAQUE appel : si le programme s'arrête,
      rien n'est perdu ni repayé.
    - Chaque tableau reçoit sa description dans table["summary"].
    Retourne le nombre d'appels réellement faits au LLM.
    """
    cache = load_cache(cache_path)
    calls = 0
    for chunk in chunks:
        descriptions = []
        for table in chunk.tables:
            table_text = table_to_text(table.get("html"), table.get("text", ""), max_chars)
            prompt = (prompt_template
                      .replace("{section}", chunk.heading or "")
                      .replace("{table}", table_text))
            key = _cache_key(prompt)
            if key not in cache:
                cache[key] = _invoke_with_retry(llm, prompt, tries, wait)
                save_cache(cache_path, cache)
                calls += 1
                if delay:
                    time.sleep(delay)
            table["summary"] = cache[key]
            descriptions.append(cache[key])
        chunk.embed_text = build_embed_text(chunk.text, descriptions)
    return calls


def embed_with_table_text(chunks, max_chars=1500):
    """Repli sans LLM (interrupteur use_table_summaries éteint) : le texte des lignes du tableau
    est ajouté tel quel au texte à embarquer."""
    for chunk in chunks:
        parts = [table_to_text(t.get("html"), t.get("text", ""), max_chars) for t in chunk.tables]
        if parts:
            chunk.embed_text = chunk.text + "\n\n" + "\n\n".join(f"Table:\n{p}" for p in parts)
        else:
            chunk.embed_text = chunk.text