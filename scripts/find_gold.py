"""Trouve les chunks candidats pour une question, pour aider à remplir le gold.

Usage :
    python scripts/find_gold.py "Quels GAN sont utilisés pour MRI-to-CT ?"
    python scripts/find_gold.py "Quels GAN..." --keywords "GAN,CycleGAN,MRI,CT"
    python scripts/find_gold.py "Quels GAN..." --top 8
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path


def _norm(text):
    """Minuscules, sans accents, pour une recherche robuste."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--keywords", default="",
                        help="mots-clés séparés par des virgules (sinon extraits de la question)")
    parser.add_argument("--chunks", default="data/chunks.jsonl")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = [w for w in re.findall(r"\w{4,}", _norm(args.question))]

    chunks = []
    with open(args.chunks, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    scored = []
    for c in chunks:
        haystack = _norm(c.get("text", "") + " " + c.get("header", ""))
        hits = sum(1 for kw in keywords if kw in haystack)
        if hits > 0:
            scored.append((hits, c))

    scored.sort(key=lambda x: -x[0])

    print(f"\nQuestion : {args.question}")
    print(f"Mots-clés : {keywords}")
    print(f"Chunks candidats (top {args.top}) :\n")
    for hits, c in scored[:args.top]:
        print(f"  [{hits} hits] {c['chunk_id']}")
        print(f"    Article    : {c['article_id']}")
        print(f"    Section    : {c.get('section')} > {c.get('sous_section')}")
        print(f"    Pages      : {c.get('page_start')}-{c.get('page_end')}")
        print(f"    Extrait    : {c.get('text', '')[:200].replace(chr(10), ' ')}...")
        print()


if __name__ == "__main__":
    main()