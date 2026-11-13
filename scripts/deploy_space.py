"""Prépare un dossier propre et l'envoie sur Hugging Face Spaces (Docker).

    python scripts/deploy_space.py --name synthlit --dry-run   # prépare build/space, n'envoie rien
    python scripts/deploy_space.py --name synthlit             # prépare + envoie

Il copie seulement ce dont l'app a besoin (code, config, index, chunks, table des sources), jamais :
les PDF, .env, tests, évaluation, cache d'extraction. Les versions des bibliothèques sont celles
installées chez toi (l'index Chroma doit être relu avec la même version que celle qui l'a écrit).
Le token Hugging Face (droit "write") est lu dans la variable HF_TOKEN. La clé Groq n'est PAS envoyée :
tu l'ajoutes toi-même comme "secret" du Space."""
import argparse
import importlib.metadata as md
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "build" / "space"
CODE = ["app.py", "pages", "ui", "rag", ".streamlit"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")

# nom pip -> utilisé pour fixer les versions (torch est installé à part, en version CPU)
PACKAGES = ["streamlit", "python-dotenv", "pyyaml", "pydantic", "langchain-core", "langchain-chroma",
            "langchain-huggingface", "langchain-groq", "chromadb", "sentence-transformers",
            "transformers", "rank-bm25"]

SPACE_README = """---
title: {title}
emoji: 🌿
colorFrom: green
colorTo: green
sdk: docker
app_port: 8501
pinned: false
short_description: Cited Q&A over open-access papers on medical image synthesis
---

# {title}

Ask questions about {n} open-access (CC BY) papers on deep learning for medical image synthesis and get
answers with numbered citations (paper, section, pages). No question is stored.
Papers, authors and licences are listed on the app's Credits page.
"""

DOCKERFILE = """FROM python:{py}-slim
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \\
 && pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""


def copy(src_rel, stage):
    src = ROOT / src_rel
    if not src.exists():
        sys.exit(f"Introuvable : {src_rel} (lance le script depuis la racine du projet)")
    dst = stage / src_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=IGNORE)
    else:
        shutil.copy2(src, dst)


def pinned_requirements():
    lines, missing = [], []
    for name in PACKAGES:
        try:
            lines.append(f"{name}=={md.version(name)}")
        except md.PackageNotFoundError:
            missing.append(name)
            lines.append(name)                       # pas installé ici : version libre
    return lines, missing


def build_stage(title):
    settings = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    paths = settings["paths"]
    needed = CODE + ["config/settings.yaml", paths["multiquery_prompt"], paths["condense_prompt"],
                     paths["answer_prompt"], paths["sources"], paths["chunks"], paths["index"]]
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for item in needed:
        copy(item, STAGE)
    reqs, missing = pinned_requirements()
    (STAGE / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    (STAGE / "Dockerfile").write_text(DOCKERFILE.format(py=f"{sys.version_info.major}.{sys.version_info.minor}"),
                                      encoding="utf-8")
    n_papers = sum(1 for _ in open(ROOT / paths["sources"], encoding="utf-8-sig")) - 1
    (STAGE / "README.md").write_text(SPACE_README.format(title=title, n=n_papers), encoding="utf-8")
    return missing


def report():
    total = 0
    for f in sorted(STAGE.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            total += size
            if size > 1_000_000:
                print(f"  {f.relative_to(STAGE)}  {size / 1e6:.1f} Mo")
    print(f"Dossier prêt : {STAGE}  ({total / 1e6:.1f} Mo au total)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", default="synthlit", help="nom du Space (dans l'URL)")
    parser.add_argument("--title", default="SynthLit", help="titre affiché sur Hugging Face")
    parser.add_argument("--dry-run", action="store_true", help="prépare le dossier sans rien envoyer")
    args = parser.parse_args()

    missing = build_stage(args.title)
    report()
    if missing:
        print("Attention, pas installés chez toi (versions non fixées) :", ", ".join(missing))
    if args.dry_run:
        return

    from huggingface_hub import HfApi
    api = HfApi()                                    # token : variable HF_TOKEN
    user = api.whoami()["name"]
    repo_id = f"{user}/{args.name}"
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
    api.upload_folder(folder_path=str(STAGE), repo_id=repo_id, repo_type="space",
                      commit_message="Deploy app")
    print(f"\nEnvoyé. Page du Space : https://huggingface.co/spaces/{repo_id}")
    print("N'oublie pas d'ajouter le secret GROQ_API_KEY dans Settings > Variables and secrets.")


if __name__ == "__main__":
    main()