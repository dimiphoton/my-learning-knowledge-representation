"""Scenario "multi-branches" : trois camps inconciliables.

Plage, Montagne et Ville s'affrontent. A chaque round, les deux camps leses par
le leader le vetotent (tant qu'ils ont des credits), ce qui force le GA a explorer
une autre option : on voit donc plusieurs BRANCHES dans l'arbre de negociation.

On genere aussi deux figures :
  - entropie.png            : l'entropie (desaccord + exploration) round par round ;
  - arbre_negociation.png   : l'arbre des candidats explores (avec vetos et consensus).

Usage :
    python 09_vote_consensus_ga/scenario_branches.py
"""

import matplotlib

matplotlib.use("Agg")  # backend sans fenetre (on sauvegarde des PNG)

from pathlib import Path

from consensus_ga import rechercher_consensus
from simulateur import Personne, charger_catalogue
from visualisation import tracer_arbre_negociation, tracer_entropie

DOSSIER = Path(__file__).parent

# Le TYPE pese 85 % : chaque camp est intransigeant sur le genre de sejour.
POIDS_TYPE = {
    "type": 0.80, "localisation": 0.04, "semaine": 0.05,
    "budget": 0.03, "animation": 0.03, "activite": 0.05,
}


def construire_groupe() -> list[Personne]:
    """Trois camps de 2 personnes, aux gouts incompatibles, avec 3 vetos chacun."""
    camp_plage = [
        Personne(nom, "Plage", "Espagne", "Plongee", {30, 31, 32, 33},
                 800, 8, POIDS_TYPE, marge=0.15, credits_veto=3)
        for nom in ("Lou", "Manon")
    ]
    camp_montagne = [
        Personne(nom, "Montagne", "Suisse", "Randonnee", {27, 28, 29, 30},
                 1200, 3, POIDS_TYPE, marge=0.15, credits_veto=3)
        for nom in ("Tom", "Zoe")
    ]
    camp_ville = [
        Personne(nom, "Ville", "Italie", "Musee", {30, 31, 32, 33},
                 800, 7, POIDS_TYPE, marge=0.15, credits_veto=3)
        for nom in ("Ali", "Bea")
    ]
    return camp_plage + camp_montagne + camp_ville


def main() -> None:
    catalogue = charger_catalogue()
    groupe = construire_groupe()

    print("=== Scenario multi-branches : Plage vs Montagne vs Ville ===\n")
    resultat = rechercher_consensus(
        catalogue, groupe, graine=1, generations_par_round=4, max_rounds=25, verbeux=True
    )

    print()
    a = resultat.attrs
    statut = "CONSENSUS" if resultat.consensus else "compromis impose (fin des rounds)"
    print(f"=> Sejour retenu : {a['nom']} + {a['activite']} "
          f"({a['type']}, {a['localisation']}) semaine {a['semaine']} | {statut}")
    print(f"   Satisfactions : {resultat.satisfactions}")

    # Combien de candidats distincts ont ete explores / vetotes ?
    explores = {tuple(h["leader"]) for h in resultat.historique}
    vetotes = {tuple(h["leader"]) for h in resultat.historique if h["vetos_du_round"]}
    print(f"\n   {len(explores)} candidats distincts explores, dont {len(vetotes)} vetotes.")

    # Figures.
    tracer_entropie(resultat.historique, chemin=str(DOSSIER / "entropie.png"))
    tracer_arbre_negociation(resultat.historique, chemin=str(DOSSIER / "arbre_negociation.png"))


if __name__ == "__main__":
    main()
