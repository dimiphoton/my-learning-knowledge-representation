"""Etape 3 : interroger un graphe RDF avec SPARQL via rdflib.

Lancement :
    pip install -r requirements.txt   (depuis la racine du depot)
    python 03_sparql_intro/requetes.py

Le script charge personnes.ttl, puis execute plusieurs requetes SELECT
et affiche les resultats de maniere lisible.
"""

from pathlib import Path

from rdflib import Graph

# Le fichier .ttl est dans le MEME dossier que ce script.
# On construit le chemin relativement au script pour pouvoir le lancer
# depuis n'importe ou (racine du depot, dossier courant, etc.).
DOSSIER = Path(__file__).parent
FICHIER_TTL = DOSSIER / "personnes.ttl"


def charger_graphe() -> Graph:
    """Charge le fichier Turtle dans un graphe rdflib."""
    graphe = Graph()
    graphe.parse(FICHIER_TTL, format="turtle")
    return graphe


def afficher_resultats(titre: str, requete: str, graphe: Graph) -> None:
    """Execute une requete SPARQL et affiche chaque ligne de resultat."""
    print(f"\n=== {titre} ===")
    resultats = graphe.query(requete)
    if not resultats:
        print("  (aucun resultat)")
        return
    for ligne in resultats:
        # 'ligne.asdict()' donne un dict {nom_variable: valeur}.
        valeurs = {str(var): str(val) for var, val in ligne.asdict().items()}
        print(" ", valeurs)


# --- Requete 1 : toutes les personnes et leur nom ---
# Pattern de triplets : "?personne est de type foaf:Person" ET "?personne a un nom".
REQUETE_PERSONNES = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?personne ?nom
WHERE {
    ?personne a foaf:Person .
    ?personne foaf:name ?nom .
}
"""

# --- Requete 2 : les personnes de plus de 30 ans ---
# On reutilise la variable ?age pour pouvoir la comparer dans FILTER.
REQUETE_PLUS_DE_30 = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?nom ?age
WHERE {
    ?personne foaf:name ?nom .
    ?personne foaf:age ?age .
    FILTER (?age > 30)
}
"""

# --- Requete 3 : qui connait qui ? ---
REQUETE_CONNAISSANCES = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?nomSujet ?nomConnu
WHERE {
    ?sujet foaf:knows ?connu .
    ?sujet foaf:name ?nomSujet .
    ?connu foaf:name ?nomConnu .
}
"""


def main() -> None:
    graphe = charger_graphe()
    print(f"Graphe charge : {len(graphe)} triplets.")

    afficher_resultats("Requete 1 : toutes les personnes", REQUETE_PERSONNES, graphe)
    afficher_resultats("Requete 2 : personnes de plus de 30 ans", REQUETE_PLUS_DE_30, graphe)
    afficher_resultats("Requete 3 : qui connait qui", REQUETE_CONNAISSANCES, graphe)


if __name__ == "__main__":
    main()
