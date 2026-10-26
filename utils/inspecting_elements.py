"""Affichages pour vérifier à l'œil le résultat de extraction -> reorder -> clean."""
from collections import Counter
from pathlib import Path


def _flat(text):
    return " ".join((text or "").split())


def show(elements, width=110, start=0, stop=None, page=None):
    """Une ligne par élément. Les textes longs montrent leur DÉBUT et leur FIN
    (pratique pour repérer une phrase coupée). '#' marque les titres."""
    for i, el in enumerate(elements):
        if i < start or (stop is not None and i >= stop):
            continue
        if page is not None and el.metadata.page_number != page:
            continue
        text = _flat(el.text)
        if len(text) > width:
            text = text[: width - 40] + " […] " + text[-35:]
        mark = "#" if el.category == "Title" else " "
        print(f"{i:4d} p{el.metadata.page_number or 0:<2} {el.category[:10]:<10} {mark} {text}")


def outline(elements):
    """Seulement les titres : tu vois d'un coup d'œil la structure et les faux titres."""
    for i, el in enumerate(elements):
        if el.category == "Title":
            print(f"{i:4d} p{el.metadata.page_number or 0:<2} {_flat(el.text)[:90]}")


def stats(elements, log=None, short=25):
    """Chiffres de contrôle."""
    print("gardés par catégorie :", dict(Counter(e.category for e in elements)))
    if log is not None:
        print("supprimés par raison :", dict(Counter(r for _, r in log)))
    if elements:
        print("premier :", _flat(elements[0].text)[:70])
        print("dernier :", _flat(elements[-1].text)[:70])
    courts = [i for i, e in enumerate(elements)
              if e.category != "Title" and len(_flat(e.text)) < short]
    print(f"blocs courts (< {short} caractères) à regarder :", courts)


def export_text(elements, path):
    """Écrit le texte nettoyé dans un fichier, comme le lira la suite du pipeline :
    titres en '## ...', autres blocs séparés par une ligne vide. Lis-le dans l'éditeur."""
    lines = []
    for el in elements:
        text = _flat(el.text)
        lines.append(f"\n## {text}\n" if el.category == "Title"
                     else f"{text}  [p.{el.metadata.page_number}]")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path