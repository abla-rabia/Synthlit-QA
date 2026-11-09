"""Citations : [1]..[n] pour les passages, [catalogue] pour la liste des articles.

Format strict : un numéro par crochet. "[2][3]" est valide ; "[1, 2]" est converti en "[1][2]"
quand tous les numéros sont des passages valides. Les "[70.8, 95.2]" (valeurs) ne sont pas touchés.
"""
import re

_CITE = re.compile(r"\[(catalogue|\d+)\]", re.IGNORECASE)
_MULTI = re.compile(r"\[(\d+(?:\s*,\s*\d+)+)\]")


_BRACKETS = str.maketrans({"【": "[", "】": "]", "［": "[", "］": "]"})


def normalize_multi(text, n_passages):
    text = text.translate(_BRACKETS)          # le LLM écrit parfois 【1】 (crochets pleine largeur)
    def expand(match):
        numbers = [int(x) for x in re.split(r"\s*,\s*", match.group(1))]
        if all(1 <= n <= n_passages for n in numbers):
            return "".join(f"[{n}]" for n in numbers)
        return match.group(0)
    return _MULTI.sub(expand, text)


def find_citations(text):
    """Liste (dans l'ordre, sans doublon) des citations : des int, ou "catalogue"."""
    found = []
    for raw in _CITE.findall(text):
        item = "catalogue" if raw.lower() == "catalogue" else int(raw)
        if item not in found:
            found.append(item)
    return found


def split_valid(citations, n_passages):
    valid = [c for c in citations if c == "catalogue" or 1 <= c <= n_passages]
    invalid = [c for c in citations if c not in valid]
    return valid, invalid


def remove_invalid(text, n_passages):
    def keep(match):
        raw = match.group(1)
        if raw.lower() == "catalogue" or 1 <= int(raw) <= n_passages:
            return match.group(0)
        return ""
    return re.sub(r"\s?" + _CITE.pattern, keep, text)


def strip_citations(text):
    """Pour l'historique : sans [n] ni [catalogue], les numéros ne se mélangent jamais d'un tour à l'autre."""
    return re.sub(r"\s?" + _CITE.pattern, "", text).strip()