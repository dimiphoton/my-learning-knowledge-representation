"""Moteur de negociation manuelle (sans UI).

L'utilisateur incarne certaines personnes et vote round par round. Les autres
peuvent etre des NPC (votants automatiques aux preferences predefinies). Le
systeme propose des candidats via un GA-lite pilote par les votes deja exprimes :
  - satisfaction connue = vote converti en [0, 1] ;
  - candidat jamais note = 0.5 (optimiste, incite a explorer) ;
  - candidat vetote = penalise dans la fitness.

Mecanismes pour FORCER la decision (tous optionnels) :
  - relachement : a chaque round sans accord, les seuils baissent (pression) ;
  - critere degressif : unanimite -> supermajorite -> majorite au fil des rounds ;
  - elimination : le menu se reduit (on retire les pires options + les vetotees) ;
  - date butoir (max_rounds) : sans accord, on impose le meilleur compromis.

Reutilise entropie_votes/exploration et les operateurs genetiques de
consensus_ga.py ; l'historique produit est compatible avec visualisation.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from consensus_ga import (
    PENALITE_VETO,
    SEUIL_VETO,
    candidat_aleatoire,
    croisement,
    entropie_exploration,
    entropie_votes,
    mutation,
)
from simulateur import (
    Candidat,
    Personne,
    attributs_candidat,
    est_candidat_valide,
    lister_candidats,
    satisfaction,
    seuil_acceptation,
)
from strategies import (
    bien_etre_mixte,
    critere_majorite,
    critere_supermajorite,
    critere_unanimite,
)

# Taille de population et generations par round (GA-lite).
TAILLE_POP = 30
GENERATIONS = 4
MAX_ROUNDS = 20

# Mecanisme "elimination" : on ne descend jamais sous ce nombre d'options.
MIN_OPTIONS = 8


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
            enfant = croisement(rng, catalogue, candidats, p1, p2)
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
    npcs: dict[str, Personne] = field(default_factory=dict)
    noms_humains: list[str] = field(default_factory=list)
    pas_relachement: float = 0.05
    critere_degressif: bool = False
    elimination: bool = False
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
    npcs: dict[str, Personne] | None = None,
    critere_degressif: bool = False,
    elimination: bool = False,
    pas_relachement: float = 0.05,
) -> EtatNegociation:
    """Initialise une negociation et propose le premier candidat.

    'npcs' : dict {nom: Personne} des votants automatiques. Les noms absents
    de ce dict sont controles par l'humain.
    """
    if critere is None:
        critere = critere_unanimite()
    npcs = npcs or {}
    noms_humains = [n for n in noms if n not in npcs]

    rng = np.random.default_rng(graine)
    candidats = lister_candidats(catalogue)
    population = [candidat_aleatoire(rng, candidats)
                  for _ in range(TAILLE_POP)]
    population = _evoluer_humain(rng, population, catalogue, candidats,
                                 noms, {}, {})

    etat = EtatNegociation(
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
        npcs=npcs,
        noms_humains=noms_humains,
        pas_relachement=pas_relachement,
        critere_degressif=critere_degressif,
        elimination=elimination,
    )
    _prevoter_npcs(etat)
    return etat


# =============================================================================
# Vote automatique des NPC
# =============================================================================
def _vote_npc(
    personne: Personne,
    attrs: dict,
    mode_vote: str,
    relachement: float,
    veto_actif: bool,
    credits: int,
) -> bool | int | str:
    """Decide le vote d'un NPC selon sa satisfaction et son seuil."""
    sat = satisfaction(personne, attrs)
    # Tres insatisfait + droit de veto disponible => il bloque.
    if veto_actif and sat < SEUIL_VETO and credits > 0:
        return "veto"
    if mode_vote == "score":
        return int(round(sat * 10))
    return bool(sat >= seuil_acceptation(personne, relachement))


def _prevoter_npcs(etat: EtatNegociation) -> None:
    """Remplit automatiquement les votes des NPC pour le candidat courant."""
    attrs = attributs_candidat(etat.catalogue, etat.leader)
    for i, nom in enumerate(etat.noms):
        if nom in etat.npcs:
            etat.votes_round[nom] = _vote_npc(
                etat.npcs[nom], attrs, etat.mode_vote,
                etat.relachement, etat.veto_actif, etat.credits_veto[i],
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


def _critere_effectif(etat: EtatNegociation) -> Callable:
    """Critere applique ce round : se relache avec le temps si demande.

    unanimite (debut) -> supermajorite 66 % -> majorite simple. C'est un
    mecanisme pour FORCER l'accord : plus on traine, moins on exige.
    """
    if not etat.critere_degressif:
        return etat.critere
    if etat.num_round < 3:
        return etat.critere
    if etat.num_round < 5:
        return critere_supermajorite(0.66)
    return critere_majorite()


def _appliquer_elimination(etat: EtatNegociation) -> None:
    """Reduit le menu : retire les pires options (et les vetotees).

    Mecanisme de forcage facon 'tour par tour' : l'espace de choix retrecit,
    donc le groupe converge forcement vers les options qui restent.
    """
    if not etat.elimination or len(etat.candidats) <= MIN_OPTIONS:
        return

    notes = [
        (_fitness_humain(c, etat.noms, etat.memoire, etat.vetos), c)
        for c in etat.candidats
    ]
    notes.sort(key=lambda x: x[0], reverse=True)
    garder = max(MIN_OPTIONS, len(etat.candidats) // 2)
    restants = [c for _, c in notes[:garder] if c not in etat.vetos]
    etat.candidats = restants or [c for _, c in notes[:garder]]

    # On reconstruit la population sur le menu reduit.
    etat.population = [
        candidat_aleatoire(etat.rng, etat.candidats)
        for _ in range(TAILLE_POP)
    ]


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
    critere = _critere_effectif(etat)
    consensus = (not leader_vetote) and critere(
        approbations, sats_liste, h_votes
    )

    infos = {
        "round": etat.num_round,
        "leader": leader,
        "nom": attrs["nom"],
        "activite": attrs["activite"],
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
        # Date butoir atteinte : on impose le meilleur compromis non vetote.
        etat.consensus_atteint = True
        return True

    # Pas d'accord : pression a negocier, retrecissement, nouveau candidat.
    etat.relachement += etat.pas_relachement
    _appliquer_elimination(etat)
    etat.population = _evoluer_humain(
        etat.rng, etat.population, etat.catalogue, etat.candidats,
        etat.noms, etat.memoire, etat.vetos,
    )
    etat.leader = etat.population[0]
    _prevoter_npcs(etat)
    return False


def jouer_automatiquement(etat: EtatNegociation,
                          max_steps: int | None = None) -> bool:
    """Enchaine les rounds tant que les NPC suffisent (aucun humain a voter).

    Utile quand tous les votants sont des NPC : la negociation se deroule
    seule jusqu'au consensus ou a la date butoir. Renvoie True si consensus.
    """
    limite = max_steps if max_steps is not None else etat.max_rounds + 1
    etapes = 0
    while not etat.consensus_atteint and etapes < limite:
        if not tous_ont_vote(etat):
            break  # des humains doivent encore se prononcer
        valider_round(etat)
        etapes += 1
    return etat.consensus_atteint


def attrs_leader(etat: EtatNegociation) -> dict:
    """Attributs du candidat propose en ce moment."""
    return attributs_candidat(etat.catalogue, etat.leader)
