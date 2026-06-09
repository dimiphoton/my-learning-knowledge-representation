"""Recherche de consensus : algorithme genetique + protocole de vote.

Le GA EXPLORE l'espace des candidats (destination, semaine). Le protocole de
votes asynchrones avec veto payant EVALUE les candidats proposes et guide le GA
(les vetos penalisent fortement un candidat), jusqu'a converger vers un sejour
qui met tout le monde d'accord.

Idees cles :
  - fitness = compromis entre satisfaction MOYENNE et satisfaction MINIMALE
    (le 'min' force l'equite : on evite de sacrifier une personne) ;
  - un veto coute un credit (veto PAYANT) : on ne peut donc pas tout bloquer ;
  - a chaque round sans accord, les seuils se relachent (pression a negocier).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

import numpy as np

from simulateur import (
    Personne,
    attributs_candidat,
    lister_candidats,
    satisfaction,
    seuil_acceptation,
)
from strategies import bien_etre_mixte, critere_unanimite

# --- Parametres du protocole ---
SEUIL_VETO = 0.35        # en dessous de cette satisfaction, la personne peut vetoter
PAS_RELACHEMENT = 0.05   # de combien les seuils baissent par round sans consensus
PENALITE_VETO = 1.0      # penalite de fitness par veto actif (forte = GA evite)

Candidat = tuple[str, int]


# =============================================================================
# Entropie (mesure du "desordre" de la negociation)
# =============================================================================
def entropie_votes(nb_approuve: int, total: int) -> float:
    """Entropie de Shannon (base 2) du partage des votes, dans [0, 1].

    0 = tout le monde est d'accord (unanime) ; 1 = groupe coupe en deux (50/50).
    C'est donc une mesure du DESACCORD a un round donne.
    """
    if total == 0:
        return 0.0
    p = nb_approuve / total
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def entropie_exploration(population: list[Candidat], nb_destinations: int) -> float:
    """Entropie (normalisee dans [0, 1]) des destinations presentes dans la population.

    Eleve = le GA explore beaucoup de destinations differentes ;
    proche de 0 = la population s'est concentree sur une seule option.
    """
    destinations = [candidat[0] for candidat in population]
    effectifs = Counter(destinations)
    n = len(destinations)
    h = -sum((c / n) * math.log2(c / n) for c in effectifs.values())
    h_max = math.log2(nb_destinations) if nb_destinations > 1 else 1.0
    return h / h_max if h_max > 0 else 0.0


# =============================================================================
# Fitness
# =============================================================================
def fitness(
    candidat: Candidat,
    catalogue: dict[str, dict],
    personnes: list[Personne],
    vetos: dict[Candidat, set[int]],
    bien_etre=bien_etre_mixte,
) -> float:
    """Note un candidat : bien-etre du groupe, moins une penalite par veto actif.

    'bien_etre' est une fonction d'agregation (voir strategies.py) : on peut donc
    changer la philosophie (utilitariste, egalitariste, Nash, leximin...).
    """
    attrs = attributs_candidat(catalogue, candidat)
    sats = np.array([satisfaction(p, attrs) for p in personnes])
    base = bien_etre(sats)
    nb_vetos = len(vetos.get(candidat, set()))
    return base - PENALITE_VETO * nb_vetos


# =============================================================================
# Operateurs genetiques
# =============================================================================
def _semaine_valide(rng, catalogue: dict[str, dict], dest_id: str) -> int:
    """Tire une semaine disponible au hasard pour une destination."""
    semaines = catalogue[dest_id]["semaines"]
    return int(rng.choice(semaines))


def candidat_aleatoire(rng, candidats: list[Candidat]) -> Candidat:
    return tuple(candidats[int(rng.integers(len(candidats)))])


def croisement(rng, catalogue, parent1: Candidat, parent2: Candidat) -> Candidat:
    """Enfant = destination d'un parent + semaine de l'autre (corrigee si besoin)."""
    dest = parent1[0]
    semaine = parent2[1]
    # La semaine du parent2 peut ne pas exister pour cette destination : on corrige.
    if semaine not in catalogue[dest]["semaines"]:
        semaine = _semaine_valide(rng, catalogue, dest)
    return (dest, semaine)


def mutation(rng, catalogue, candidats, candidat: Candidat, taux: float = 0.3) -> Candidat:
    """Avec une probabilite 'taux', change la destination OU la semaine."""
    dest, semaine = candidat
    if rng.random() < taux:
        if rng.random() < 0.5:
            # nouvelle destination + semaine valide
            dest = candidat_aleatoire(rng, candidats)[0]
            semaine = _semaine_valide(rng, catalogue, dest)
        else:
            semaine = _semaine_valide(rng, catalogue, dest)
    return (dest, semaine)


def _selection_tournoi(rng, population, notes, taille=3) -> Candidat:
    """Choisit le meilleur parmi 'taille' candidats tires au hasard."""
    indices = rng.integers(0, len(population), size=taille)
    meilleur = max(indices, key=lambda i: notes[i])
    return population[meilleur]


def evoluer(
    rng,
    population: list[Candidat],
    catalogue: dict[str, dict],
    candidats: list[Candidat],
    personnes: list[Personne],
    vetos: dict[Candidat, set[int]],
    n_generations: int = 5,
    elitisme: int = 2,
    bien_etre=bien_etre_mixte,
) -> list[Candidat]:
    """Fait evoluer la population pendant n_generations et la renvoie triee."""
    for _ in range(n_generations):
        notes = [fitness(c, catalogue, personnes, vetos, bien_etre) for c in population]
        ordre = sorted(range(len(population)), key=lambda i: notes[i], reverse=True)

        # Elitisme : on garde les meilleurs tels quels.
        nouvelle_pop = [population[i] for i in ordre[:elitisme]]

        # Le reste par tournoi + croisement + mutation.
        while len(nouvelle_pop) < len(population):
            p1 = _selection_tournoi(rng, population, notes)
            p2 = _selection_tournoi(rng, population, notes)
            enfant = croisement(rng, catalogue, p1, p2)
            enfant = mutation(rng, catalogue, candidats, enfant)
            nouvelle_pop.append(enfant)

        population = nouvelle_pop

    notes = [fitness(c, catalogue, personnes, vetos, bien_etre) for c in population]
    return [population[i] for i in sorted(range(len(population)), key=lambda i: notes[i], reverse=True)]


# =============================================================================
# Resultat de la recherche
# =============================================================================
@dataclass
class Resultat:
    candidat: Candidat
    attrs: dict
    satisfactions: dict[str, float]
    consensus: bool
    nb_rounds: int
    historique: list[dict] = field(default_factory=list)


def _satisfactions(personnes, attrs) -> dict[str, float]:
    return {p.nom: round(satisfaction(p, attrs), 3) for p in personnes}


# =============================================================================
# GA seul (sans protocole) : utile pour la pedagogie / comparaison
# =============================================================================
def meilleur_candidat_ga(
    catalogue: dict[str, dict],
    personnes: list[Personne],
    taille_pop: int = 40,
    n_generations: int = 30,
    graine: int = 0,
    bien_etre=bien_etre_mixte,
) -> Resultat:
    """Optimise uniquement la fitness (aucun vote, aucun veto)."""
    rng = np.random.default_rng(graine)
    candidats = lister_candidats(catalogue)
    population = [candidat_aleatoire(rng, candidats) for _ in range(taille_pop)]
    population = evoluer(
        rng, population, catalogue, candidats, personnes, {}, n_generations, bien_etre=bien_etre
    )
    meilleur = population[0]
    attrs = attributs_candidat(catalogue, meilleur)
    return Resultat(meilleur, attrs, _satisfactions(personnes, attrs), consensus=False, nb_rounds=0)


# =============================================================================
# Protocole complet : GA + votes asynchrones + veto payant
# =============================================================================
def _appliquer_vetos(
    mode_veto: str,
    intentions: list[int],
    leader: Candidat,
    vetos: dict[Candidat, set[int]],
    credits: dict[int, int],
    points: dict[int, int],
    nb_vetos_poses: dict[int, int],
    personnes: list[Personne],
    k_coalition: int,
) -> list[str]:
    """Applique les vetos d'un round selon le mode choisi et renvoie les noms des vetants.

    - "simple"      : chaque veto coute 1 credit (comportement par defaut).
    - "quadratique" : le n-ieme veto d'une personne coute n points (cout croissant).
    - "coalition"   : un veto ne passe que si au moins k personnes bloquent ensemble.
    """
    vetants: list[str] = []

    if mode_veto == "coalition":
        # On ne bloque que si la coalition est assez grande (parmi ceux qui peuvent payer).
        payeurs = [idx for idx in intentions if credits[idx] > 0]
        if len(payeurs) >= k_coalition:
            for idx in payeurs:
                credits[idx] -= 1
                vetos.setdefault(leader, set()).add(idx)
                vetants.append(personnes[idx].nom)
        return vetants

    for idx in intentions:
        if mode_veto == "quadratique":
            cout = nb_vetos_poses[idx] + 1  # 1, puis 2, puis 3...
            if points[idx] >= cout:
                points[idx] -= cout
                nb_vetos_poses[idx] += 1
                vetos.setdefault(leader, set()).add(idx)
                vetants.append(personnes[idx].nom)
        else:  # "simple"
            if credits[idx] > 0:
                credits[idx] -= 1
                vetos.setdefault(leader, set()).add(idx)
                vetants.append(personnes[idx].nom)

    return vetants


def rechercher_consensus(
    catalogue: dict[str, dict],
    personnes: list[Personne],
    taille_pop: int = 40,
    generations_par_round: int = 4,
    max_rounds: int = 15,
    graine: int = 0,
    verbeux: bool = False,
    bien_etre=None,
    critere_consensus=None,
    mode_vote: str = "binaire",
    mode_veto: str = "simple",
    k_coalition: int = 2,
) -> Resultat:
    """Boucle de consensus, entierement parametrable.

    Strategies interchangeables (voir strategies.py) :
      - bien_etre        : fonction d'agregation des satisfactions (defaut : mixte) ;
      - critere_consensus: condition d'arret (defaut : unanimite) ;
      - mode_vote        : "binaire" (oui/non) ou "score" (chacun note de 0 a 10) ;
      - mode_veto        : "simple", "quadratique" ou "coalition" (+ k_coalition).
    """
    if bien_etre is None:
        bien_etre = bien_etre_mixte
    if critere_consensus is None:
        critere_consensus = critere_unanimite()

    rng = np.random.default_rng(graine)
    candidats = lister_candidats(catalogue)
    vetos: dict[Candidat, set[int]] = {}
    population = [candidat_aleatoire(rng, candidats) for _ in range(taille_pop)]

    # Etats de veto (copies, pour ne pas modifier les personnes d'origine).
    credits = {i: p.credits_veto for i, p in enumerate(personnes)}      # simple / coalition
    points = {i: p.credits_veto for i, p in enumerate(personnes)}       # quadratique (budget)
    nb_vetos_poses = {i: 0 for i in range(len(personnes))}              # quadratique (compteur)

    historique: list[dict] = []
    relachement = 0.0

    for num_round in range(1, max_rounds + 1):
        # 1) Le GA cherche : il evite naturellement les candidats vetotes (penalite).
        population = evoluer(
            rng, population, catalogue, candidats, personnes, vetos,
            generations_par_round, bien_etre=bien_etre,
        )
        leader = population[0]
        attrs = attributs_candidat(catalogue, leader)

        # 2) Vote asynchrone : les personnes se prononcent une a une, ordre aleatoire.
        ordre = rng.permutation(len(personnes))
        approbations: dict[str, bool] = {}
        scores: dict[str, int] = {}
        sats_liste = np.zeros(len(personnes))
        intentions_veto: list[int] = []

        for idx in ordre:
            personne = personnes[idx]
            sat = satisfaction(personne, attrs)
            sats_liste[idx] = sat
            seuil = seuil_acceptation(personne, relachement)
            approuve = sat >= seuil
            approbations[personne.nom] = approuve
            if mode_vote == "score":
                scores[personne.nom] = round(sat * 10)

            # Intention de veto : tres insatisfaite et candidat non approuve.
            if (not approuve) and sat < SEUIL_VETO:
                intentions_veto.append(idx)

        # 3) Application des vetos selon le mode (simple / quadratique / coalition).
        vetos_du_round = _appliquer_vetos(
            mode_veto, intentions_veto, leader, vetos, credits, points,
            nb_vetos_poses, personnes, k_coalition,
        )

        # 4) Decision : le critere de consensus choisi tranche (sauf si leader vetote).
        leader_vetote = leader in vetos
        nb_approuve = sum(approbations.values())
        h_votes = entropie_votes(nb_approuve, len(personnes))
        h_explo = entropie_exploration(population, len(catalogue))
        approuve_liste = [approbations[p.nom] for p in personnes]
        consensus = (not leader_vetote) and critere_consensus(approuve_liste, sats_liste, h_votes)

        infos_round = {
            "round": num_round,
            "leader": leader,
            "nom": attrs["nom"],
            "semaine": attrs["semaine"],
            "fitness": round(fitness(leader, catalogue, personnes, vetos, bien_etre), 3),
            "relachement": round(relachement, 3),
            "nb_approbations": nb_approuve,
            "vetos_du_round": vetos_du_round,
            "consensus": consensus,
            "entropie_votes": round(h_votes, 3),
            "entropie_exploration": round(h_explo, 3),
        }
        if mode_vote == "score":
            infos_round["scores"] = scores
        historique.append(infos_round)

        if verbeux:
            print(
                f"Round {num_round:2d} | {attrs['nom']} (sem. {attrs['semaine']}) | "
                f"approbations {nb_approuve}/{len(personnes)} | "
                f"vetos: {vetos_du_round or '-'} | "
                f"H_votes {h_votes:.2f} H_explo {h_explo:.2f} | "
                f"{'CONSENSUS' if consensus else ''}"
            )

        if consensus:
            return Resultat(leader, attrs, _satisfactions(personnes, attrs), True, num_round, historique)

        # 5) Pas d'accord : on relache les exigences pour le round suivant.
        relachement += PAS_RELACHEMENT

    # 6) Aucun consensus : on retient le meilleur candidat NON vetote (pour le bien-etre choisi).
    candidats_libres = [c for c in candidats if c not in vetos] or candidats
    meilleur = max(candidats_libres, key=lambda c: fitness(c, catalogue, personnes, vetos, bien_etre))
    attrs = attributs_candidat(catalogue, meilleur)
    return Resultat(meilleur, attrs, _satisfactions(personnes, attrs), False, max_rounds, historique)
