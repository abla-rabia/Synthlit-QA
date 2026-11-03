"""Chargement de config/settings.yaml (chiffres, chemins, interrupteurs)."""
from pathlib import Path

import yaml


def load_settings(path="config/settings.yaml"):
    """Lit le fichier de configuration et retourne un dictionnaire.

    Les chemins sont relatifs à la racine du projet : lance les scripts depuis cette racine.
    """
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))