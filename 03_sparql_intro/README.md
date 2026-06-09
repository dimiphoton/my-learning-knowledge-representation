# Étape 3 — Introduction à SPARQL (interrogation de graphes)

## Objectif

Apprendre à **poser des questions** à un graphe RDF avec le langage **SPARQL**. C'est l'équivalent du SQL, mais pour les triplets. On exécute les requêtes en Python avec `rdflib`.

---

## Concepts clés (expliqués simplement)

### 1. Le principe : le « pattern matching » de triplets

SPARQL fonctionne par **filtrage de motifs**. On décrit un motif de triplets avec des **variables** (préfixées par `?`), et SPARQL cherche dans le graphe toutes les combinaisons qui collent au motif.

Exemple de motif :

```sparql
?personne a foaf:Person .
```

« Trouve tout ce qui (`?personne`) est de type `foaf:Person`. » SPARQL va essayer de remplacer `?personne` par chaque nœud du graphe et garder ceux qui satisfont le triplet.

Si on ajoute un 2ᵉ triplet avec la **même variable**, les deux doivent être vrais en même temps (comme un « ET ») :

```sparql
?personne a foaf:Person .
?personne foaf:name ?nom .
```

→ « les `?personne` qui sont des Person **et** qui ont un `?nom` ».

### 2. La structure d'une requête SELECT

```sparql
PREFIX foaf: <http://xmlns.com/foaf/0.1/>   # 1. les prefixes (comme en Turtle)

SELECT ?nom ?age                            # 2. les variables qu'on veut afficher
WHERE {                                     # 3. le motif a faire correspondre
    ?personne foaf:name ?nom .
    ?personne foaf:age ?age .
}
```

- **PREFIX** : déclare les raccourcis (même rôle que `@prefix` en Turtle).
- **SELECT** : liste les colonnes du résultat (les variables à retourner).
- **WHERE { ... }** : le graphe-motif ; chaque ligne est un triplet à satisfaire, terminé par `.`.

### 3. Petit aperçu de FILTER

Pour garder seulement certains résultats selon une condition, on ajoute un `FILTER` :

```sparql
FILTER (?age > 30)
```

On ne fait que l'effleurer ici (« plus de 30 ans »). Les filtres et conditions avancées sont le cœur de l'étape 4.

---

## Le fichier de données

[personnes.ttl](personnes.ttl) est une copie autonome du graphe de l'étape 2 (Alice, Bob, Carol + organisations), pour que ce dossier fonctionne seul.

## Le script

[requetes.py](requetes.py) charge le graphe avec `rdflib`, puis exécute 3 requêtes :
1. Toutes les personnes et leur nom.
2. Les personnes de plus de 30 ans (`FILTER`).
3. Qui connaît qui.

Il existe deux façons de pratiquer :
- le **script** [requetes.py](requetes.py) (exécution en une fois) ;
- le **notebook** [manipulations.ipynb](manipulations.ipynb) (recommandé), qui construit les requêtes **progressivement** : un triplet, puis deux, puis un `FILTER`, et te laisse modifier les valeurs en direct.

### Comment lancer le script

Depuis la **racine du dépôt** :

```bash
pip install -r requirements.txt
python 03_sparql_intro/requetes.py
```

Sortie attendue (les personnes > 30 ans sont Alice 32 et Carol 41) :

```
Graphe charge : 22 triplets.

=== Requete 1 : toutes les personnes ===
  {'personne': 'http://exemple.org/alice', 'nom': 'Alice Martin'}
  {'personne': 'http://exemple.org/bob', 'nom': 'Bob Dupont'}
  {'personne': 'http://exemple.org/carol', 'nom': 'Carol Nguyen'}

=== Requete 2 : personnes de plus de 30 ans ===
  {'nom': 'Alice Martin', 'age': '32'}
  {'nom': 'Carol Nguyen', 'age': '41'}

=== Requete 3 : qui connait qui ===
  {'nomSujet': 'Alice Martin', 'nomConnu': 'Bob Dupont'}
  {'nomSujet': 'Carol Nguyen', 'nomConnu': 'Alice Martin'}
```

(L'ordre des lignes peut varier : un graphe RDF n'est pas ordonné.)

---

## Exercice guidé

> **Énoncé :** Écris une requête SPARQL qui retourne **le nom de chaque personne et le nom de son employeur**.
>
> Indices :
> - l'employeur est relié par `schema:worksFor` ;
> - le nom d'une organisation utilise `schema:name`.

<details>
<summary>Afficher la solution</summary>

```sparql
PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
PREFIX schema: <https://schema.org/>

SELECT ?nomPersonne ?nomEmployeur
WHERE {
    ?personne foaf:name ?nomPersonne .
    ?personne schema:worksFor ?employeur .
    ?employeur schema:name ?nomEmployeur .
}
```

Pour la tester, tu peux l'ajouter dans `requetes.py` :

```python
REQUETE_EMPLOYEURS = """
PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
PREFIX schema: <https://schema.org/>

SELECT ?nomPersonne ?nomEmployeur
WHERE {
    ?personne foaf:name ?nomPersonne .
    ?personne schema:worksFor ?employeur .
    ?employeur schema:name ?nomEmployeur .
}
"""

# ... puis dans main() :
afficher_resultats("Exercice : employeurs", REQUETE_EMPLOYEURS, graphe)
```

Résultat attendu : Alice et Bob → « ACME Corporation », Carol → « Globex ».

</details>

---

## Points à retenir

- SPARQL = filtrage de **motifs de triplets** avec des **variables** `?x`.
- Structure : `PREFIX` → `SELECT` (colonnes) → `WHERE { motif }`.
- Réutiliser la **même variable** dans plusieurs triplets agit comme une jointure (un « ET »).

➡️ Étape suivante : conditions avancées avec `FILTER`, `OPTIONAL`, `BIND` et les fonctions sur chaînes/dates.
