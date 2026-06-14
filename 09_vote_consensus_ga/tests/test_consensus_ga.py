"""Tests unitaires — consensus_ga.py (GA, entropie, protocole)."""
from __future__ import annotations

import numpy as np

from consensus_ga import (
    candidat_aleatoire,
    croisement,
    entropie_exploration,
    entropie_votes,
    fitness,
    meilleur_candidat_ga,
    mutation,
    rechercher_consensus,
)
from simulateur import est_candidat_valide, generer_personnes, lister_candidats


def test_entropie_votes_unanime():
    assert entropie_votes(8, 8) == 0.0


def test_entropie_votes_divise():
    assert entropie_votes(4, 8) > 0.0


def test_entropie_exploration_dans_bornes(catalogue_v1, candidats_v1):
    rng = np.random.default_rng(0)
    pop = [candidats_v1[int(rng.integers(len(candidats_v1)))] for _ in range(20)]
    h = entropie_exploration(pop, len(catalogue_v1))
    assert 0.0 <= h <= 1.0


def test_candidat_aleatoire_dans_liste(candidats_v1):
    rng = np.random.default_rng(42)
    c = candidat_aleatoire(rng, candidats_v1)
    assert c in candidats_v1


def test_croisement_produit_valide(catalogue_v1, candidats_v1):
    rng = np.random.default_rng(1)
    p1, p2 = candidats_v1[0], candidats_v1[min(5, len(candidats_v1) - 1)]
    enfant = croisement(rng, catalogue_v1, candidats_v1, p1, p2)
    assert est_candidat_valide(catalogue_v1, enfant)


def test_mutation_produit_valide(catalogue_v1, candidats_v1):
    rng = np.random.default_rng(2)
    enfant = mutation(rng, catalogue_v1, candidats_v1, candidats_v1[0], taux=1.0)
    assert est_candidat_valide(catalogue_v1, enfant)


def test_fitness_baisse_avec_veto(catalogue_v1, candidats_v1):
    personnes = generer_personnes(3, catalogue_v1, graine=0)
    c = candidats_v1[0]
    sans = fitness(c, catalogue_v1, personnes, {})
    avec = fitness(c, catalogue_v1, personnes, {c: {0}})
    assert avec < sans


def test_meilleur_candidat_ga_retour(catalogue_v1):
    personnes = generer_personnes(4, catalogue_v1, graine=3)
    res = meilleur_candidat_ga(catalogue_v1, personnes, graine=3, n_generations=5)
    assert res.attrs["nom"]
    assert len(res.satisfactions) == 4


def test_rechercher_consensus_termine(catalogue_v1):
    personnes = generer_personnes(4, catalogue_v1, graine=42)
    res = rechercher_consensus(
        catalogue_v1, personnes, graine=42, max_rounds=10,
    )
    assert res.nb_rounds <= 10
    assert res.attrs["semaine"] > 0


def test_rechercher_consensus_historique(catalogue_v1):
    personnes = generer_personnes(4, catalogue_v1, graine=7)
    res = rechercher_consensus(
        catalogue_v1, personnes, graine=7, max_rounds=8,
    )
    assert len(res.historique) == res.nb_rounds
    for h in res.historique:
        assert "entropie_votes" in h
        assert "activite" in h


def test_mode_score_remplit_scores(catalogue_v1):
    personnes = generer_personnes(3, catalogue_v1, graine=5)
    res = rechercher_consensus(
        catalogue_v1, personnes, graine=5, max_rounds=3,
        mode_vote="score",
    )
    if res.historique:
        assert "scores" in res.historique[0]
