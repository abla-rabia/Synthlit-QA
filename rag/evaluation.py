"""Évaluation : questions + gold -> mesures automatiques (recall@10, recall@5, refus, citations)
et fichiers à relire à la main (fidélité, hors sujet).

Une question (YAML) :
    - id: q01
      type: definition                  # libre ; "offtopic" pour les questions hors sujet
      question: Which generative models are used for PET synthesis from MRI?
      gold: 2022_rajagopal_synthetic-pet-from-mri-3d | 2.1 | pages 3-4     # ou "aucun" si hors sujet
      reponse_reference: Une phrase avec la bonne réponse.
      heldout: false                    # true = question gardée de côté (jamais utilisée pour régler)

`gold` peut être une liste (plusieurs passages valables : un seul suffit pour réussir).
Règle de réussite : un chunk du MÊME article dont les pages recoupent celles du gold.
"""
import csv
import json
import re
from pathlib import Path

import yaml

OFFTOPIC_TYPES = {"offtopic", "horssujet"}
NO_GOLD_TYPES = OFFTOPIC_TYPES | {"catalogue"}      # "catalogue" : réponse prise dans le catalogue, pas dans un passage
NO_GOLD_WORDS = {"aucun", "aucune", "none", "no", "n/a", "na", "rien", "hors", "nothing", "null"}


def _type_key(value):
    return re.sub(r"[^a-z]", "", (value or "").lower())


def _parse_pages(text):
    numbers = [int(n) for n in re.findall(r"\d+", str(text))]
    return (min(numbers), max(numbers)) if numbers else (None, None)


def parse_gold(value):
    """'article | section | pages 3-4'  (ou un dict, ou une liste de ceux-là, ou 'aucun') -> liste de dicts."""
    if value is None or value == "" or value == []:
        return []
    items = value if isinstance(value, list) else [value]
    gold = []
    for item in items:
        if isinstance(item, dict):
            article, section = item.get("article", ""), item.get("section", "")
            start, end = _parse_pages(item.get("pages", ""))
        else:
            text = str(item).strip()
            first_word = re.sub(r"[^a-zà-ÿ/]", " ", text.lower()).split()[:1]
            if not text or text == "-" or (first_word and first_word[0] in NO_GOLD_WORDS):
                continue                              # "aucun", "Aucune.", "none", "N/A", "hors sujet"…
            parts = [p.strip() for p in text.split("|")]
            article = parts[0]
            section = parts[1] if len(parts) > 1 else ""
            start, end = _parse_pages(parts[2]) if len(parts) > 2 else (None, None)
        gold.append({"article": str(article).strip(), "section": str(section or "").strip(),
                     "start": start, "end": end})
    return gold


def load_questions(path, sources=None):
    """Lit et VALIDE le fichier (erreur claire si un id est en double, un gold manque, un article est inconnu)."""
    items = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    questions, seen = [], set()
    for raw in items:
        for key in ("id", "type", "question"):
            if not raw.get(key):
                raise ValueError(f"{raw.get('id', '?')} : champ '{key}' manquant")
        qid = str(raw["id"])
        if qid in seen:
            raise ValueError(f"id en double : {qid}")
        seen.add(qid)
        gold = parse_gold(raw.get("gold"))
        offtopic = _type_key(raw["type"]) in OFFTOPIC_TYPES
        catalogue = _type_key(raw["type"]) == "catalogue"
        if (offtopic or catalogue) and gold:
            raise ValueError(f"{qid} : type {raw['type']} mais gold lu = {raw.get('gold')!r} "
                             "(écris exactement  gold: aucun)")
        if not (offtopic or catalogue) and not gold:
            raise ValueError(f"{qid} : gold manquant")
        for g in gold:
            if sources is not None and g["article"] not in sources:
                raise ValueError(f"{qid} : article inconnu '{g['article']}' (fautes de frappe ?)")
        questions.append({"id": qid, "type": str(raw["type"]), "question": str(raw["question"]).strip(),
                          "gold": gold, "offtopic": offtopic, "catalogue": catalogue, "heldout": bool(raw.get("heldout", False)),
                          "reference": str(raw.get("reponse_reference") or raw.get("reference") or "").strip()})
    return questions


# ------------------------------------------------------------------ mesures automatiques
def is_hit(hit, gold):
    """Ce chunk contient-il (au moins en partie) le passage gold ?"""
    for g in gold:
        if hit.article_id != g["article"]:
            continue
        if g["start"] is None or (hit.page_start <= g["end"] and hit.page_end >= g["start"]):
            return True
    return False


def first_rank(hits, gold):
    """Position (1 = meilleure) du premier chunk gold dans la liste, ou None."""
    for position, hit in enumerate(hits, start=1):
        if is_hit(hit, gold):
            return position
    return None


def evaluate_question(question, answer=None, error=""):
    """Une ligne de résultats. `answer` est un rag.types.Answer (None si erreur)."""
    row = {"id": question["id"], "type": question["type"], "heldout": question["heldout"],
           "offtopic": question["offtopic"], "catalogue": question.get("catalogue", False), "error": error, "recall10": None, "recall5": None,
           "rank10": None, "rank5": None, "refused": None, "retries": None, "removed": None,
           "n_citations": None, "used_catalogue": None, "trace_ok": None}
    if answer is None:
        return row
    retrieval = answer.retrieval
    if question["gold"]:
        row["rank10"] = first_rank(retrieval.candidates, question["gold"])
        row["rank5"] = first_rank(retrieval.final, question["gold"])
        row["recall10"] = int(row["rank10"] is not None)
        row["recall5"] = int(row["rank5"] is not None)
    row.update(refused=int(answer.refused), retries=answer.retries, removed=list(answer.removed),
               n_citations=len(answer.citations), used_catalogue=int(answer.used_catalogue))
    row["trace_ok"] = int(not answer.removed and (answer.refused or answer.used_catalogue
                                                  or len(answer.citations) > 0))
    return row


def _mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


def stats(rows):
    rows = [r for r in rows if not r["error"]]
    scored = [r for r in rows if r["recall10"] is not None]
    off = [r for r in rows if r["offtopic"]]
    cat = [r for r in rows if r.get("catalogue")]
    by_type = {}
    for r in scored:
        by_type.setdefault(r["type"], []).append(r["recall5"])
    return {"n": len(rows), "n_avec_gold": len(scored), "n_hors_sujet": len(off),
            "recall@10": _mean(r["recall10"] for r in scored),
            "recall@5": _mean(r["recall5"] for r in scored),
            "recall@5 par type": {t: _mean(v) for t, v in by_type.items()},
            "refus a tort (question avec gold refusee)": sum(r["refused"] for r in scored),
            "hors sujet refuses": f"{sum(r['refused'] for r in off)}/{len(off)}",
            "citations valides": _mean(r["trace_ok"] for r in rows),
            "n_catalogue": len(cat),
            "catalogue cite [catalogue]": _mean(r["used_catalogue"] for r in cat)}


def summarize(rows, manual=None):
    """Résumé global, dev (réglage) et held-out (jamais utilisé pour régler), + mesures manuelles."""
    summary = {"toutes": stats(rows),
               "dev": stats([r for r in rows if not r["heldout"]]),
               "heldout": stats([r for r in rows if r["heldout"]])}
    summary["erreurs"] = [r["id"] for r in rows if r["error"]]
    if manual:
        done = [m for m in manual.values() if m["total"]]
        total = sum(m["total"] for m in done)
        off = [m["offtopic_ok"] for m in manual.values() if m["offtopic_ok"] is not None]
        summary["manuel"] = {
            "fidelite (affirmations soutenues / total)": round(sum(m["supported"] for m in done) / total, 3) if total else None,
            "questions relues": len(done),
            "hors sujet corrects": _mean(off)}
    return summary


def format_summary(summary):
    lines = []
    for name in ("toutes", "dev", "heldout"):
        s = summary[name]
        if not s["n"]:
            continue
        lines.append(f"== {name} ({s['n']} questions : {s['n_avec_gold']} avec gold, {s['n_hors_sujet']} hors sujet)")
        for key in ("recall@10", "recall@5", "refus a tort (question avec gold refusee)",
                    "hors sujet refuses", "citations valides"):
            lines.append(f"   {key}: {s[key]}")
        lines.append(f"   recall@5 par type: {s['recall@5 par type']}")
        if s["n_catalogue"]:
            lines.append(f"   questions catalogue ({s['n_catalogue']}) citant [catalogue]: {s['catalogue cite [catalogue]']}")
    if summary["erreurs"]:
        lines.append(f"!! erreurs (exclues des moyennes) : {summary['erreurs']}")
    if "manuel" in summary:
        lines.append("== mesures manuelles")
        lines += [f"   {k}: {v}" for k, v in summary["manuel"].items()]
    return "\n".join(lines)


# ------------------------------------------------------------------ fichiers
RESULT_COLUMNS = ["id", "type", "heldout", "recall10", "recall5", "rank10", "rank5", "refused",
                  "retries", "removed", "n_citations", "used_catalogue", "trace_ok", "error"]


def write_results(folder, rows):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "results.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    (folder / "rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def write_manual_template(folder, rows):
    """À remplir à la main. `offtopic_ok` est pré-rempli par le refus automatique : à vérifier."""
    path = Path(folder) / "manual.csv"
    if path.exists():                                  # ne jamais écraser ce que tu as rempli
        return path
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "claims_total", "claims_supported", "offtopic_ok"])
        for r in rows:
            guess = r["refused"] if r["offtopic"] and not r["error"] else ""
            writer.writerow([r["id"], "", "", guess])
    return path


def read_manual(path):
    """manual.csv -> {id: {total, supported, offtopic_ok}} (cases vides = non remplies)."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        head = f.readline()
        f.seek(0)
        delimiter = ";" if head.count(";") > head.count(",") else ","
        out = {}
        for row in csv.DictReader(f, delimiter=delimiter):
            def num(key):
                value = (row.get(key) or "").strip()
                return int(value) if value.isdigit() else None
            out[row["id"]] = {"total": num("claims_total"), "supported": num("claims_supported") or 0,
                              "offtopic_ok": num("offtopic_ok")}
    return out


def write_review(path, results, settings_snapshot):
    """review.md : pour chaque question, la réponse et les passages à comparer (pour la fidélité)."""
    lines = ["# Relecture manuelle", "",
             "Pour chaque réponse : compte les affirmations (claims_total) et combien sont bien dans les "
             "passages cités (claims_supported), puis remplis manual.csv.", "",
             f"Réglages du run : `{json.dumps(settings_snapshot, ensure_ascii=False)}`", ""]
    for question, answer, row in results:
        lines += [f"---\n\n## {question['id']} · {question['type']}", f"**Question :** {question['question']}"]
        if question["reference"]:
            lines.append(f"**Référence :** {question['reference']}")
        gold = " ; ".join(f"{g['article']} | {g['section']} | p. {g['start']}-{g['end']}" for g in question["gold"])
        lines.append(f"**Gold :** {gold or 'aucun (hors sujet ou catalogue)'}")
        if answer is None:
            lines += [f"**ERREUR :** {row['error']}", ""]
            continue
        lines += [f"**Rang du gold :** top10 = {row['rank10']}, top5 = {row['rank5']}", "",
                  "**Réponse du système :**", "", answer.text, "", "**Passages envoyés au LLM :**", ""]
        for n, hit in enumerate(answer.hits, start=1):
            mark = " ✔ GOLD" if not question["offtopic"] and is_hit(hit, question["gold"]) else ""
            snippet = hit.text.replace("\n", " ")
            snippet = snippet[:700] + ("…" if len(snippet) > 700 else "")
            tables = f" (+{len(hit.tables)} tableau(x))" if hit.tables else ""
            lines += [f"- **[{n}]** {hit.header} ({hit.pages}){mark}{tables}", f"  > {snippet}"]
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


# ------------------------------------------------------------------ diagnostic
def explain_gold(retriever, question, k=100):
    """Pour chaque chunk du gold : son rang dans la recherche sémantique et dans BM25 (par requête),
    et s'il est dans les 10 candidats / les 5 retenus. Sert à comprendre OÙ un bon passage se perd."""
    result = retriever.retrieve(question["question"])
    gold_ids = [cid for cid, h in retriever.hits.items() if is_hit(h, question["gold"])]
    ranks = {"vector": {}, "keyword": {}}
    for query in result.queries:
        for name, searcher in (("vector", retriever.vector), ("keyword", retriever.keyword)):
            found = searcher.search(query, k)
            ranks[name][query] = {cid: found.index(cid) + 1 for cid in gold_ids if cid in found}
    candidates = {h.chunk_id for h in result.candidates}
    final = {h.chunk_id for h in result.final}
    rows = []
    for cid in gold_ids:
        vec = [ranks["vector"][q].get(cid) for q in result.queries]
        kw = [ranks["keyword"][q].get(cid) for q in result.queries]
        best = min([r for r in vec + kw if r] or [10 ** 9])
        rows.append({"chunk_id": cid, "header": retriever.hits[cid].header, "vector": vec, "keyword": kw,
                     "in_candidates": cid in candidates, "in_final": cid in final, "best": best})
    rows.sort(key=lambda r: r["best"])
    return {"queries": result.queries, "rows": rows}