"""Simulateur d'opinions pour le projet de vote de consensus.

Ce module s'occupe de :
  1. lire l'ontologie (ontologie_vacances.ttl) via SPARQL pour construire le
     catalogue des destinations et l'espace des candidats (destination, semaine) ;
  2. generer N personnes avec des preferences, des marges de negociation et des
     credits de veto ;
  3. calculer la satisfaction d'une personne pour un candidat donne.

Aucune logique de vote ou de genetique ici : tout cela est dans consensus_ga.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rdflib import Graph

DOSSIER = Path(__file__).parent
FICHIER_TTL = DOSSIER / "ontologie_vacances.ttl"

# Les 5 criteres pris en compte dans la satisfaction.
CRITERES = ("type", "localisation", "semaine", "budget", "animation")


# =============================================================================
# 1) Lecture de l'ontologie
# =============================================================================
def charger_catalogue(chemin_ttl: Path = FICHIER_TTL) -> dict[str, dict]:
    """Lit l'ontologie et renvoie un dict {id_destination: attributs}.

    Chaque destination contient : nom, type, localisation, cout (int),
    animation (int 0-10) et semaines (liste d'entiers).
    """
    graphe = Graph()
    graphe.parse(chemin_ttl, format="turtle")

    # Requete 1 : les attributs a valeur unique.
    requete_attrs = """
    PREFIX v:    <http://exemple.org/vacances/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?dest ?nom ?typeNom ?locNom ?cout ?anim
    WHERE {
        ?dest a v:Destination ;
              rdfs:label ?nom ;
              v:aPourType ?type ;
              v:aPourLocalisation ?loc ;
              v:coutParPersonne ?cout ;
              v:niveauAnimation ?anim .
        ?type rdfs:label ?typeNom .
        ?loc rdfs:label ?locNom .
    }
    """

    catalogue: dict[str, dict] = {}
    for ligne in graphe.query(requete_attrs):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id] = {
            "nom": str(ligne.nom),
            "type": str(ligne.typeNom),
            "localisation": str(ligne.locNom),
            "cout": int(ligne.cout),
            "animation": int(ligne.anim),
            "semaines": [],
        }

    # Requete 2 : les semaines disponibles (valeurs multiples).
    requete_semaines = """
    PREFIX v: <http://exemple.org/vacances/>

    SELECT ?dest ?semaine
    WHERE { ?dest v:semaineDisponible ?semaine . }
    """
    for ligne in graphe.query(requete_semaines):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id]["semaines"].append(int(ligne.semaine))

    for infos in catalogue.values():
        infos["semaines"].sort()
    return catalogue


def lister_candidats(catalogue: dict[str, dict]) -> list[tuple[str, int]]:
    """Construit l'espace de recherche : tous les couples (destination, semaine)."""
    candidats = []
    for dest_id, infos in catalogue.items():
        for semaine in infos["semaines"]:
            candidats.append((dest_id, semaine))
    return candidats


# =============================================================================
# 2) Le modele d'une personne
# =============================================================================
@dataclass
class Personne:
    """Un votant avec ses preferences et ses marges de negociation."""

    nom: str
    type_prefere: str
    localisation_preferee: str
    semaines_dispo: set[int]
    budget_max: int
    animation_preferee: int            # 0 (calme) a 10 (festif)
    poids: dict[str, float]            # importance de chaque critere (somme = 1)
    marge: float                       # tolerance dans [0, 1] (1 = tres conciliant)
    credits_veto: int                  # nombre de vetos payants encore disponibles


def generer_personnes(
    n: int,
    catalogue: dict[str, dict],
    credits_veto: int = 2,
    graine: int | None = 42,
) -> list[Personne]:
    """Genere n personnes aleatoires mais coherentes avec le catalogue."""
    rng = np.random.default_rng(graine)

    types = sorted({infos["type"] for infos in catalogue.values()})
    localisations = sorted({infos["localisation"] for infos in catalogue.values()})
    toutes_semaines = sorted({s for infos in catalogue.values() for s in infos["semaines"]})

    prenoms = [
        "Alice", "Bob", "Carol", "David", "Emma", "Frank", "Gina", "Hugo",
        "Ines", "Jules", "Kira", "Leo", "Mia", "Noe", "Olga", "Paul",
    ]

    personnes: list[Personne] = []
    for i in range(n):
        # Poids aleatoires positifs, normalises pour sommer a 1.
        poids_bruts = rng.uniform(0.5, 1.5, size=len(CRITERES))
        poids = dict(zip(CRITERES, (poids_bruts / poids_bruts.sum()).tolist()))

        # Une fenetre de disponibilite continue de 3 a 6 semaines.
        debut = int(rng.choice(toutes_semaines[:-2]))
        largeur = int(rng.integers(3, 7))
        semaines_dispo = {s for s in toutes_semaines if debut <= s < debut + largeur}
        if not semaines_dispo:
            semaines_dispo = {debut}

        personnes.append(
            Personne(
                nom=prenoms[i % len(prenoms)] + ("" if i < len(prenoms) else f"_{i}"),
                type_prefere=str(rng.choice(types)),
                localisation_preferee=str(rng.choice(localisations)),
                semaines_dispo=semaines_dispo,
                budget_max=int(rng.choice([500, 600, 700, 800, 1000])),
                animation_preferee=int(rng.integers(0, 11)),
                poids=poids,
                marge=float(rng.uniform(0.1, 0.6)),
                credits_veto=credits_veto,
            )
        )
    return personnes


# =============================================================================
# 3) La satisfaction (intrinseque, independante de la marge)
# =============================================================================
def satisfaction(personne: Personne, attrs: dict) -> float:
    """Score dans [0, 1] mesurant l'adequation d'un candidat pour une personne.

    'attrs' est le dict d'attributs d'un candidat (voir attributs_candidat).
    """
    # Score par critere, chacun dans [0, 1].
    s_type = 1.0 if attrs["type"] == personne.type_prefere else 0.2
    s_loc = 1.0 if attrs["localisation"] == personne.localisation_preferee else 0.4
    s_semaine = 1.0 if attrs["semaine"] in personne.semaines_dispo else 0.1

    # Budget : parfait si dans l'enveloppe, sinon penalite progressive.
    if attrs["cout"] <= personne.budget_max:
        s_budget = 1.0
    else:
        depassement = (attrs["cout"] - personne.budget_max) / personne.budget_max
        s_budget = max(0.0, 1.0 - depassement)

    # Animation : proche de l'ideal = bon (ecart sur une echelle 0-10).
    s_anim = 1.0 - abs(attrs["animation"] - personne.animation_preferee) / 10.0

    scores = {
        "type": s_type,
        "localisation": s_loc,
        "semaine": s_semaine,
        "budget": s_budget,
        "animation": s_anim,
    }
    return float(sum(personne.poids[c] * scores[c] for c in CRITERES))


def attributs_candidat(catalogue: dict[str, dict], candidat: tuple[str, int]) -> dict:
    """Transforme un candidat (id_destination, semaine) en dict d'attributs."""
    dest_id, semaine = candidat
    infos = catalogue[dest_id]
    return {
        "destination": dest_id,
        "nom": infos["nom"],
        "type": infos["type"],
        "localisation": infos["localisation"],
        "cout": infos["cout"],
        "animation": infos["animation"],
        "semaine": semaine,
    }


def seuil_acceptation(personne: Personne, relachement: float = 0.0) -> float:
    """Seuil de satisfaction au-dessus duquel la personne approuve un candidat.

    Une grande marge => seuil plus bas (personne conciliante).
    'relachement' (>= 0) abaisse encore le seuil au fil des rounds sans consensus.
    """
    seuil = 0.82 - 0.4 * personne.marge - relachement
    return max(0.25, seuil)
