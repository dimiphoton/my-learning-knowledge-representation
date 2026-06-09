"""Strategies interchangeables pour la recherche de consensus.

Trois familles de "briques" qu'on peut combiner :

  1. FONCTIONS DE BIEN-ETRE : comment agreger les satisfactions d'un
     groupe en un seul score (utilitariste, egalitariste, Nash...).
  2. CRITERES DE CONSENSUS : a quelle condition declare-t-on l'accord
     (unanimite, supermajorite, plancher, entropie faible...).
  3. MOTEUR EXHAUSTIF : evalue TOUS les candidats (l'espace est petit
     ici), pour servir de "verite-terrain" face au genetique.

Tout est ecrit comme de simples fonctions, faciles a brancher.
"""

from __future__ import annotations

import numpy as np

from simulateur import attributs_candidat, lister_candidats, satisfaction


# =============================================================================
# 1) Fonctions de bien-etre : satisfactions (np.ndarray) -> float [0, 1]
# =============================================================================
def bien_etre_moyenne(sats: np.ndarray) -> float:
    """Utilitariste : maximise le bonheur TOTAL (peut leser une personne)."""
    return float(np.mean(sats))


def bien_etre_min(sats: np.ndarray) -> float:
    """Egalitariste (maximin / Rawls) : ne regarde que le plus malheureux."""
    return float(np.min(sats))


def bien_etre_mixte(sats: np.ndarray) -> float:
    """Compromis moyenne/min (valeur par defaut du projet)."""
    return 0.5 * float(np.mean(sats)) + 0.5 * float(np.min(sats))


def bien_etre_nash(sats: np.ndarray) -> float:
    """Bien-etre de Nash : moyenne geometrique.

    Le produit des satisfactions chute des qu'une personne est proche
    de 0 : bon equilibre entre efficacite et equite.
    """
    sats = np.clip(sats, 1e-9, None)  # evite log(0)
    return float(np.exp(np.mean(np.log(sats))))


def bien_etre_leximin(sats: np.ndarray) -> float:
    """Leximin (approche) : le plus malheureux pese le plus lourd.

    On trie les satisfactions par ordre croissant et on les pondere de
    facon decroissante (1, 1/2, 1/4...). C'est l'esprit du leximin :
    on departage surtout sur les personnes les moins satisfaites.
    """
    triees = np.sort(sats)  # croissant : la pire en premier
    poids = 0.5 ** np.arange(len(triees))
    return float(np.sum(poids * triees) / np.sum(poids))


# Catalogue pour choisir une strategie par son nom (pratique en notebook).
BIENS_ETRE = {
    "moyenne": bien_etre_moyenne,
    "min": bien_etre_min,
    "mixte": bien_etre_mixte,
    "nash": bien_etre_nash,
    "leximin": bien_etre_leximin,
}


# =============================================================================
# 2) Criteres de consensus : (approbations, sats, entropie) -> bool
#    On les construit via des "fabriques" pour regler leurs seuils.
# =============================================================================
def critere_unanimite():
    """Accord seulement si TOUT le monde approuve (defaut)."""
    def critere(approbations, sats, h_votes):
        return all(approbations)
    return critere


def critere_supermajorite(seuil: float = 0.75):
    """Accord si au moins 'seuil' (ex. 75 %) des personnes approuvent."""
    def critere(approbations, sats, h_votes):
        return (sum(approbations) / len(approbations)) >= seuil
    return critere


def critere_majorite():
    """Accord a la majorite simple (> 50 %)."""
    return critere_supermajorite(seuil=0.5 + 1e-9)


def critere_plancher(plancher: float = 0.4):
    """Accord si PERSONNE n'est sous un plancher (equite minimale)."""
    def critere(approbations, sats, h_votes):
        return float(np.min(sats)) >= plancher
    return critere


def critere_entropie(seuil: float = 0.2):
    """Accord quand le desaccord (entropie des votes) passe sous seuil."""
    def critere(approbations, sats, h_votes):
        return h_votes <= seuil
    return critere


def critere_score_moyen(seuil: float = 0.6):
    """Vote par score : accord si le score MOYEN depasse seuil (6/10)."""
    def critere(approbations, sats, h_votes):
        return float(np.mean(sats)) >= seuil
    return critere


# =============================================================================
# 3) Moteur exhaustif : la "verite-terrain"
# =============================================================================
def evaluer_candidat(catalogue, personnes, candidat) -> np.ndarray:
    """Renvoie le vecteur des satisfactions pour un candidat."""
    attrs = attributs_candidat(catalogue, candidat)
    return np.array([satisfaction(p, attrs) for p in personnes])


def meilleur_exhaustif(catalogue, personnes, bien_etre=bien_etre_mixte):
    """Parcourt TOUS les candidats et renvoie l'optimum.

    Renvoie un dict : candidat, attrs, valeur (bien-etre), satisfactions.
    Sert de reference pour juger l'algorithme genetique.
    """
    candidats = lister_candidats(catalogue)

    def note(c):
        return bien_etre(evaluer_candidat(catalogue, personnes, c))

    meilleur = max(candidats, key=note)
    attrs = attributs_candidat(catalogue, meilleur)
    sats = evaluer_candidat(catalogue, personnes, meilleur)
    return {
        "candidat": meilleur,
        "attrs": attrs,
        "valeur": round(float(bien_etre(sats)), 4),
        "satisfactions": {
            p.nom: round(float(s), 3) for p, s in zip(personnes, sats)
        },
    }
