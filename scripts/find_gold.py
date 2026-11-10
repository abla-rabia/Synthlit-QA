"""Trouve où se trouve une réponse : cherche des mots dans data/chunks.jsonl et affiche
les lignes `gold` prêtes à copier dans questions.yaml.

    python scripts/find_gold.py "lowest MAE"
    python scripts/find_gold.py PET MRI attenuation        # plusieurs mots : tous doivent être présents
    python scripts/find_gold.py "SSIM" --article zimmermann --max 10
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.ingestion.index import load_chunks_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("words", nargs="+")
    parser.add_argument("--chunks", default="data/chunks.jsonl")
    parser.add_argument("--article", help="morceau du nom d'article (ex. zimmermann)")
    parser.add_argument("--max", type=int, default=8)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    words = [w.lower() for w in args.words]
    shown = 0
    for r in load_chunks_jsonl(args.chunks):
        if args.article and args.article.lower() not in r["article_id"].lower():
            continue
        text = r["text"] + " " + " ".join(t.get("text", "") for t in r.get("tables", []))
        if not all(w in text.lower() for w in words):
            continue
        where = r.get("sous_section") or r.get("section") or ""
        p1, p2 = r.get("page_start"), r.get("page_end")
        pages = f"{p1}-{p2}" if p2 and p2 != p1 else f"{p1}"
        pos = text.lower().find(words[0])
        extrait = re.sub(r"\s+", " ", text[max(0, pos - 120): pos + 200])
        print(f"gold: {r['article_id']} | {where} | pages {pages}")
        print(f"      …{extrait}…\n")
        shown += 1
        if shown >= args.max:
            break
    if not shown:
        print("Rien trouvé : essaie un autre mot (ou moins de mots).")


if __name__ == "__main__":
    main()