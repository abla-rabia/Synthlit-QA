"""Nettoyage des éléments `unstructured` déjà remis dans l'ordre de lecture.

Pipeline :  partition_pdf (hi_res)  ->  reorder_document  ->  clean_document

Chaque règle est une petite fonction qui prend une liste d'éléments et renvoie
(éléments_gardés, [(élément_supprimé, raison), ...]). Rien n'est supprimé en
silence : `clean_document` te rend aussi le journal de tout ce qui a été retiré.

Usage :
    from cleaning import clean_document, summarize
    cleaned, log = clean_document(ordered)
    summarize(log)
"""
import re
import warnings
from collections import Counter

# Les catégories "visuelles" : leur contenu texte est de l'OCR peu fiable ou
# est déjà dans l'élément lui-même.
VISUAL_CATEGORIES = {"Table", "Image", "Formula"}

# Sections sans intérêt pour tes questions (comparées sans numéro, en minuscules).
DROP_SECTIONS = {
    "conflict of interest", "conflicts of interest",
    "declaration of competing interest", "declaration of interest",
    "acknowledgement", "acknowledgements", "acknowledgment", "acknowledgments",
    "funding", "author contributions", "data availability statement",
}

# Lignes parasites (adresse e-mail = donnée personnelle : tu ne veux pas l'indexer).
BOILERPLATE = [
    r"[\w.+-]+@[\w-]+\.[\w.-]+",         # adresse e-mail
    r"^\W*corresponding author",
    r"^available online at",
]

REF_TITLE = re.compile(r"^\s*(\d+\.?\s*)?(references|bibliography)\s*$", re.IGNORECASE)
ABSTRACT = re.compile(r"^\s*abstract\b", re.IGNORECASE)

# Ligatures typographiques : "beneﬁcial" -> "beneficial". Volontairement une
# liste explicite : NFKC aurait aussi transformé "mm²" en "mm2".
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
CID = re.compile(r"\(cid:\d+\)")                      # résidu d'encodage de police
HYPHEN_BREAK = re.compile(r"(\w+)- ([a-z]+)")         # "evalua- tion", "MRI- based"
SUSPENDED = {"and", "or", "to"}                       # "T2- and T1-weighted" : à garder


def _norm(text):
    """Texte comparable : ligatures remplacées, espaces réduits, minuscules."""
    for old, new in LIGATURES.items():
        text = (text or "").replace(old, new)
    return re.sub(r"\s+", " ", text).strip().lower()


def _box(el):
    """(x0, y0, x1, y1) de l'élément, ou None s'il n'a pas de coordonnées."""
    c = el.metadata.coordinates
    if c is None or not c.points:
        return None
    xs = [p[0] for p in c.points]
    ys = [p[1] for p in c.points]
    return min(xs), min(ys), max(xs), max(ys)


def _inside_ratio(inner, outer):
    """Part (0 à 1) de la surface de `inner` qui se trouve dans `outer`."""
    w = min(inner[2], outer[2]) - max(inner[0], outer[0])
    h = min(inner[3], outer[3]) - max(inner[1], outer[1])
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    if w <= 0 or h <= 0 or area <= 0:
        return 0.0
    return (w * h) / area


# ------------------------------------------------------------------ règles
def cut_references(elements):
    """Coupe à partir du titre 'References' (et tout ce qui suit)."""
    for i, el in enumerate(elements):
        if el.category == "Title" and REF_TITLE.match(el.text or ""):
            return elements[:i], [(e, "bibliographie") for e in elements[i:]]
    warnings.warn("Aucun titre 'References' trouvé : rien n'a été coupé.")
    return elements, []


def drop_front_matter(elements):
    """Supprime tout ce qui précède le résumé (titre, auteurs, affiliations).

    Le titre, les auteurs et l'année sont déjà dans sources.csv.
    """
    for i, el in enumerate(elements):
        page = el.metadata.page_number or 1
        if page <= 2 and el.category in ("Title", "NarrativeText") and ABSTRACT.match(el.text or ""):
            return elements[i:], [(e, "avant le résumé") for e in elements[:i]]
    warnings.warn("Aucun 'Abstract' trouvé dans les 2 premières pages : rien n'a été coupé.")
    return elements, []


def drop_inside_visuals(elements, min_inside=0.8):
    """Supprime les Image / Formula, et tout bloc situé DANS un Table, Image ou Formula.

    Ça retire les cellules de tableau recopiées, le texte des figures et l'OCR
    illisible. L'élément Table lui-même et les légendes (hors du cadre) restent.
    """
    visuals = {}
    for el in elements:
        if el.category in VISUAL_CATEGORIES and _box(el):
            visuals.setdefault(el.metadata.page_number, []).append((el, _box(el)))

    kept, dropped = [], []
    for el in elements:
        if el.category in ("Image", "Formula"):
            dropped.append((el, f"{el.category} (OCR peu fiable)"))
            continue
        box = _box(el)
        if el.category != "Table" and box is not None:
            container = next((v for v, vbox in visuals.get(el.metadata.page_number, [])
                              if v is not el and _inside_ratio(box, vbox) >= min_inside), None)
            if container is not None:
                dropped.append((el, f"à l'intérieur d'un bloc {container.category}"))
                continue
        kept.append(el)
    return kept, dropped


def drop_boilerplate(elements, patterns=BOILERPLATE, max_chars=200):
    """Supprime les courtes lignes parasites (e-mail, 'Corresponding author'...)."""
    regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
    kept, dropped = [], []
    for el in elements:
        text = (el.text or "").strip()
        hit = next((r.pattern for r in regexes if len(text) <= max_chars and r.search(text)), None)
        if hit:
            dropped.append((el, f"texte parasite ({hit})"))
        else:
            kept.append(el)
    return kept, dropped


def _section_name(title):
    name = re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", title or "")
    return re.sub(r"[\s:.]+$", "", name).strip().lower()


def drop_sections(elements, names=DROP_SECTIONS):
    """Supprime les sections inutiles (remerciements, conflits d'intérêts...)."""
    kept, dropped, skipping = [], [], False
    for el in elements:
        if el.category == "Title":
            skipping = _section_name(el.text) in names
        if skipping:
            dropped.append((el, "section écartée"))
        else:
            kept.append(el)
    return kept, dropped


def drop_duplicates(elements, window=3, min_tail=8):
    """Supprime les UncategorizedText qui recopient un bloc voisin.

    Doublon  : texte identique à l'un des `window` blocs gardés précédents, ou
               texte qui termine le bloc précédent (au moins `min_tail` caractères).
    Orphelin : tout autre UncategorizedText (ex. dernière ligne d'un paragraphe)
               est GARDÉ : il se recolle au paragraphe au moment du regroupement.
    """
    kept, dropped = [], []
    for el in elements:
        text = _norm(el.text)
        if el.category == "UncategorizedText" and text and kept:
            recent = [_norm(k.text) for k in kept[-window:]]
            same = text in recent
            tail = len(text) >= min_tail and recent[-1].endswith(text)
            if same or tail:
                dropped.append((el, "doublon"))
                continue
        kept.append(el)
    return kept, dropped


# --------------------------------------------------------- normalisation
def build_vocab(elements):
    """Mots (3 lettres ou plus) qui apparaissent entiers dans le document."""
    words = set()
    for el in elements:
        words.update(re.findall(r"[a-z]{3,}", _norm(el.text)))
    return words


def normalize_text(text, vocab):
    """Ligatures, résidus (cid:..), mots coupés par un tiret, espaces."""
    for old, new in LIGATURES.items():
        text = (text or "").replace(old, new)
    text = CID.sub("", text)

    def join(m):
        a, b = m.group(1), m.group(2)
        if b in SUSPENDED:                    # "T2- and T1-weighted" : on laisse
            return m.group(0)
        if (a + b).lower() in vocab:          # "evalua- tion" -> "evaluation"
            return a + b
        return f"{a}-{b}"                     # "MRI- based"   -> "MRI-based"

    text = HYPHEN_BREAK.sub(join, text)
    return re.sub(r"[ \t]+", " ", text).strip()


# -------------------------------------------------------------- pipeline
def clean_document(elements, drop_section_names=DROP_SECTIONS):
    """Applique toutes les règles dans l'ordre. Retourne (éléments, journal).

    Attention : le texte des éléments gardés est modifié sur place.
    """
    log = []
    steps = [
        cut_references,
        drop_front_matter,
        drop_inside_visuals,
        drop_boilerplate,
        lambda els: drop_sections(els, drop_section_names),
        drop_duplicates,
    ]
    for step in steps:
        elements, dropped = step(elements)
        log += dropped

    vocab = build_vocab(elements)
    for el in elements:
        el.text = normalize_text(el.text, vocab)
    return elements, log


def summarize(log, examples=2):
    """Affiche combien d'éléments chaque raison a supprimés, avec des exemples."""
    by_reason = {}
    for el, reason in log:
        by_reason.setdefault(reason, []).append(el)
    for reason, els in Counter({r: len(e) for r, e in by_reason.items()}).most_common():
        print(f"{els:4d} x {reason}")
        for el in by_reason[reason][:examples]:
            print(f"        p.{el.metadata.page_number} {el.category}: {(el.text or '')[:60]!r}")