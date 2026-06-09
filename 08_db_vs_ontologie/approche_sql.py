"""Approche "base de donnees simple" (table SQL) sur les memes donnees.

But : montrer concretement CE QUI COINCE avec une simple table, avant de voir
comment l'ontologie le resout (voir entreprise.ttl et comparaison.ipynb).

On utilise sqlite3 (inclus dans Python, aucune installation) et le CSV partage.

Lancement :
    python 08_db_vs_ontologie/approche_sql.py
"""

import csv
import sqlite3
from pathlib import Path

DOSSIER = Path(__file__).parent
FICHIER_CSV = DOSSIER / "entreprise.csv"


def charger_table() -> sqlite3.Connection:
    """Charge entreprise.csv dans une table SQLite en memoire."""
    connexion = sqlite3.connect(":memory:")
    connexion.execute(
        "CREATE TABLE employe (id TEXT, nom TEXT, role TEXT, superieur_id TEXT)"
    )
    with open(FICHIER_CSV, encoding="utf-8") as fichier:
        lecteur = csv.DictReader(fichier)
        lignes = [
            (l["id"], l["nom"], l["role"], l["superieur_id"] or None)
            for l in lecteur
        ]
    connexion.executemany("INSERT INTO employe VALUES (?, ?, ?, ?)", lignes)
    return connexion


def limite_1_hierarchie_de_types(connexion: sqlite3.Connection) -> None:
    """Limite 1 : la table ne 'sait' pas qu'un Manager est un Employe."""
    print("=== LIMITE 1 : hierarchie de types (heritage) ===")

    # On cherche naivement "tous les employes". Mais le role est un simple texte :
    # personne n'a le role exact 'Employe', donc le resultat est VIDE.
    resultat = connexion.execute(
        "SELECT nom FROM employe WHERE role = 'Employe'"
    ).fetchall()
    print("  Recherche WHERE role = 'Employe' :", resultat, "-> rien !")

    # Pour vraiment tout recuperer, il faut connaitre et lister TOUS les roles
    # a la main. Si demain on ajoute 'Stagiaire', cette requete devient fausse.
    roles_connus = ("Directrice", "Manager", "Ingenieur")
    placeholders = ",".join("?" for _ in roles_connus)
    resultat = connexion.execute(
        f"SELECT nom FROM employe WHERE role IN ({placeholders})", roles_connus
    ).fetchall()
    noms = [ligne[0] for ligne in resultat]
    print("  En listant les roles a la main :", noms)
    print("  => Le SENS 'Manager est une sorte d'Employe' n'existe pas dans la table.\n")


def limite_2_chaine_hierarchique(connexion: sqlite3.Connection) -> None:
    """Limite 2 : remonter toute la chaine hierarchique demande une requete recursive."""
    print("=== LIMITE 2 : relation transitive (chaine de management) ===")

    # Le superieur DIRECT, c'est facile :
    direct = connexion.execute(
        "SELECT nom, superieur_id FROM employe WHERE id = 'e4'"
    ).fetchone()
    print(f"  Superieur direct de David : {direct[1]} (simple).")

    # Mais "tous les superieurs, meme indirects" oblige a ecrire une requete
    # RECURSIVE (CTE WITH RECURSIVE), complexe et facile a rater.
    requete_recursive = """
    WITH RECURSIVE chaine(id, superieur_id) AS (
        SELECT id, superieur_id FROM employe WHERE id = 'e4'
        UNION ALL
        SELECT e.id, e.superieur_id
        FROM employe e
        JOIN chaine c ON e.id = c.superieur_id
    )
    SELECT sup.nom
    FROM chaine
    JOIN employe sup ON sup.id = chaine.superieur_id
    """
    superieurs = [ligne[0] for ligne in connexion.execute(requete_recursive).fetchall()]
    print(f"  Toute la chaine au-dessus de David : {superieurs}")
    print("  => Possible, mais il faut CODER la recursivite a la main a chaque fois.\n")


def main() -> None:
    connexion = charger_table()
    print("Donnees chargees dans une table SQL.\n")
    limite_1_hierarchie_de_types(connexion)
    limite_2_chaine_hierarchique(connexion)
    print("Conclusion : la table STOCKE les donnees, mais ne RAISONNE pas dessus.")
    print("L'ontologie (entreprise.ttl) declare le sens une fois, et le deduit tout seul.")


if __name__ == "__main__":
    main()
