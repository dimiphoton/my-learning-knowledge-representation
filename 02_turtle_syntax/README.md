# Étape 2 — Syntaxe Turtle avancée et vocabulaires communs

## Objectif

Rendre nos triplets **lisibles** et **réutilisables**. On arrête d'écrire des IRIs à rallonge grâce aux **préfixes**, on type correctement nos valeurs (entiers, dates), et surtout on **réutilise des vocabulaires standards** (FOAF, Schema.org) au lieu d'inventer nos propres prédicats.

---

## Concepts clés (expliqués simplement)

### 1. Les préfixes (`@prefix`)

À l'étape 1 on écrivait `<http://exemple.org/alice>` partout. Pénible et illisible.

Un préfixe déclare un **raccourci** :

```turtle
@prefix ex: <http://exemple.org/> .
```

Désormais `ex:alice` est l'écriture courte de `<http://exemple.org/alice>`. Le mot avant les `:` est le préfixe, le mot après est le **nom local**.

Deux raccourcis Turtle bien pratiques :
- `a` signifie `rdf:type` (« est un / est de type »). `ex:alice a foaf:Person` = « Alice est une Personne ».
- `;` permet d'enchaîner plusieurs prédicats **sur le même sujet** sans le réécrire :

```turtle
ex:alice foaf:name "Alice Martin" ;
         foaf:age 32 .
```

### 2. Les littéraux typés

Un littéral, ce n'est pas toujours du texte. RDF distingue les types via le vocabulaire **XSD** :

| Écriture Turtle | Type | Sens |
|---|---|---|
| `"Alice Martin"` | chaîne (par défaut) | du texte |
| `32` | `xsd:integer` | un entier (déduit automatiquement) |
| `"1994-03-15"^^xsd:date` | `xsd:date` | une date |
| `"3.14"^^xsd:decimal` | `xsd:decimal` | un nombre décimal |

La notation `"valeur"^^type` (deux accents circonflexes) attache explicitement un type à la valeur. C'est important : `32` (entier) et `"32"` (texte) ne se comportent pas pareil lors d'une comparaison en SPARQL (étape 3-4).

### 3. Réutiliser des vocabulaires standards

Plutôt que d'inventer `ex:connait`, `ex:nom`, etc., on réutilise des vocabulaires que **tout le monde** comprend déjà :

- **FOAF** (`Friend Of A Friend`) : décrire des personnes et leurs relations.
  - `foaf:Person`, `foaf:name`, `foaf:age`, `foaf:mbox` (email), `foaf:knows`.
- **Schema.org** : vocabulaire généraliste poussé par les moteurs de recherche.
  - `schema:Organization`, `schema:name`, `schema:birthDate`, `schema:worksFor`.

> Pourquoi ? Parce qu'une donnée qui utilise `foaf:name` est immédiatement comprise par n'importe quel outil du web sémantique, sans documentation. C'est l'équivalent de « parler une langue commune ».

Détail de convention : un email en FOAF s'écrit comme une IRI `mailto:` (`<mailto:alice@exemple.org>`), pas comme un simple texte.

---

## Le fichier de données

Ouvre [personnes_enrichi.ttl](personnes_enrichi.ttl). Il reprend Alice, Bob et Carol, mais :
- avec des préfixes,
- avec de vraies propriétés (âge, email, date de naissance, employeur),
- avec des organisations (`ACME`, `Globex`).

Quelques « pièges » volontaires, utiles pour les exercices SPARQL des étapes suivantes :
- **Carol n'a pas d'email** (`foaf:mbox` absent).
- **Bob ne connaît personne** (`foaf:knows` absent).

## Manipulations (notebook)

Le notebook [manipulations.ipynb](manipulations.ipynb) te fait charger ce fichier, lire des propriétés, et surtout **comprendre pourquoi le type d'un littéral compte** (un entier `32` n'est pas le texte `"32"`). Lance-le avec Jupyter après `pip install -r requirements.txt`.

---

## Exercice guidé

> **Énoncé :** Ajoute une 4ᵉ personne, **David**, dans `personnes_enrichi.ttl` :
>
> 1. C'est une `foaf:Person` nommée « David Leroy ».
> 2. Il a 29 ans (entier).
> 3. Son email est `david@exemple.org`.
> 4. Il travaille chez `ex:globex`.
> 5. Il connaît Bob et Carol.

<details>
<summary>Afficher la solution</summary>

```turtle
ex:david a foaf:Person ;
    foaf:name "David Leroy" ;
    foaf:age 29 ;
    foaf:mbox <mailto:david@exemple.org> ;
    schema:worksFor ex:globex ;
    foaf:knows ex:bob , ex:carol .
```

Astuce : la **virgule** `,` permet de répéter le **même sujet ET le même prédicat** avec plusieurs objets. Ici `foaf:knows ex:bob , ex:carol` crée deux triplets « David knows Bob » et « David knows Carol ». À ne pas confondre avec le `;` qui change de prédicat.

</details>

---

## Points à retenir

- `@prefix` raccourcit les IRIs ; `a` = `rdf:type` ; `;` change de prédicat ; `,` change d'objet.
- Les littéraux peuvent être **typés** (`^^xsd:integer`, `^^xsd:date`...).
- Réutiliser **FOAF** et **Schema.org** rend les données interopérables sans effort.

➡️ Étape suivante : maintenant qu'on a un vrai graphe, on apprend à l'**interroger** avec SPARQL.
