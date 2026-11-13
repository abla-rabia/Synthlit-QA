"""Écrit requirements.txt avec les versions EXACTES installées chez toi.

    python scripts/make_requirements.py

Pourquoi : l'index Chroma doit être relu avec la même version que celle qui l'a écrit.
Seuls les paquets utiles à l'APP sont listés (pas unstructured : l'extraction des PDF n'est pas refaite en ligne)."""
import importlib.metadata as md
import sys
from pathlib import Path

PACKAGES = ["streamlit", "python-dotenv", "pyyaml", "pydantic", "langchain-core", "langchain-chroma",
            "langchain-huggingface", "langchain-groq", "chromadb", "sentence-transformers",
            "transformers", "torch", "rank-bm25"]

lines, missing = [], []
for name in PACKAGES:
    try:
        version = md.version(name).split("+")[0]        # "2.5.1+cpu" -> "2.5.1"
        lines.append(f"{name}=={version}")
    except md.PackageNotFoundError:
        missing.append(name)
Path("requirements.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("requirements.txt écrit :")
print("\n".join(lines))
print(f"\nPython utilisé ici : {sys.version_info.major}.{sys.version_info.minor} "
      "(choisis la même version sur Streamlit Community Cloud)")
if missing:
    print("Non installés ici (non listés) :", ", ".join(missing))