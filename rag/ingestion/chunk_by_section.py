"""Regroupe les éléments nettoyés d'un article en chunks : une (sous-)section = un chunk.

Pipeline :  partition -> reorder_document -> clean_document -> chunk_by_section

Décisions de ton journal appliquées ici :
- un chunk = une section ou une sous-section ; on garde le nom de la section ET de la sous-section ;
- une section trop longue est coupée par paragraphes (puis par phrases si besoin),
  avec un petit recouvrement fait de phrases entières ;
- tableaux : le HTML est gardé à côté du chunk (clé "tables"), pas dans le texte ;
- légendes de figures et de tableaux : ajoutées à la fin du chunk ;
- pages : page_start / page_end pour chaque chunk.

Usage :
    from chunk_by_section import chunk_by_section, make_token_counter, summarize_chunks
    count_tokens = make_token_counter("BAAI/bge-small-en-v1.5")
    chunks = chunk_by_section(cleaned, "2022_zimmermann", count_tokens)
    summarize_chunks(chunks)
"""
import re
from dataclasses import dataclass, field, asdict
from statistics import median

# "2.1.3 Vision transformers" : numéro (1 à 3 niveaux), puis un mot qui commence par une majuscule
NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+[A-Z]")
MAX_SECTION_NUMBER = 20            # "2022 The Authors" n'est pas un titre de section
LABEL = re.compile(r"^(table|fig\.?|figure)\s*\d+", re.IGNORECASE)
# légende : "Fig. 4. Overview…", "Table 1" ; mais pas "Fig. 1 provides a chronology…"
CAPTION = re.compile(r"^(table|fig\.?|figure)\s*\d+\s*([.:]|$)", re.IGNORECASE)
SPACED = re.compile(r"^(?:[A-Za-z] )+[A-Za-z]$")            # "A B S T R A C T"
SENTENCE_END = (".", "?", "!", ":", ";", ")", "]")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")
MAX_HEADING_CHARS = 120
NOT_HEADING = {"Table", "Image", "Formula", "ListItem"}
KNOWN_HEADINGS = {
    "abstract", "introduction", "background", "methods", "materials and methods",
    "results", "results and discussion", "discussion", "conclusion", "conclusions",
    "limitations", "future work", "related work",
}


# ------------------------------------------------------------------ données
@dataclass
class Para:
    """Un paragraphe (ou une légende) et les pages qu'il couvre."""
    text: str
    page_start: int
    page_end: int


@dataclass
class TableRef:
    html: str | None
    text: str
    page: int


@dataclass
class Unit:
    """Une (sous-)section avant la découpe par taille."""
    section: str | None
    sous_section: str | None
    items: list = field(default_factory=list)       # Para | TableRef, dans l'ordre
    captions: list = field(default_factory=list)    # Para


@dataclass
class Chunk:
    chunk_id: str
    article_id: str
    section: str | None
    sous_section: str | None
    page_start: int
    page_end: int
    text: str
    tables: list                                    # [{"page", "html", "text"}]
    n_tokens: int
    chunk_type: str = "text"
    embed_text: str = ""        # texte envoyé au modèle d'embedding (rempli ici, complété par tables.py)

    @property
    def heading(self):
        """Le titre le plus précis (celui de la citation)."""
        return self.sous_section or self.section

    def to_dict(self):
        return asdict(self)


# ------------------------------------------------------------------ titres
def squeeze(text):
    return re.sub(r"\s+", " ", text or "").strip()


def display_title(text):
    """'A B S T R A C T' -> 'Abstract' ; sinon le titre tel quel."""
    text = squeeze(text)
    return text.replace(" ", "").capitalize() if SPACED.match(text) else text


def heading_level(el, titles_fallback=False):
    """0 si l'élément n'est pas un titre de section, sinon son niveau (1, 2, 3…).

    Règles : numérotation ("2.1 Patient cohort" -> niveau 2) ou nom connu
    ("Abstract", "Conclusion" -> niveau 1). Les "Table N" / "Figure N" ne sont
    jamais des titres. Si l'article n'a presque aucun titre numéroté,
    `titles_fallback=True` accepte les `Title` d'unstructured (niveau 1).
    """
    text = squeeze(el.text)
    if not text or len(text) > MAX_HEADING_CHARS or LABEL.match(text):
        return 0
    if el.category in NOT_HEADING:
        return 0
    if SPACED.match(text):
        text = text.replace(" ", "")
    m = NUMBERED.match(text)
    if m and int(m.group(1).split(".")[0]) <= MAX_SECTION_NUMBER \
            and not text.endswith((".", "?", "!", ",", ";", ":")):
        return len(m.group(1).split("."))
    if re.sub(r"[^a-z ]", "", text.lower()).strip() in KNOWN_HEADINGS:
        return 1
    if titles_fallback and el.category == "Title":
        return 1
    return 0


# ------------------------------------------------- passe 1 : regrouper
def _continues(previous, new):
    """Le bloc `new` continue-t-il la phrase de `previous` ? (queue orpheline, changement de colonne ou de page)"""
    return not previous.endswith(SENTENCE_END) and (new[0].islower() or new[0].isdigit())


def _add_text(unit, text, page):
    last = unit.items[-1] if unit.items else None
    if isinstance(last, Para) and _continues(last.text, text):
        last.text += " " + text
        last.page_end = page
    else:
        unit.items.append(Para(text, page, page))


def _close(units, unit):
    if unit.items or unit.captions:        # un titre sans rien dessous n'est pas gardé
        units.append(unit)


def group_into_units(elements, min_headings=3):
    """Parcourt les éléments et crée une Unit par (sous-)section."""
    fallback = sum(heading_level(el) > 0 for el in elements) < min_headings
    units, section, sous = [], None, None
    current, page = Unit(None, None), 1

    for el in elements:
        page = el.metadata.page_number or page
        level = heading_level(el, titles_fallback=fallback)
        if level:
            _close(units, current)
            title = display_title(el.text)
            if level == 1:
                section, sous = title, None
            else:
                sous = title                 # la section parente est conservée
            current = Unit(section, sous)
            continue

        text = squeeze(el.text)
        if el.category == "Table":
            html = getattr(el.metadata, "text_as_html", None)
            current.items.append(TableRef(html, text, page))
        elif not text:
            continue
        elif el.category == "FigureCaption" or CAPTION.match(text):
            current.captions.append(Para(text, page, page))
        else:
            _add_text(current, text, page)

    _close(units, current)
    return units


# ----------------------------------------- passe 2 : couper selon les jetons
def _sentences(text):
    return SENTENCE_SPLIT.split(text)


def _hard_split(sentence, count_tokens, limit):
    """Dernier recours : une phrase plus longue que la limite est coupée par mots."""
    if count_tokens(sentence) <= limit:
        return [sentence]
    out, current = [], []
    for word in sentence.split():
        if current and count_tokens(" ".join(current + [word])) > limit:
            out.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        out.append(" ".join(current))
    return out


def split_paragraph(para, count_tokens, limit):
    """Un paragraphe de plus de `limit` jetons est coupé par phrases."""
    if count_tokens(para.text) <= limit:
        return [para]
    parts, current, used = [], [], 0
    for sentence in _sentences(para.text):
        for piece in _hard_split(sentence, count_tokens, limit):
            n = count_tokens(piece)
            if current and used + n > limit:
                parts.append(" ".join(current))
                current, used = [], 0
            current.append(piece)
            used += n
    if current:
        parts.append(" ".join(current))
    return [Para(t, para.page_start, para.page_end) for t in parts]


def tail_text(text, count_tokens, overlap_tokens):
    """Les dernières phrases entières qui tiennent dans `overlap_tokens` (recouvrement)."""
    if overlap_tokens <= 0:
        return ""
    kept, used = [], 0
    for sentence in reversed(_sentences(text)):
        n = count_tokens(sentence)
        if used + n > overlap_tokens:
            break
        kept.insert(0, sentence)
        used += n
    return " ".join(kept)


@dataclass
class _Piece:
    paras: list = field(default_factory=list)
    tables: list = field(default_factory=list)
    captions: list = field(default_factory=list)
    tokens: int = 0


def split_unit(unit, count_tokens, max_tokens, overlap_tokens):
    """Découpe une Unit en morceaux de `max_tokens` jetons au plus."""
    assert max_tokens > overlap_tokens >= 0
    limit = max_tokens - overlap_tokens     # un morceau neuf = recouvrement + un bloc <= limit
    pieces, cur = [], _Piece()

    for item in unit.items:
        if isinstance(item, TableRef):      # le HTML ne compte pas dans les jetons du texte
            cur.tables.append(item)
            continue
        for part in split_paragraph(item, count_tokens, limit):
            n = count_tokens(part.text)
            if cur.paras and cur.tokens + n > max_tokens:
                pieces.append(cur)
                prev = cur.paras[-1]
                carry = tail_text(prev.text, count_tokens, overlap_tokens)
                cur = _Piece()
                if carry:
                    cur.paras.append(Para(carry, prev.page_end, prev.page_end))
                    cur.tokens = count_tokens(carry)
            cur.paras.append(part)
            cur.tokens += n

    if unit.captions:                       # légendes : à la fin de la section
        n = sum(count_tokens(c.text) for c in unit.captions)
        if cur.paras and cur.tokens + n > max_tokens:
            pieces.append(cur)
            cur = _Piece()
        cur.captions = list(unit.captions)
        cur.tokens += n

    if cur.paras or cur.tables or cur.captions:
        pieces.append(cur)
    return pieces


# ------------------------------------------------------------- principal
def chunk_by_section(elements, article_id, count_tokens, max_tokens=450,
                     overlap_tokens=60, min_headings=3):
    """Éléments nettoyés (dans l'ordre de lecture) -> liste de Chunk."""
    chunks = []
    for unit in group_into_units(elements, min_headings):
        for piece in split_unit(unit, count_tokens, max_tokens, overlap_tokens):
            blocks = piece.paras + piece.captions
            text = "\n\n".join(b.text for b in blocks)
            pages = [b.page_start for b in blocks] + [b.page_end for b in blocks] \
                    + [t.page for t in piece.tables]
            chunks.append(Chunk(
                chunk_id=f"{article_id}::{len(chunks):03d}",
                article_id=article_id,
                section=unit.section,
                sous_section=unit.sous_section,
                page_start=min(pages),
                page_end=max(pages),
                text=text,
                tables=[{"page": t.page, "html": t.html, "text": t.text} for t in piece.tables],
                n_tokens=count_tokens(text),
                embed_text=text,
            ))
    return chunks


# ------------------------------------------------------------ utilitaires
def make_token_counter(model_name="BAAI/bge-small-en-v1.5"):
    """Compte les jetons avec le tokenizer du modèle d'embedding (pas en caractères)."""
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.model_max_length = 1_000_000          # évite l'avertissement "séquence trop longue"
    return lambda text: len(tokenizer.encode(text, add_special_tokens=False))


def find_long_embed_texts(chunks, count_tokens, limit=512, reserve=25):
    """Chunks dont le texte à embarquer risque d'être tronqué par le modèle.

    `reserve` = jetons de l'en-tête ajouté plus tard ("Dayarathna 2024 · section").
    Retourne [(chunk_id, nombre de jetons), ...] pour ceux qui dépassent `limit`.
    """
    result = []
    for chunk in chunks:
        n = count_tokens(chunk.embed_text) + reserve
        if n > limit:
            result.append((chunk.chunk_id, n))
    return result


def summarize_chunks(chunks, max_tokens=450):
    """Résumé rapide : nombre de chunks, tailles, tableaux."""
    if not chunks:
        print("Aucun chunk.")
        return
    sizes = [c.n_tokens for c in chunks]
    print(f"{len(chunks)} chunks · médiane {median(sizes):.0f} jetons · max {max(sizes)} · "
          f"{sum(s > max_tokens for s in sizes)} au-dessus de {max_tokens} · "
          f"{sum(bool(c.tables) for c in chunks)} avec tableau · "
          f"{sum(s < 30 for s in sizes)} de moins de 30 jetons")