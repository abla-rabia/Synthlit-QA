"""Évaluation du RAG : questions + gold -> tableau de résultats -> résumé.

Mesures
  Automatiques : recall@10 (candidats après RRF), recall@5 (après rerank),
                 refus correct (hors sujet refusé / question normale non refusée).
  Manuelle     : fidélité = affirmations soutenues par les passages cités / affirmations totales
                 (tu remplis claims_total et claims_supported dans manual.csv).

Un gold = un article + une section + des pages. Un chunk "retrouve" le gold si c'est le même article
ET si ses pages recoupent celles du gold. Pour une question à plusieurs gold (croisement),
le recall est la part des gold retrouvés (ex. 4 sur 6 = 0.67).
"""
import csv
import json
import re
from pathlib import Path

import yaml

SEP = ";"          # point-virgule : s'ouvre correctement dans Excel en français
RESULT_FIELDS = ["id", "type", "question", "gold_n", "found_10", "found_5", "recall_10", "recall_5",
                 "expects_refusal", "refused", "refusal_ok", "n_citations", "retries", "error"]
MANUAL_FIELDS = ["id", "claims_total", "claims_supported", "note"]
_PAGES_PART = re.compile(r"(?i)^\s*(pages?|pp?\.?)\s*\d")


# ---------- gold ----------
def _pages_from(value):
    """'pages 3-4' / 'p. 5' / 7 / [2, 3] -> (début, fin) ; (None, None) si rien."""
    if value is None or value == "":
        return None, None
    if isinstance(value, (list, tuple)):
        nums = [int(x) for x in value]
    elif isinstance(value, int):
        nums = [value]
    else:
        nums = [int(x) for x in re.findall(r"\d+", str(value))]
    if not nums:
        return None, None
    return nums[0], nums[-1]


def _parse_one(item):
    if isinstance(item, dict):
        article = str(item.get("article", "")).strip()
        start, end = _pages_from(item.get("pages"))
        section = str(item.get("section", "") or "").strip()
    else:
        parts = [p.strip() for p in str(item).split("|")]
        article, section, pages = parts[0], "", None
        for part in parts[1:]:
            if _PAGES_PART.match(part):
                pages = part
            elif not section:
                section = part
        start, end = _pages_from(pages)
    if not article:
        raise ValueError(f"gold sans article : {item!r}")
    return {"article": article, "section": section, "start": start, "end": end}


def parse_gold(value):
    """Gold -> liste de {article, section, start, end}. 'aucun' / vide -> []."""
    if value is None:
        return []
    if isinstance(value, str) and value.strip().lower() in ("", "aucun", "none"):
        return []
    items = value if isinstance(value, list) else [value]
    return [_parse_one(i) for i in items]


def is_hit(hit, gold):
    """Le chunk est du bon article et ses pages recoupent celles du gold (article seul si pas de pages)."""
    if hit.article_id != gold["article"]:
        return False
    if gold["start"] is None:
        return True
    h_start = hit.page_start or 0
    h_end = hit.page_end or h_start
    return h_start <= gold["end"] and h_end >= gold["start"]


# ---------- questions ----------
def load_questions(path, known_articles=None):
    """Lit questions.yaml, vérifie la forme. Renvoie une liste de dicts avec 'gold_items' ajouté."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("questions.yaml doit contenir une liste de questions (lignes qui commencent par '- id:').")
    seen, out = set(), []
    for i, q in enumerate(data, 1):
        for key in ("id", "question", "type"):
            if not q.get(key):
                raise ValueError(f"Question n°{i} : champ '{key}' manquant.")
        qid = str(q["id"])
        if qid in seen:
            raise ValueError(f"Identifiant en double : {qid}")
        seen.add(qid)
        gold = parse_gold(q.get("gold"))
        if q["type"] == "hors_sujet" and gold:
            raise ValueError(f"{qid} : une question hors_sujet doit avoir 'gold: aucun'.")
        if q["type"] != "hors_sujet" and not gold:
            raise ValueError(f"{qid} : il manque le gold (article | section | pages X-Y).")
        if known_articles is not None:
            for g in gold:
                if g["article"] not in known_articles:
                    raise ValueError(f"{qid} : article inconnu '{g['article']}' (faute de frappe ?).")
        out.append({**q, "id": qid, "gold_items": gold})
    return out


# ---------- une question ----------
def _covered(hits, gold_items):
    return [any(is_hit(h, g) for h in hits) for g in gold_items]


def evaluate_question(question, answer):
    """Ligne de résultat (dict) pour une question et la Answer du système."""
    gold = question["gold_items"]
    r = answer.retrieval
    c10 = _covered(r.candidates, gold) if r else []
    c5 = _covered(r.final, gold) if r else []
    expects_refusal = not gold
    n = len(gold)
    return {
        "id": question["id"], "type": question["type"], "question": question["question"],
        "gold_n": n,
        "found_10": sum(c10), "found_5": sum(c5),
        "recall_10": round(sum(c10) / n, 3) if n else "",
        "recall_5": round(sum(c5) / n, 3) if n else "",
        "expects_refusal": int(expects_refusal), "refused": int(bool(answer.refused)),
        "refusal_ok": int(bool(answer.refused) == expects_refusal),
        "n_citations": len(answer.citations), "retries": answer.retries, "error": "",
    }


def error_row(question, exc):
    return {"id": question["id"], "type": question["type"], "question": question["question"],
            "gold_n": len(question["gold_items"]), "found_10": "", "found_5": "", "recall_10": "",
            "recall_5": "", "expects_refusal": int(not question["gold_items"]), "refused": "",
            "refusal_ok": "", "n_citations": "", "retries": "", "error": f"{type(exc).__name__}: {exc}"}


# ---------- fichiers ----------
def write_results(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESULT_FIELDS, delimiter=SEP)
        w.writeheader()
        w.writerows(rows)


def read_results(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=SEP))


def write_manual_template(path, rows):
    """manual.csv : une ligne par question répondue. Ne touche jamais à ce que tu as déjà rempli."""
    path = Path(path)
    existing = {}
    if path.exists():
        with open(path, encoding="utf-8-sig", newline="") as f:
            existing = {r["id"]: r for r in csv.DictReader(f, delimiter=SEP)}
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANUAL_FIELDS, delimiter=SEP)
        w.writeheader()
        for row in rows:
            if row["id"] in existing:
                w.writerow({k: existing[row["id"]].get(k, "") for k in MANUAL_FIELDS})
            elif not row["expects_refusal"] and not row["refused"]:      # on ne note que les vraies réponses
                w.writerow({"id": row["id"], "claims_total": "", "claims_supported": "", "note": ""})


def read_manual(path):
    """{id: (claims_total, claims_supported)} pour les lignes remplies. Vérifie la cohérence."""
    path = Path(path)
    if not path.exists():
        return {}
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=SEP):
            total, sup = (r.get("claims_total") or "").strip(), (r.get("claims_supported") or "").strip()
            if not total and not sup:
                continue
            if not (total.isdigit() and sup.isdigit()):
                raise ValueError(f"manual.csv, {r['id']} : mets des nombres entiers (reçu '{total}' / '{sup}').")
            if int(sup) > int(total):
                raise ValueError(f"manual.csv, {r['id']} : claims_supported ({sup}) > claims_total ({total}).")
            out[r["id"]] = (int(total), int(sup))
    return out


def _clip(text, n=1400):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + " …"


def write_review(path, results, settings_snapshot):
    """review.md : pour chaque question, la réponse et les passages cités, à comparer pour la fidélité.

    results = liste de (question, answer, row). answer peut être None (erreur)."""
    lines = ["# Relecture manuelle", "",
             "Pour chaque réponse : compte les affirmations (claims_total) et combien sont bien dans les "
             "passages cités (claims_supported), puis écris les deux nombres dans manual.csv.", "",
             f"Réglages du run : `{json.dumps(settings_snapshot, ensure_ascii=False)}`", ""]
    for question, answer, row in results:
        lines += [f"---\n\n## {question['id']} · {question['type']}", f"**Question :** {question['question']}", ""]
        gold = [f"{g['article']} | {g['section']} | pp. {g['start']}-{g['end']}" for g in question["gold_items"]]
        lines += ["**Gold :** " + ("aucun (refus attendu)" if not gold else ""), *[f"- {g}" for g in gold]]
        lines += ["", f"**Réponse de référence :** {question.get('reponse_reference', '')}", ""]
        if answer is None:
            lines += [f"**ERREUR :** {row['error']}", ""]
            continue
        lines += [f"**Retrouvé :** top10 {row['found_10']}/{row['gold_n']} · top5 {row['found_5']}/{row['gold_n']}"
                  if row["gold_n"] else f"**Refus :** {'oui' if answer.refused else 'NON'} (attendu : oui)", "",
                  "**Réponse du système :**", "", answer.text, ""]
        for c in answer.citations:
            n = c["n"]
            hit = answer.hits[n - 1] if 0 < n <= len(answer.hits) else None
            if hit is None:
                continue
            lines += [f"> **[{n}] {hit.article_id}** · {hit.section} · p. {hit.page_start}-{hit.page_end}",
                      f"> {_clip(hit.text)}", ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


# ---------- résumé ----------
def _mean(values):
    values = [float(v) for v in values if v not in ("", None)]
    return round(sum(values) / len(values), 3) if values else None


def summarize(rows, manual=None):
    """Chiffres globaux et par type. rows = lignes de résultats (dicts, valeurs éventuellement en texte)."""
    ok = [r for r in rows if not r.get("error")]
    answerable = [r for r in ok if str(r["expects_refusal"]) == "0"]
    off_topic = [r for r in ok if str(r["expects_refusal"]) == "1"]
    by_type = {}
    for t in sorted({r["type"] for r in answerable}):
        sub = [r for r in answerable if r["type"] == t]
        by_type[t] = {"n": len(sub), "recall_10": _mean(r["recall_10"] for r in sub),
                      "recall_5": _mean(r["recall_5"] for r in sub)}
    out = {
        "n_questions": len(rows), "n_errors": len(rows) - len(ok),
        "recall_10": _mean(r["recall_10"] for r in answerable),
        "recall_5": _mean(r["recall_5"] for r in answerable),
        "hit_10": _mean(int(float(r["found_10"]) > 0) for r in answerable),
        "hit_5": _mean(int(float(r["found_5"]) > 0) for r in answerable),
        "off_topic_refused": _mean(r["refused"] for r in off_topic),
        "false_refusals": _mean(r["refused"] for r in answerable),
        "by_type": by_type,
    }
    manual = manual or {}
    scored = {i: v for i, v in manual.items() if any(r["id"] == i for r in ok)}
    total = sum(t for t, _ in scored.values())
    out["faithfulness"] = round(sum(s for _, s in scored.values()) / total, 3) if total else None
    out["faithfulness_questions"] = len(scored)
    return out


def format_summary(s, title=""):
    def pct(x):
        return "n/a" if x is None else f"{x * 100:.0f} %"
    lines = [f"== {title or 'Résumé'} ==",
             f"Questions : {s['n_questions']} (erreurs : {s['n_errors']})",
             f"Recall@10 : {pct(s['recall_10'])}   Recall@5 : {pct(s['recall_5'])}   "
             f"(au moins un bon passage : top10 {pct(s['hit_10'])}, top5 {pct(s['hit_5'])})",
             f"Hors sujet refusés : {pct(s['off_topic_refused'])}   Refus à tort : {pct(s['false_refusals'])}",
             f"Fidélité (manuelle) : {pct(s['faithfulness'])} sur {s['faithfulness_questions']} réponse(s)",
             "Par type :"]
    for t, v in s["by_type"].items():
        lines.append(f"  - {t} (n={v['n']}) : recall@10 {pct(v['recall_10'])}, recall@5 {pct(v['recall_5'])}")
    return "\n".join(lines)


def compare(named_summaries):
    """Tableau texte : une colonne par run. named_summaries = [(nom, summary), ...]."""
    keys = [("recall_10", "Recall@10"), ("recall_5", "Recall@5"), ("hit_10", "Au moins 1 (top10)"),
            ("hit_5", "Au moins 1 (top5)"), ("off_topic_refused", "Hors sujet refusés"),
            ("false_refusals", "Refus à tort"), ("faithfulness", "Fidélité")]
    names = [n for n, _ in named_summaries]
    width = max(len(n) for n in names + ["Mesure"]) + 2
    head = f"{'Mesure':<22}" + "".join(f"{n:>{width}}" for n in names)
    lines = [head, "-" * len(head)]
    for key, label in keys:
        cells = []
        for _, s in named_summaries:
            v = s.get(key)
            cells.append("n/a" if v is None else f"{v * 100:.0f} %")
        lines.append(f"{label:<22}" + "".join(f"{c:>{width}}" for c in cells))
    return "\n".join(lines)
