# Étape 4 — SPARQL avancé (filtres et modificateurs)

## Objectif

Passer de requêtes simples à des requêtes **expressives** : conditions complexes (`FILTER`), données optionnelles (`OPTIONAL`), variables calculées (`BIND`), et fonctions sur les **chaînes** et les **dates**.

---

## Concepts clés (expliqués simplement)

### 1. `FILTER` : garder seulement ce qui satisfait une condition

`FILTER` élimine les lignes qui ne respectent pas une condition booléenne.

```sparql
FILTER (?age > 30)
FILTER (?age >= 30 && ?age < 40)     # ET logique avec &&
FILTER (?age < 18 || ?age > 65)      # OU logique avec ||
```

### 2. `OPTIONAL` : récupérer une donnée *si elle existe*

Par défaut, si un triplet du motif manque, la personne est **complètement exclue** du résultat. Or Carol et Anna n'ont pas d'email : une requête qui exige `foaf:mbox` les ferait disparaître.

`OPTIONAL` règle ça : le bloc est rempli **s'il existe**, sinon la variable reste simplement non liée (vide).

```sparql
?personne foaf:name ?nom .
OPTIONAL { ?personne foaf:mbox ?email . }
```

Combiné à `FILTER(!BOUND(?email))`, on peut trouver les personnes **sans** email (voir l'exercice).

### 3. `BIND` : créer une nouvelle variable calculée

`BIND` affecte le résultat d'un calcul à une variable, réutilisable ensuite.

```sparql
BIND (YEAR(?dateNaissance) AS ?annee)
BIND (2026 - YEAR(?dateNaissance) AS ?ageApprox)
```

### 4. Fonctions utiles

Sur les **chaînes** :
- `STRSTARTS(?nom, "A")` : vrai si `?nom` commence par "A".
- `CONTAINS(?nom, "Martin")`, `UCASE(?nom)`, `LCASE(?nom)`, `STRLEN(?nom)`.

Sur les **dates** :
- `YEAR(?date)`, `MONTH(?date)`, `DAY(?date)`.
- `NOW()` : date/heure courante.

Test d'existence :
- `BOUND(?var)` : vrai si la variable a une valeur. `!BOUND(?var)` = elle est absente.

---

## Le fichier de données

[personnes.ttl](personnes.ttl) reprend nos personnes et en ajoute deux (David, Anna) pour varier les cas :
- **Carol et Anna n'ont pas d'email** → parfait pour `OPTIONAL` / `!BOUND`.
- **Alice et Anna** ont un nom qui commence par "A".
- Tout le monde a une **date de naissance** typée → parfait pour les fonctions de dates.

## Le notebook

[manipulations.ipynb](manipulations.ipynb) déroule chaque concept dans sa propre cellule, du plus simple (`FILTER`) au plus complet (combinaison `OPTIONAL` + `BIND` + fonctions).

Lancement : `pip install -r requirements.txt` puis ouvre le notebook avec Jupyter.

---

## Exercice guidé

> **Énoncé :** Trouve les personnes dont le **nom commence par 'A'** **OU** qui **n'ont pas d'email** renseigné. Affiche le nom et l'email (vide si absent).

<details>
<summary>Afficher la solution</summary>

```sparql
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?nom ?email
WHERE {
    ?personne foaf:name ?nom .
    OPTIONAL { ?personne foaf:mbox ?email . }
    FILTER ( STRSTARTS(?nom, "A") || !BOUND(?email) )
}
```

- `STRSTARTS(?nom, "A")` attrape Alice et Anna.
- `!BOUND(?email)` attrape Carol et Anna (pas d'email).
- Le `||` réunit les deux conditions.

Résultat : Alice (avec email), Anna (sans), Carol (sans).

</details>

---

## Points à retenir

- `FILTER` = condition booléenne (`&&`, `||`, comparaisons, fonctions).
- `OPTIONAL` = « récupère si ça existe », évite de perdre des lignes incomplètes.
- `BIND` = variable calculée ; `BOUND` teste la présence d'une valeur.
- Fonctions chaînes (`STRSTARTS`, `CONTAINS`...) et dates (`YEAR`, `NOW`...).

➡️ Étape suivante : on quitte les données pures pour décrire leur **schéma** (classes, sous-classes) avec RDFS.
