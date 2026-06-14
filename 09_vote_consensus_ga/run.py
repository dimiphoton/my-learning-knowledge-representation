"""Lance une simulation complete de vote de consensus.

Usage :
    pip install -r requirements.txt
    python 09_vote_consensus_ga/run.py

Affiche : les personnes generees, la meilleure option pour le GA seul, puis le
deroule du protocole (votes + veto payant) et le sejour de consensus retenu.
"""

from simulateur import charger_catalogue, generer_personnes
from consensus_ga import meilleur_candidat_ga, rechercher_consensus

# --- Parametres reglables de la simulation ---
NB_PERSONNES = 8
CREDITS_VETO = 2
GRAINE = 42


def afficher_personnes(personnes) -> None:
    print("=== Les votants ===")
    for p in personnes:
        semaines = sorted(p.semaines_dispo)
        print(
            f"  {p.nom:8s} | aime {p.type_prefere:8s} en {p.localisation_preferee:8s} | "
            f"activite {p.activite_preferee:12s} | "
            f"budget {p.budget_max} | animation ideale {p.animation_preferee}/10 | "
            f"semaines {semaines[0]}-{semaines[-1]} | marge {p.marge:.2f} | "
            f"vetos {p.credits_veto}"
        )
    print()


def afficher_resultat(titre, resultat) -> None:
    print(f"=== {titre} ===")
    a = resultat.attrs
    print(f"  Sejour : {a['nom']} + {a['activite']} ({a['type']}, {a['localisation']}) "
          f"semaine {a['semaine']}, {a['cout_total']} EUR/pers (dont activite {a['cout_activite']})")
    sats = resultat.satisfactions
    moyenne = sum(sats.values()) / len(sats)
    mini = min(sats.values())
    print(f"  Satisfaction moyenne : {moyenne:.2f} | minimale : {mini:.2f}")
    print(f"  Detail : {sats}")
    if resultat.nb_rounds:
        statut = "CONSENSUS atteint" if resultat.consensus else "Pas de consensus strict (meilleur compromis)"
        print(f"  {statut} en {resultat.nb_rounds} round(s)")
    print()


def main() -> None:
    catalogue = charger_catalogue()
    from simulateur import lister_candidats
    nb_candidats = len(lister_candidats(catalogue))
    print(f"Catalogue : {len(catalogue)} destinations, {nb_candidats} combinaisons "
          f"(lieu x activite x semaine).\n")

    personnes = generer_personnes(NB_PERSONNES, catalogue, credits_veto=CREDITS_VETO, graine=GRAINE)
    afficher_personnes(personnes)

    # Etape A : ce que donnerait une simple optimisation (GA seul, sans vote).
    resultat_ga = meilleur_candidat_ga(catalogue, personnes, graine=GRAINE)
    afficher_resultat("Option optimale (GA seul, sans protocole de vote)", resultat_ga)

    # Etape B : le protocole complet avec votes asynchrones et veto payant.
    print("=== Deroule du protocole de consensus ===")
    resultat = rechercher_consensus(catalogue, personnes, graine=GRAINE, verbeux=True)
    print()
    afficher_resultat("Sejour retenu par le protocole", resultat)


if __name__ == "__main__":
    main()
