"""Compare plusieurs runs d'évaluation dans un tableau prêt pour le README.

    python scripts/compare.py data/eval/runs/baseline_run data/eval/runs/sans_rerank

Par défaut, seules les questions SANS erreur dans TOUS les runs sont comparées (sinon un run qui
a planté sur une question serait avantagé ou désavantagé). --all-questions pour tout garder.
Rang moyen : position moyenne du premier bon passage (1 = meilleur) ; plus fin que le recall
quand celui-ci est à 100 %.
"""
import argparse
import json
import sys
from pathlib import Path


def load(folder):
    return {r["id"]: r for r in json.loads((Path(folder) / "rows.json").read_text(encoding="utf-8"))}


def mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def fmt(value, digits=2):
    return "-" if value is None else f"{value:.{digits}f}"


def summarize(rows):
    scored = [r for r in rows if r["recall10"] is not None]
    off = [r for r in rows if r["offtopic"]]
    return {
        "n": len(rows), "n_gold": len(scored),
        "recall10": mean(r["recall10"] for r in scored), "recall5": mean(r["recall5"] for r in scored),
        "rang10": mean(r["rank10"] for r in scored), "rang5": mean(r["rank5"] for r in scored),
        "refus_a_tort": sum(r["refused"] for r in scored),
        "hors_sujet": f"{sum(r['refused'] for r in off)}/{len(off)}",
        "citations": mean(r["trace_ok"] for r in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--all-questions", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    runs = {Path(p).name: load(p) for p in args.runs}
    ids = set.intersection(*(set(r) for r in runs.values()))
    if not args.all_questions:
        bad = {i for r in runs.values() for i, row in r.items() if row["error"]}
        for name, r in runs.items():
            errors = sorted(i for i, row in r.items() if row["error"])
            if errors:
                print(f"! {name} : erreur sur {errors} -> ces questions sont exclues de TOUS les runs")
        ids -= bad
    print(f"\n{len(ids)} questions comparées\n")
    print("| Run | Recall@10 | Recall@5 | Rang moyen (top10 / top5) | Refus à tort | Hors sujet refusés | Citations valides |")
    print("|---|---|---|---|---|---|---|")
    for name, rows in runs.items():
        s = summarize([rows[i] for i in sorted(ids) if not rows[i]["error"]])
        print(f"| {name} | {fmt(s['recall10'])} | {fmt(s['recall5'])} | {fmt(s['rang10'])} / {fmt(s['rang5'])} "
              f"| {s['refus_a_tort']} | {s['hors_sujet']} | {fmt(s['citations'], 2)} |")
    refused = {name: sorted(i for i in ids if rows[i]["refused"] and not rows[i]["offtopic"])
               for name, rows in runs.items()}
    print("\nQuestions avec réponse attendue mais refusées :", refused)


if __name__ == "__main__":
    main()