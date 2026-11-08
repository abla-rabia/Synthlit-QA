"""Chat dans le terminal (sans interface).

Usage (depuis la racine du projet) :
    python scripts/chat.py                 # conversation
    python scripts/chat.py --debug         # montre la question réécrite, les 3 requêtes, les 10 candidats, les 5 retenus
    python scripts/chat.py --no-rerank     # éteint une brique (aussi --no-multiquery, --no-hybrid)
Commandes : /reset (nouvelle conversation), /quit
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from rag.config import load_settings
from rag.pipeline import Conversation, load_pipeline


def show(answer, debug):
    r = answer.retrieval
    if debug:
        print(f"\n[question autonome] {r.standalone}")
        for i, q in enumerate(r.queries, 1):
            print(f"[requête {i}] {q}")
        print(f"[candidats RRF ({len(r.candidates)})] " + ", ".join(h.chunk_id for h in r.candidates))
        print(f"[après rerank ({len(r.final)})] " + ", ".join(h.chunk_id for h in r.final))
        if answer.retries or answer.removed:
            print(f"[citations] nouvel essai : {answer.retries}, numéros invalides retirés : {answer.removed}")
    print("\n" + answer.text)
    if answer.used_catalogue:
        print("\n[catalogue] = liste des articles de la collection")
    for c in answer.citations:
        print(f"[{c['n']}] {c['citation']} · {c['section']} ({c['pages']}) — {c['title']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Chat avec les articles (terminal).")
    parser.add_argument("--settings", default="config/settings.yaml")
    parser.add_argument("--debug", action="store_true")
    for brick in ("multiquery", "hybrid", "rerank"):
        parser.add_argument(f"--no-{brick}", action="store_true")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")        # accents / symboles sous Windows
    load_dotenv()
    settings = load_settings(args.settings)
    for brick in ("multiquery", "hybrid", "rerank"):
        if getattr(args, f"no_{brick}"):
            settings["retrieval"][f"use_{brick}"] = False

    print("Chargement (la 1re fois, les modèles se téléchargent)…")
    chat = Conversation(load_pipeline(settings), settings["retrieval"]["history_turns"])
    print("Prêt. /reset = nouvelle conversation, /quit = quitter.\n")
    while True:
        try:
            question = input("Question > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question in ("/quit", "/exit"):
            break
        if question == "/reset":
            chat.reset()
            print("Conversation réinitialisée.\n")
            continue
        if question:
            show(chat.ask(question), args.debug)


if __name__ == "__main__":
    main()
