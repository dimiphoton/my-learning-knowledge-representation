"""Moteur de negociation manuelle (sans UI).

L'utilisateur incarne chaque personne et vote round par round. Le systeme
propose des candidats via un GA-lite pilote par les votes deja exprimes :
  - satisfaction connue = vote converti en [0, 1] ;
  - candidat jamais note = 0.5 (optimiste, incite a explorer) ;
  - candidat vetote = penalise dans la fitness.

Reutilise entropie_votes/exploration et les operateurs genetiques de
consensus_ga.py ; l'historique produit est compatible avec visualisation.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from consensus_ga import (
    PENALITE_VETO,
    Candidat,
    candidat_aleatoire,
    croisement,
    entropie_exploration,
    entropie_votes,
    mutation,
)
from simulateur import attributs_candidat, lister_candidats
from strategies import bien_etre_mixte, critere_unanimite

# Taille de population et generations par round (GA-lite).
TAILLE_POP = 30
GENERATIONS = 4
MAX_ROUNDS = 20


def _fitness_humain(
    candidat: Candidat,
    noms: list[str],
    memoire: dict[tuple[str, Candidat], float],
    vetos: dict[Candidat, set[int]],
) -> float:
    """Note un candidat a partir des votes humains deja enregistres."""
    sats = np.array([
        memoire.get((nom, candidat), 0.5) for nom in noms
    ])
    base = bien_etre_mixte(sats)
    nb_vetos = len(vetos.get(candidat, set()))
    return base - PENALITE_VETO * nb_vetos


def _selection_tournoi(rng, population, notes, taille=3) -> Candidat:
    """Choisit le meilleur parmi 'taille' candidats tires au hasard."""
    indices = rng.integers(0, len(population), size=taille)
    meilleur = max(indices, key=lambda i: notes[i])
    return population[meilleur]


def _evoluer_humain(
    rng,
    population: list[Candidat],
    catalogue: dict,
    candidats: list[Candidat],
    noms: list[str],
    memoire: dict,
    vetos: dict,
    n_generations: int = GENERATIONS,
) -> list[Candidat]:
    """Fait evoluer la population avec la fitness humaine."""
    for _ in range(n_generations):
        notes = [
            _fitness_humain(c, noms, memoire, vetos) for c in population
        ]
        ordre = sorted(range(len(population)), key=lambda i: notes[i],
                       reverse=True)

        nouvelle_pop = [population[i] for i in ordre[:2]]  # elitisme
        while len(nouvelle_pop) < len(population):
            p1 = _selection_tournoi(rng, population, notes)
            p2 = _selection_tournoi(rng, population, notes)
            enfant = croisement(rng, catalogue, p1, p2)
            enfant = mutation(rng, catalogue, candidats, enfant)
            nouvelle_pop.append(enfant)
        population = nouvelle_pop

    notes = [_fitness_humain(c, noms, memoire, vetos) for c in population]
    return [population[i] for i in sorted(range(len(population)),
                                          key=lambda i: notes[i],
                                          reverse=True)]


@dataclass
class EtatNegociation:
    """Etat complet d'une negociation manuelle en cours."""

    catalogue: dict
    candidats: list[Candidat]
    noms: list[str]
    mode_vote: str                          # "binaire" ou "score"
    critere: Callable                       # fabrique de strategies.py
    veto_actif: bool
    rng: np.random.Generator
    population: list[Candidat]
    vetos: dict[Candidat, set[int]]
    credits_veto: dict[int, int]
    relachement: float
    leader: Candidat
    votes_round: dict[str, bool | int | str]  # votes du round en cours
    idx_personne: int
    historique: list[dict] = field(default_factory=list)
    memoire: dict[tuple[str, Candidat], float] = field(default_factory=dict)
    num_round: int = 0
    consensus_atteint: bool = False
    max_rounds: int = MAX_ROUNDS


def demarrer(
    catalogue: dict,
    noms: list[str],
    mode_vote: str = "binaire",
    critere=None,
    veto_actif: bool = False,
    credits_veto: int = 2,
    graine: int = 0,
) -> EtatNegociation:
    """Initialise une negociation et propose le premier candidat."""
    if critere is None:
        critere = critere_unanimite()

    rng = np.random.default_rng(graine)
    candidats = lister_candidats(catalogue)
    population = [candidat_aleatoire(rng, candidats)
                  for _ in range(TAILLE_POP)]
    population = _evoluer_humain(rng, population, catalogue, candidats,
                                 noms, {}, {})

    return EtatNegociation(
        catalogue=catalogue,
        candidats=candidats,
        noms=noms,
        mode_vote=mode_vote,
        critere=critere,
        veto_actif=veto_actif,
        rng=rng,
        population=population,
        vetos={},
        credits_veto={i: credits_veto for i in range(len(noms))},
        relachement=0.0,
        leader=population[0],
        votes_round={},
        idx_personne=0,
    )


def enregistrer_vote(etat: EtatNegociation, nom: str,
                     valeur: bool | int | str) -> None:
    """Enregistre le vote d'une personne pour le round en cours."""
    etat.votes_round[nom] = valeur


def tous_ont_vote(etat: EtatNegociation) -> bool:
    """True si chaque personne a deja vote pour le candidat courant."""
    return len(etat.votes_round) == len(etat.noms)


def _vote_en_satisfaction(vote: bool | int | str) -> float:
    """Convertit un vote en score de satisfaction [0, 1]."""
    if vote == "veto":
        return 0.0
    if isinstance(vote, bool):
        return 1.0 if vote else 0.0
    return float(vote) / 10.0


def _est_approuve(vote: bool | int | str, mode: str) -> bool:
    """Determine si un vote compte comme approbation."""
    if vote == "veto":
        return False
    if mode == "binaire":
        return bool(vote)
    return int(vote) >= 6  # score >= 6/10


def valider_round(etat: EtatNegociation) -> bool:
    """Traite le round courant. Renvoie True si consensus atteint."""
    if not tous_ont_vote(etat):
        return False

    etat.num_round += 1
    leader = etat.leader
    attrs = attributs_candidat(etat.catalogue, leader)

    # Enregistre les votes dans la memoire (pour le GA futur).
    approbations: list[bool] = []
    sats_liste = np.zeros(len(etat.noms))
    vetos_du_round: list[str] = []

    for i, nom in enumerate(etat.noms):
        vote = etat.votes_round[nom]
        sat = _vote_en_satisfaction(vote)
        sats_liste[i] = sat
        etat.memoire[(nom, leader)] = sat
        approbations.append(_est_approuve(vote, etat.mode_vote))

        # Veto payant (optionnel).
        if etat.veto_actif and vote == "veto" and etat.credits_veto[i] > 0:
            etat.credits_veto[i] -= 1
            etat.vetos.setdefault(leader, set()).add(i)
            vetos_du_round.append(nom)

    nb_approuve = sum(approbations)
    h_votes = entropie_votes(nb_approuve, len(etat.noms))
    h_explo = entropie_exploration(etat.population, len(etat.catalogue))
    leader_vetote = leader in etat.vetos
    consensus = (not leader_vetote) and etat.critere(
        approbations, sats_liste, h_votes
    )

    infos = {
        "round": etat.num_round,
        "leader": leader,
        "nom": attrs["nom"],
        "semaine": attrs["semaine"],
        "fitness": round(_fitness_humain(leader, etat.noms, etat.memoire,
                                         etat.vetos), 3),
        "relachement": round(etat.relachement, 3),
        "nb_approbations": nb_approuve,
        "vetos_du_round": vetos_du_round,
        "consensus": consensus,
        "entropie_votes": round(h_votes, 3),
        "entropie_exploration": round(h_explo, 3),
    }
    if etat.mode_vote == "score":
        infos["scores"] = {
            nom: int(etat.votes_round[nom]) for nom in etat.noms
        }
    etat.historique.append(infos)

    # Reinitialise les votes pour le prochain round.
    etat.votes_round = {}
    etat.idx_personne = 0

    if consensus:
        etat.consensus_atteint = True
        return True

    if etat.num_round >= etat.max_rounds:
        # Fin forcee : on retient le meilleur candidat non vetote.
        etat.consensus_atteint = True
        return True

    # Pas d'accord : on evolue le GA et on propose un nouveau candidat.
    etat.relachement += 0.05
    etat.population = _evoluer_humain(
        etat.rng, etat.population, etat.catalogue, etat.candidats,
        etat.noms, etat.memoire, etat.vetos,
    )
    etat.leader = etat.population[0]
    return False


def attrs_leader(etat: EtatNegociation) -> dict:
    """Attributs du candidat propose en ce moment."""
    return attributs_candidat(etat.catalogue, etat.leader)
