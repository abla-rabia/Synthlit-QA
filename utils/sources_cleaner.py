"""Nettoie data/sources.csv (export Google Sheets) et signale les problèmes.

Usage :
    python clean_sources.py data/sources.csv data/sources_clean.csv

Ne modifie jamais le fichier d'entrée. Écrit le fichier nettoyé et affiche
les avertissements (ils ne bloquent pas l'écriture : tu décides quoi corriger).
"""
import csv
import re
import sys

COLONNES = ["ID", "Titre", "Auteurs", "Année", "Lien", "License",
            "Preuve license", "nb colonnes", "nb pages", "Type article"]
LICENCES_OK = {"CC0", "CC BY", "CC BY 3.0", "CC BY 4.0",
               "CC BY-SA 3.0", "CC BY-SA 4.0"}
TYPES_OK = {"review", "methodes"}

# lien Creative Commons éventuellement coupé par des espaces / retours à la ligne
RE_CC = re.compile(
    r"https?://\s*creativecommons\.org/\s*licenses/\s*[\w-]+/\s*\d\.\d/?",
    re.IGNORECASE)


def espaces(texte):
    """Remplace tout enchaînement d'espaces / retours à la ligne par un espace."""
    return re.sub(r"\s+", " ", texte).strip()


def sans_guillemets(texte):
    return texte.strip().strip('"').strip()


def reparer_liens_cc(texte):
    """Retire les espaces à l'intérieur des liens creativecommons.org."""
    return RE_CC.sub(lambda m: re.sub(r"\s+", "", m.group(0)), texte)


def nettoyer_ligne(ligne):
    ligne = [sans_guillemets(c) for c in ligne]
    ligne = [espaces(c) for c in ligne]
    ligne[4] = re.sub(r"\s+", "", ligne[4])            # Lien : aucun espace
    ligne[6] = reparer_liens_cc(ligne[6])              # Preuve : lien CC réparé
    ligne[6] = re.sub(r"(https?://)\s+", r"\1", ligne[6])
    ligne[9] = ligne[9].lower()                        # Review -> review
    return ligne


def verifier(ligne, ids_vus):
    """Retourne la liste des avertissements pour une ligne nettoyée."""
    id_, titre, auteurs, annee, lien, licence, preuve, cols, pages, type_ = ligne
    w = []
    if id_ in ids_vus:
        w.append("id en double")
    ids_vus.add(id_)
    if not id_.endswith(".pdf"):
        w.append("id ne finit pas par .pdf")
    for nom, val in zip(COLONNES, ligne):
        if not val:
            w.append(f"colonne vide : {nom}")
    if not re.fullmatch(r"(19|20)\d\d", annee):
        w.append(f"année bizarre : {annee!r}")
    if cols not in {"1", "2"}:
        w.append(f"nb colonnes doit être 1 ou 2 : {cols!r}")
    if not pages.isdigit():
        w.append(f"nb pages pas un nombre : {pages!r}")
    if type_ not in TYPES_OK:
        w.append(f"type inconnu : {type_!r}")
    if licence not in LICENCES_OK:
        w.append(f"licence hors liste autorisée : {licence!r}")
    if re.search(r"-nc|-nd|NonCommercial|NoDerivs", preuve, re.IGNORECASE):
        w.append("la preuve contient NC ou ND : à exclure")
    if "creativecommons" not in preuve.lower() and "creative commons" not in preuve.lower():
        w.append("la preuve ne mentionne pas Creative Commons")
    # la version écrite dans License est-elle prouvée ?
    version = re.search(r"\d\.\d", licence)
    if version:
        v = version.group(0)
        if not (re.search(r"licenses/[\w-]+/" + re.escape(v), preuve) or
                re.search(r"(Attribution|CC BY)\s*" + re.escape(v), preuve)):
            w.append(f"version {v} non prouvée par la phrase")
    if re.search(r"\*is is|openaccess|\w-\s\w", preuve):
        w.append("défaut d'extraction possible dans la preuve (lettrine, mot collé ou coupé)")
    return w


def main(entree, sortie):
    with open(entree, encoding="utf-8", newline="") as f:
        debut = f.readline()
    delim = "\t" if "\t" in debut else ","
    with open(entree, encoding="utf-8", newline="") as f:
        lignes = list(csv.reader(f, delimiter=delim))

    entete, corps = lignes[0], lignes[1:]
    if len(entete) != len(COLONNES):
        sys.exit(f"Erreur : {len(entete)} colonnes dans l'en-tête, {len(COLONNES)} attendues")

    propres, ids_vus, total_w = [], set(), 0
    for i, ligne in enumerate(corps, start=2):
        if len(ligne) != len(COLONNES):
            print(f"[ligne {i}] {len(ligne)} colonnes au lieu de {len(COLONNES)} : ignorée")
            total_w += 1
            continue
        ligne = nettoyer_ligne(ligne)
        propres.append(ligne)
        for w in verifier(ligne, ids_vus):
            print(f"[{ligne[0][:40]}] {w}")
            total_w += 1

    with open(sortie, "w", encoding="utf-8", newline="") as f:
        ecr = csv.writer(f)
        ecr.writerow(COLONNES)
        ecr.writerows(propres)
    print(f"\n{len(propres)} lignes écrites dans {sortie} ; {total_w} avertissement(s)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])