"""Remet les éléments d'`unstructured` dans l'ordre de lecture, page par page.

Idée : sur chaque page, on cherche les "gouttières" (bandes verticales vides
entre deux colonnes) à partir des coordonnées des blocs. On n'a donc besoin
de savoir ni si l'article est en 1 ou 2 colonnes, ni où est le milieu de la page.

Usage :
    from reading_order import reorder_document
    ordered, dropped = reorder_document(elements)
"""
from dataclasses import dataclass


@dataclass
class Block:
    """Un élément + son rectangle sur la page (origine en haut à gauche)."""
    el: object
    x0: float          # bord gauche
    x1: float          # bord droit
    y0: float          # bord haut
    y1: float          # bord bas
    page_width: float
    page_height: float


def to_block(el):
    """Retourne le Block de l'élément, ou None s'il n'a pas de coordonnées."""
    c = el.metadata.coordinates
    if c is None or not c.points:
        return None
    xs = [p[0] for p in c.points]
    ys = [p[1] for p in c.points]
    return Block(el, min(xs), max(xs), min(ys), max(ys),
                 c.system.width, c.system.height)


# ---------------------------------------------------------------- bruit
def split_noise(elements, top_ratio=0.07, bottom_ratio=0.93, min_chars=3):
    """Sépare les éléments en (gardés, supprimés).

    Supprimés : texte de moins de `min_chars` caractères (ex. le "×"),
    bloc dont le haut est dans la marge du haut (en-tête, numéro de page),
    bloc dont le haut est dans la marge du bas (pied de page).
    Les éléments sans coordonnées sont gardés.
    Chaque élément supprimé est renvoyé avec sa raison : vérifie-les toujours.
    """
    kept, dropped = [], []
    for el in elements:
        # if len((el.text or "").strip()) < min_chars:
        #     dropped.append((el, "texte trop court"))
        #     continue
        b = to_block(el)
        if b is not None and b.y0 < top_ratio * b.page_height:
            dropped.append((el, "marge du haut (en-tête / numéro de page)"))
        elif b is not None and b.y0 > bottom_ratio * b.page_height:
            dropped.append((el, "marge du bas (pied de page)"))
        else:
            kept.append(el)
    return kept, dropped


# ------------------------------------------------------------ colonnes
def find_gutters(intervals, min_gap=4):
    """Positions x des gouttières, à partir d'intervalles (x0, x1).

    On trie les intervalles par x0 et on les fusionne tant qu'ils se
    chevauchent. Un trou d'au moins `min_gap` entre deux intervalles
    fusionnés est une gouttière (on renvoie son milieu).
    """
    intervals = sorted(intervals)
    gutters = []
    current_end = intervals[0][1]
    for x0, x1 in intervals[1:]:
        if x0 - current_end >= min_gap:
            gutters.append((current_end + x0) / 2)
            current_end = x1
        else:
            current_end = max(current_end, x1)
    return gutters


def order_band(band, min_gap=4):
    """Ordonne une bande de blocs étroits : colonne par colonne, de haut en bas."""
    if not band:
        return []
    gutters = find_gutters([(b.x0, b.x1) for b in band], min_gap)

    def column(b):
        centre = (b.x0 + b.x1) / 2
        return sum(centre > g for g in gutters)   # 0 = colonne la plus à gauche

    return sorted(band, key=lambda b: (column(b), b.y0))


# ---------------------------------------------------------------- page
def reorder_page(page_elements, wide_ratio=0.75, min_gap=4):
    """Ordre de lecture d'une page.

    Un bloc "pleine largeur" coupe la page en bandes : sa largeur est au moins
    `wide_ratio` de la largeur du CONTENU de la page (du bord gauche du bloc le
    plus à gauche au bord droit du bloc le plus à droite), pas de la largeur
    de la page, car les marges en prennent environ 20 %.
    Chaque bande est ordonnée séparément, donc une page peut avoir 2 colonnes
    en haut et 1 colonne en bas.
    Les éléments sans coordonnées sont placés à la fin, dans leur ordre d'origine.
    """
    blocks = [b for b in (to_block(el) for el in page_elements) if b is not None]
    unplaced = [el for el in page_elements if to_block(el) is None]
    if not blocks:
        return unplaced

    content_width = max(b.x1 for b in blocks) - min(b.x0 for b in blocks)

    blocks.sort(key=lambda b: b.y0)
    ordered, band = [], []
    for b in blocks:
        if (b.x1 - b.x0) >= wide_ratio * content_width:   # pleine largeur
            ordered += order_band(band, min_gap)
            band = []
            ordered.append(b)
        else:
            band.append(b)
    ordered += order_band(band, min_gap)
    return [b.el for b in ordered] + unplaced


# ------------------------------------------------------------ document
def reorder_document(elements, **options):
    """Applique le nettoyage du bruit puis l'ordre de lecture, page par page.

    Retourne (éléments_dans_l_ordre, éléments_supprimés_avec_leur_raison).
    `options` : top_ratio, bottom_ratio, min_chars, wide_ratio, min_gap.
    """
    noise_opts = {k: options[k] for k in ("top_ratio", "bottom_ratio", "min_chars")
                  if k in options}
    order_opts = {k: options[k] for k in ("wide_ratio", "min_gap") if k in options}

    pages = {}
    for el in elements:
        pages.setdefault(el.metadata.page_number, []).append(el)

    ordered, dropped = [], []
    for number in sorted(pages, key=lambda n: (n is None, n)):
        kept, bad = split_noise(pages[number], **noise_opts)
        ordered += reorder_page(kept, **order_opts)
        dropped += bad
    return ordered, dropped