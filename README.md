# my-learning-knowledge-representation

Parcours de tutoriels ultra-progressifs pour apprendre la **Représentation des Connaissances** (Knowledge Representation) : de l'écriture des premiers triplets RDF jusqu'au raisonnement OWL.

## Démarrage

```bash
pip install -r requirements.txt
```

Chaque étape est dans son dossier numéroté et contient : un `README.md` (objectif, concepts, exercice + solution), les données (`.ttl`) et un notebook `manipulations.ipynb` à dérouler cellule par cellule.

## Le parcours (7 étapes)

1. [01_rdf_basics](01_rdf_basics/) — Fondations du Web Sémantique (RDF & triplets)
2. [02_turtle_syntax](02_turtle_syntax/) — Syntaxe Turtle avancée et vocabulaires communs (FOAF, Schema.org)
3. [03_sparql_intro](03_sparql_intro/) — Introduction à SPARQL (interrogation de graphes)
4. [04_sparql_avance](04_sparql_avance/) — SPARQL avancé (filtres et modificateurs)
5. [05_rdfs_ontologie](05_rdfs_ontologie/) — Ontologies avec RDFS (schéma)
6. [06_inference_rdfs](06_inference_rdfs/) — Raisonnement de base (inférence RDFS)
7. [07_owl_proprietes](07_owl_proprietes/) — Transition vers OWL (propriétés logiques)

## Projet bonus : base de données simple vs ontologie

Le dossier [08_db_vs_ontologie](08_db_vs_ontologie/) est un mini-projet qui répond, preuves à l'appui, à la question : **« pourquoi et quand une simple base de données ne suffit pas ? »**

On prend les **mêmes données** (un organigramme d'entreprise) et on les traite de deux façons pour montrer où la table SQL coince :

- **Hiérarchie de types** : en SQL, « tous les employés » oblige à énumérer les rôles à la main ; en ontologie, `subClassOf` permet à un Manager d'être automatiquement reconnu comme Employé.
- **Relation transitive** : en SQL, remonter toute la chaîne hiérarchique demande une requête récursive ; en ontologie, une propriété déclarée transitive le déduit toute seule.
- **Relation inverse** : `owl:inverseOf` génère gratuitement la relation miroir (subordonnés) qu'on n'a jamais écrite.

Idée clé : **une base stocke les données ; une ontologie stocke les données ET leur sens, ce qui permet de raisonner.** Le projet contient `approche_sql.py` (SQLite), `entreprise.ttl` (ontologie OWL) et un notebook `comparaison.ipynb` qui met les deux côte à côte. Détails et conseils « quand choisir quoi » dans son [README](08_db_vs_ontologie/README.md).

## Projet bonus : vote de consensus (ontologie + algorithme génétique)

Le dossier [09_vote_consensus_ga](09_vote_consensus_ga/) est un projet plus ambitieux : N personnes doivent choisir **un** séjour de vacances commun.

- une **ontologie** décrit l'espace des options (type, localisation, semaine, coût, animation) ;
- un **simulateur d'opinions** dote chaque personne de préférences, d'une marge de négociation et de crédits de veto ;
- un **algorithme génétique** (écrit à la main) recherche les meilleurs candidats, en maximisant un compromis moyenne/minimum (équité) ;
- un **protocole de consensus** organise des votes asynchrones, un **veto payant** (limité, donc on ne peut pas tout bloquer) et un assouplissement progressif des exigences.

Le notebook `vote_consensus.ipynb` déroule tout pas à pas, jusqu'à une démonstration où deux camps inconciliables s'affrontent et dépensent leurs vetos avant qu'un compromis n'émerge.

**Documentation conceptuelle complète** : [09_vote_consensus_ga/docs/](09_vote_consensus_ga/docs/00_INDEX.md) — concepts, architecture, guide pratique, et **[prompt produit](09_vote_consensus_ga/docs/PROMPT_PRODUIT.md)** pour construire un moteur de consensus réutilisable puis une couche blockchain.

Détails opérationnels dans son [README](09_vote_consensus_ga/README.md).

## Connaissances & compétences (checklist)

À cocher au fur et à mesure de ta progression.

### Étape 1 — RDF & triplets
- [ ] Lire et écrire un triplet Sujet–Prédicat–Objet
- [ ] Comprendre les IRI/URI comme identifiants globaux
- [ ] Distinguer une IRI d'un littéral
- [ ] Expliquer pourquoi RDF lie les données mieux que le texte brut ou le JSON

### Étape 2 — Turtle avancé & vocabulaires
- [ ] Utiliser les préfixes (`@prefix`, `a`, `;`, `,`)
- [ ] Typer les littéraux (`xsd:integer`, `xsd:date`...)
- [ ] Réutiliser des vocabulaires standards (FOAF, Schema.org)

### Étape 3 — SPARQL (introduction)
- [ ] Comprendre le pattern matching de triplets avec des variables `?x`
- [ ] Écrire une requête `SELECT ... WHERE { ... }`
- [ ] Combiner plusieurs triplets (jointure via variable partagée)

### Étape 4 — SPARQL avancé
- [ ] Filtrer avec `FILTER` (`&&`, `||`, comparaisons)
- [ ] Gérer les données manquantes avec `OPTIONAL` et `!BOUND`
- [ ] Créer une variable calculée avec `BIND`
- [ ] Utiliser les fonctions de chaînes (`STRSTARTS`...) et de dates (`YEAR`...)

### Étape 5 — Ontologies RDFS (schéma)
- [ ] Distinguer données (instances) et schéma (classes)
- [ ] Déclarer des classes (`rdfs:Class`) et des sous-classes (`rdfs:subClassOf`)
- [ ] Définir le `rdfs:domain` et le `rdfs:range` d'une propriété

### Étape 6 — Inférence RDFS
- [ ] Comprendre l'inférence (matérialiser les triplets implicites)
- [ ] Appliquer l'héritage de classe (`subClassOf`)
- [ ] Appliquer le typage par `domain`/`range`
- [ ] Lancer un raisonneur RDFS avec `owlrl`

### Étape 7 — OWL (propriétés logiques)
- [ ] Identifier les limites de RDFS
- [ ] Déclarer une propriété symétrique (`owl:SymmetricProperty`)
- [ ] Déclarer des propriétés inverses (`owl:inverseOf`)
- [ ] Déclarer une propriété transitive (`owl:TransitiveProperty`)
- [ ] Connaître l'existence des restrictions de cardinalité (`owl:Restriction`)
- [ ] Lancer un raisonneur OWL avec `owlrl`

## Convaincre un recruteur

Cette section te prépare à parler de Représentation des Connaissances en entretien (postes Data, Knowledge Engineer, Semantic Web, Knowledge Graph...). L'idée : montrer que tu maîtrises les concepts **et** que tu sais les appliquer sur des données réelles.

### Définitions à connaître (réponses courtes)

| Terme | Définition en une phrase |
|---|---|
| **RDF** | Modèle de données du Web sémantique où tout fait est un triplet Sujet–Prédicat–Objet. |
| **Triplet** | Une affirmation atomique : `(sujet, prédicat, objet)`. |
| **IRI/URI** | Identifiant global et unique d'une ressource (sert de « nom » mondial). |
| **Littéral** | Une valeur brute (texte, nombre, date), avec un type optionnel (`xsd:...`). |
| **Turtle** | Syntaxe lisible pour écrire du RDF (`.ttl`). |
| **Graphe de connaissances** | Un ensemble de triplets reliant des entités entre elles (Google KG, Wikidata...). |
| **SPARQL** | Le langage de requête du RDF (équivalent du SQL pour les graphes). |
| **Vocabulaire / Ontologie** | Un ensemble de classes et propriétés partagées pour décrire un domaine. |
| **RDFS** | Première couche d'ontologie : classes, sous-classes, domain/range. |
| **OWL** | Langage d'ontologie riche : propriétés symétriques, inverses, transitives, cardinalités. |
| **Inférence / Raisonnement** | Déduire automatiquement de nouveaux triplets à partir du schéma. |
| **SHACL** | Langage de validation de graphes RDF (vérifier que les données respectent des contraintes). |
| **JSON-LD** | Une façon d'écrire du RDF en JSON (très utilisé pour le SEO et les API). |
| **Triplestore** | Base de données spécialisée pour stocker/interroger du RDF (GraphDB, Blazegraph, Fuseki, Virtuoso). |
| **Linked Data** | Principes pour publier et relier des données ouvertes via des IRI déréférençables. |
| **SKOS** | Vocabulaire pour modéliser des thésaurus et taxonomies (concepts, `broader`/`narrower`). |

### Questions / exemples types en entretien

- « Quelle est la différence entre RDF, RDFS et OWL ? » → RDF = les données (triplets) ; RDFS = le schéma de base (classes, sous-classes) ; OWL = la logique avancée (relations symétriques, inverses, transitives, cardinalités).
- « RDFS vs base SQL ? » → SQL = schéma rigide et fermé ; RDF = schéma flexible, ouvert, conçu pour relier des données hétérogènes entre sources.
- « À quoi sert `rdfs:domain` ? » → Ce n'est PAS une validation, c'est une règle d'inférence qui type le sujet d'une propriété.
- « Donne un exemple d'inférence. » → Si `Acteur subClassOf Personne` et `dicaprio a Acteur`, alors `dicaprio a Personne` (jamais écrit, mais déduit).
- « Différence ontologie vs taxonomie ? » → Une taxonomie est une simple hiérarchie ; une ontologie ajoute des propriétés et des règles logiques.
- « Qu'est-ce qu'un knowledge graph et où en as-tu vu ? » → Wikidata, DBpedia, le Google Knowledge Graph, les graphes produits internes pour le RAG/LLM.

### Projets à réaliser (portfolio)

Du plus simple au plus impressionnant :

1. **Mini knowledge graph personnel** : modéliser un domaine que tu connais (films, recettes, jeux vidéo) en Turtle + requêtes SPARQL. (Ce repo en est déjà une base.)
2. **Interroger Wikidata en direct** : script Python qui envoie des requêtes SPARQL au endpoint public et produit un petit tableau/`pandas`.
3. **Construire et valider une ontologie** : créer une ontologie OWL d'un domaine métier, ajouter un raisonneur (`owlrl`) et de la validation `SHACL`.
4. **Conversion de données → RDF** : prendre un CSV réel (data.gouv.fr) et le transformer en graphe RDF aligné sur Schema.org.
5. **Knowledge Graph + LLM (RAG)** : utiliser un graphe pour donner du contexte structuré à un LLM (très demandé actuellement).

> Conseil : héberge 1-2 projets sur GitHub avec un README clair (objectif, données, requêtes, résultats). Un graphe interrogeable + 3 requêtes SPARQL commentées valent mieux qu'un long discours.

### Datasets & endpoints réels

- **Wikidata** — graphe collaboratif géant, endpoint SPARQL public : [query.wikidata.org](https://query.wikidata.org)
- **DBpedia** — extraction RDF de Wikipédia : [dbpedia.org/sparql](https://dbpedia.org/sparql)
- **Schema.org** — vocabulaire standard du web (SEO, JSON-LD) : [schema.org](https://schema.org)
- **GeoNames** — données géographiques mondiales : [geonames.org](https://www.geonames.org)
- **MusicBrainz** — métadonnées musicales ouvertes
- **data.gouv.fr** / **EU Open Data Portal** — open data français et européen (souvent en CSV à convertir en RDF)
- **YAGO** — base de connaissances dérivée de Wikipédia/WordNet
- **BioPortal / UniProt** — ontologies et données biomédicales (domaine très utilisateur d'OWL)
