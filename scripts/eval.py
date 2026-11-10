"""Évaluation du système sur data/eval/questions.yaml.

Lancer un run (depuis la racine du projet) :
    python scripts/eval.py --name baseline
    python scripts/eval.py --name sans_rerank --no-rerank       # UN seul changement par run
    python scripts/eval.py --name essai --only q01 q02          # quelques questions
Puis ouvre data/eval/runs/<name>/review.md, remplis manual.csv, et calcule :
    python scripts/eval.py --score data/eval/runs/baseline
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from rag.config import load_settings
from rag.evaluation import (evaluate_question, format_summary, load_questions, read_manual, summarize,
                            write_manual_template, write_results, write_review)
from rag.sources import load_sources


def main():
    parser = argparse.ArgumentParser(description="Évalue le retrieval et la génération.")
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--questions", default="data/eval/questions.yaml")
    parser.add_argument("--runs", default="data/eval/runs")
    parser.add_argument("--name", help="nom du run (dossier dans data/eval/runs)")
    parser.add_argument("--only", nargs="+", help="ids de questions à poser")
    parser.add_argument("--delay", type=float, default=2.0, help="secondes entre deux questions (limites Groq)")
    parser.add_argument("--score", help="dossier d'un run : recalcule le résumé avec manual.csv")
    for brick in ("multiquery", "hybrid", "rerank"):
        parser.add_argument(f"--no-{brick}", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.score:
        folder = Path(args.score)
        rows = json.loads((folder / "rows.json").read_text(encoding="utf-8"))
        summary = summarize(rows, read_manual(folder / "manual.csv"))
        (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        print(format_summary(summary))
        return

    if not args.name:
        parser.error("--name est obligatoire (ex. --name baseline)")
    load_dotenv()
    settings = load_settings(args.settings)
    for brick in ("multiquery", "hybrid", "rerank"):
        if getattr(args, f"no_{brick}"):
            settings["retrieval"][f"use_{brick}"] = False

    sources = load_sources(settings["paths"]["sources"])
    questions = load_questions(args.questions, sources)          # valide avant de dépenser des appels
    if args.only:
        unknown = set(args.only) - {q["id"] for q in questions}
        if unknown:
            parser.error(f"ids inconnus : {sorted(unknown)}")
        questions = [q for q in questions if q["id"] in args.only]

    from rag.pipeline import load_pipeline
    print("Chargement…")
    pipeline = load_pipeline(settings)

    results = []
    for i, question in enumerate(questions, start=1):
        try:
            answer, error = pipeline.ask(question["question"]), ""
        except Exception as e:                                    # limite de débit, réseau…
            answer, error = None, f"{type(e).__name__}: {e}"
        row = evaluate_question(question, answer, error)
        results.append((question, answer, row))
        status = error or f"recall@10={row['recall10']} recall@5={row['recall5']} refus={row['refused']}"
        print(f"[{i}/{len(questions)}] {question['id']} {status}")
        time.sleep(args.delay)

    folder = Path(args.runs) / args.name
    rows = [r for _, _, r in results]
    snapshot = {**settings["retrieval"], "llm": settings["llm"]["model"]}
    write_results(folder, rows)
    write_review(folder / "review.md", results, snapshot)
    write_manual_template(folder, rows)
    summary = summarize(rows)
    (folder / "summary.json").write_text(json.dumps({"reglages": snapshot, **summary}, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    print("\n" + format_summary(summary))
    print(f"\nFichiers : {folder}  (review.md à lire, manual.csv à remplir, puis --score)")


if __name__ == "__main__":
    main()