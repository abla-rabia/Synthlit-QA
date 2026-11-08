"""Construit l'index : PDF -> chunks -> embeddings -> Chroma.

Usage (depuis la racine du projet) :
    python scripts/build_index.py                          # tous les articles
    python scripts/build_index.py --only 2022_zimmermann   # essai : n'écrit pas l'index
    python scripts/build_index.py --force                  # refait aussi l'extraction hi_res
    python scripts/build_index.py --no-summaries           # sans résumés de tableaux (pas de LLM)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # pour trouver le paquet `rag`

from dotenv import load_dotenv

from rag.config import load_settings
from rag.ingestion.pipeline import run_ingestion


def main():
    parser = argparse.ArgumentParser(description="Construit l'index de l'assistant.")
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--only", nargs="+", help="article_id à traiter (mode essai)")
    parser.add_argument("--force", action="store_true", help="refait l'extraction hi_res")
    parser.add_argument("--no-summaries", action="store_true", help="éteint les résumés de tableaux")
    parser.add_argument("--allow-partial", action="store_true",
                        help="construit l'index même si un article échoue")
    args = parser.parse_args()

    load_dotenv()                                  # lit GROQ_API_KEY dans .env
    settings = load_settings(args.settings)
    if args.no_summaries:
        settings["ingestion"]["use_table_summaries"] = False

    result = run_ingestion(settings, only=args.only, force=args.force,
                           allow_partial=args.allow_partial)
    sys.exit(1 if result["failures"] else 0)


if __name__ == "__main__":
    main()