"""Évaluation : pose les questions de data/eval/questions.yaml au système et écrit les tableaux.

Un run = une configuration. On change UNE chose à la fois, on relance, on compare :
    python scripts/eval.py                          # tout activé  -> data/eval/runs/full
    python scripts/eval.py --no-rerank              # sans reranker -> data/eval/runs/no-rerank
    python scripts/eval.py --no-multiquery          # (aussi --no-hybrid)
    python scripts/eval.py --score data/eval/runs/full      # recalcule le résumé après avoir rempli manual.csv
    python scripts/eval.py --compare data/eval/runs/full data/eval/runs/no-rerank

Fichiers écrits dans le dossier du run :
    results.csv  (un ligne par question, chiffres automatiques)
    review.md    (réponses + passages cités, à lire pour la fidélité)
    manual.csv   (à remplir : claims_total, claims_supported)
    summary.json (les chiffres globaux)
    answers.jsonl (sortie brute : texte, citations, chunks candidats et retenus)
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.evaluation import (compare, error_row, evaluate_question, format_summary, load_questions,
                            read_manual, read_results, summarize, write_manual_template,
                            write_results, write_review)

BRICKS = ("multiquery", "hybrid", "rerank")


def run_name(args):
    off = [b for b in BRICKS if getattr(args, f"no_{b}")]
    return args.name or ("no-" + "-no-".join(off) if off else "full")


def score(run_dir):
    run_dir = Path(run_dir)
    rows = read_results(run_dir / "results.csv")
    summary = summarize(rows, read_manual(run_dir / "manual.csv"))
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(format_summary(summary, run_dir.name))
    return summary


def do_compare(dirs):
    items = []
    for d in dirs:
        s = score(d)          # recalcule avec le manual.csv à jour
        items.append((Path(d).name, s))
        print()
    print(compare(items))


def run(args):
    from dotenv import load_dotenv
    from rag.config import load_settings
    from rag.pipeline import load_pipeline

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    settings = load_settings(args.settings)
    for brick in BRICKS:
        if getattr(args, f"no_{brick}"):
            settings["retrieval"][f"use_{brick}"] = False
    snapshot = {b: settings["retrieval"].get(f"use_{b}", True) for b in BRICKS}

    print("Chargement du système…")
    pipeline = load_pipeline(settings)
    try:
        known = set(pipeline.sources)
    except TypeError:
        known = None
    questions = load_questions(args.questions, known_articles=known)
    if args.limit:
        questions = questions[:args.limit]

    name = run_name(args)
    run_dir = Path(args.out) / name
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run « {name} » : {len(questions)} questions, réglages {snapshot}\n")

    results, rows, raw = [], [], []
    for i, q in enumerate(questions, 1):
        try:
            answer = pipeline.ask(q["question"])          # chaque question est indépendante (pas d'historique)
            row = evaluate_question(q, answer)
            raw.append({"id": q["id"], "answer": answer.text, "refused": answer.refused,
                        "citations": answer.citations,
                        "candidates": [h.chunk_id for h in answer.retrieval.candidates],
                        "final": [h.chunk_id for h in answer.retrieval.final]})
        except Exception as exc:                          # une erreur ne doit pas arrêter les 21 autres
            answer, row = None, error_row(q, exc)
            print(f"  ! {q['id']} : {row['error']}")
        rows.append(row)
        results.append((q, answer, row))
        print(f"[{i}/{len(questions)}] {q['id']} {q['type']:<14} top10 {row['found_10']}/{row['gold_n']}  "
              f"top5 {row['found_5']}/{row['gold_n']}  refus {row['refused']}")

    write_results(run_dir / "results.csv", rows)
    write_review(run_dir / "review.md", results, snapshot)
    write_manual_template(run_dir / "manual.csv", rows)
    with open(run_dir / "answers.jsonl", "w", encoding="utf-8") as f:
        for item in raw:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print()
    score(run_dir)
    print(f"\nFichiers dans {run_dir}. Prochaine étape : lis review.md, remplis manual.csv, puis\n"
          f"  python scripts/eval.py --score {run_dir}")


def main():
    p = argparse.ArgumentParser(description="Évaluation du RAG.")
    p.add_argument("--settings", default="config/settings.yaml")
    p.add_argument("--questions", default="data/eval/questions.yaml")
    p.add_argument("--out", default="data/eval/runs")
    p.add_argument("--name", help="nom du dossier du run (par défaut : full, no-rerank, …)")
    p.add_argument("--limit", type=int, help="ne poser que les N premières questions (test rapide)")
    p.add_argument("--score", metavar="DOSSIER", help="recalcule le résumé d'un run (après manual.csv)")
    p.add_argument("--compare", nargs="+", metavar="DOSSIER", help="compare plusieurs runs")
    for b in BRICKS:
        p.add_argument(f"--no-{b}", action="store_true")
    args = p.parse_args()
    if args.compare:
        do_compare(args.compare)
    elif args.score:
        score(args.score)
    else:
        run(args)


if __name__ == "__main__":
    main()
