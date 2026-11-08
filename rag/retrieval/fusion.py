"""Fusion de classements : RRF (Reciprocal Rank Fusion), avec des poids.

score(id) = somme sur chaque liste de  poids / (k + position)     (position : 1, 2, 3…)
Les poids s'appliquent aux RANGS, pas aux scores bruts (c'est ce que fait EnsembleRetriever).
"""


def weighted_rrf(rank_lists, weights=None, k=60):
    """rank_lists : liste de listes d'ids (meilleur en premier). Retourne [(id, score)] trié."""
    weights = weights or [1.0] * len(rank_lists)
    if len(weights) != len(rank_lists):
        raise ValueError("un poids par liste")
    scores = {}
    for ids, weight in zip(rank_lists, weights):
        seen = set()
        for position, item in enumerate(ids, start=1):
            if item in seen:               # un doublon dans la même liste ne compte qu'une fois
                continue
            seen.add(item)
            scores[item] = scores.get(item, 0.0) + weight / (k + position)
    return sorted(scores.items(), key=lambda pair: -pair[1])   # tri stable : égalité = 1er vu
