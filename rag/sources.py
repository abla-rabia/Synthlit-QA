"""Lecture de data/sources_clean.csv (une ligne par article) et citations courtes.

Sert à l'ingestion (en-tête de chaque chunk), à la page Crédits et, plus tard, au
catalogue donné au LLM de réponse.
"""
import csv
import re
import unicodedata


def _norm(name):
    """'Année ' -> 'annee' : sans accents, sans espaces autour, en minuscules."""
    name = unicodedata.normalize("NFKD", name or "")
    return "".join(c for c in name if not unicodedata.combining(c)).strip().lower()


def load_sources(path):
    """Retourne {article_id: {article_id, file, title, authors, year, link, license, type}}.

    article_id = la colonne ID sans ".pdf" ; `file` = le nom du PDF dans data/pdfs/.
    Le séparateur (tabulation ou virgule) est détecté tout seul.
    """
    sources = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        header = f.readline()
        f.seek(0)
        delimiter = "\t" if header.count("\t") > header.count(",") else ","
        for raw in csv.DictReader(f, delimiter=delimiter):
            row = {_norm(k): (v or "").strip() for k, v in raw.items() if k}

            def pick(prefix, row=row):
                return next((v for k, v in row.items() if k.startswith(prefix)), "")

            file_id = pick("id")
            if not file_id:
                continue
            is_pdf = file_id.lower().endswith(".pdf")
            article_id = file_id[:-4] if is_pdf else file_id
            sources[article_id] = {
                "article_id": article_id,
                "file": file_id if is_pdf else file_id + ".pdf",
                "title": pick("titre"),
                "authors": pick("auteur"),
                "year": pick("annee"),
                "link": pick("lien"),
                "license": pick("licen"),
                "type": pick("type"),
            }
    return sources


def short_authors(authors):
    """'Sanuwani Dayarathna, Kh Islam, …' -> 'Dayarathna et al.' (un seul auteur : son nom).

    Hypothèse : 'Prénom Nom' séparés par des virgules ou des points-virgules.
    Pour 'Nom, Prénom ; Nom, Prénom', utilise le point-virgule comme séparateur.
    """
    text = (authors or "").strip()
    if not text:
        return ""
    if "et al" in text.lower():
        first = text.lower().split("et al")[0]
        first = text[:len(first)].strip(" ,.;")
        return f"{first.split()[-1]} et al." if first else ""
    parts = text.split(";") if ";" in text else re.split(r",| and | & ", text)
    parts = [p.strip() for p in parts if p.strip()]
    first = parts[0]
    if "," in first:                                  # "Nom, Prénom"
        surname = first.split(",")[0].split()[-1]
    else:
        tokens = first.split()
        initials = len(tokens) > 1 and len(tokens[-1]) <= 2 and tokens[-1].isupper()
        surname = tokens[0] if initials else tokens[-1]   # "Wang T" (nom + initiales) ou "Tao Wang"
    if len(surname) > 1 and surname.isupper():            # "BAYDOUN" -> "Baydoun"
        surname = surname.title()
    return surname if len(parts) == 1 else f"{surname} et al."


def short_citation(source):
    """'Dayarathna et al., 2024' (ou le début du titre si les auteurs manquent)."""
    authors = short_authors(source.get("authors", ""))
    year = source.get("year", "")
    if authors and year:
        return f"{authors}, {year}"
    return authors or (source.get("title", "") or "")[:60]


def catalogue_text(sources):
    """Catalogue compact des articles, donné au LLM de réponse (cité [catalogue]).

    Une ligne par article : '- Dayarathna et al., 2024 — Titre (revue)'.
    """
    lines = []
    for source in sorted(sources.values(), key=lambda s: (s.get("year", ""), s["article_id"])):
        kind = f" ({source['type']})" if source.get("type") else ""
        lines.append(f"- {short_citation(source)} — {source.get('title', '')}{kind}")
    return "\n".join(lines)