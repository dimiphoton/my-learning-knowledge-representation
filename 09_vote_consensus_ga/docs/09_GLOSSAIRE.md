# 09 — Glossaire

| Terme | Définition |
|---|---|
| **Algorithme génétique (GA)** | Métaheuristique d'optimisation inspirée de la sélection naturelle : population, fitness, croisement, mutation, élitisme. |
| **Approbation** | Vote positif d'une personne sur un candidat (binaire : True ; score : ≥ 6/10). |
| **Arbre de négociation** | Graphe des candidats testés round par round, avec branches vetotées (rouge) et consensus (vert). |
| **Attributs (candidat)** | Dict `{nom, type, localisation, cout, animation, semaine}` lu depuis l'ontologie. |
| **Bien-être (welfare)** | Fonction qui agrège les satisfactions individuelles en un score collectif. |
| **Candidat** | Option concrète dans l'espace de recherche : `(id_destination, semaine)`. |
| **Catalogue** | Dict Python `{id: attributs}` produit par la lecture SPARQL de l'ontologie. |
| **Classe (RDF)** | Type d'entité dans le schémat (`rdfs:Class`), ex. `Destination`. |
| **Compromis final** | Meilleur candidat non vetoté retenu quand aucun consensus n'est atteint. |
| **Consensus** | Accord du groupe selon le critère choisi, sans veto actif sur le leader. |
| **Crédit de veto** | Ressource limitée consommée pour bloquer un candidat. |
| **Critère de consensus** | Condition booléenne déclenchant l'accord (unanimité, majorité…). |
| **Entropie d'exploration** | Mesure de la diversité des destinations dans la population GA. |
| **Entropie des votes** | Mesure du désaccord (partage approuve/rejette) via Shannon. |
| **Espace de recherche** | Ensemble de tous les candidats possibles (~88 ici). |
| **Fitness** | Score d'un candidat pour l'optimiseur : bien-être − pénalité veto. |
| **Instance (RDF)** | Individu concret typé par une classe, ex. `nice a v:Destination`. |
| **Leader** | Meilleur candidat de la population GA à un round donné. |
| **Marge de négociation** | Capacité d'une personne à céder (0 = rigide, 1 = conciliante). |
| **Moteur exhaustif** | Parcours de tous les candidats pour trouver l'optimum exact. |
| **Ontologie** | Description formelle d'un domaine : classes, propriétés, instances (RDF/Turtle). |
| **Pénalité de veto** | Réduction de fitness imposée aux candidats vetotés (`PENALITE_VETO = 1.0`). |
| **Personne** | Votant avec préférences, poids, marge et crédits de veto. |
| **Population (GA)** | Ensemble d'individus (candidats) maintenu par l'algorithme génétique. |
| **Propriété (RDF)** | Relation typée entre entités ou vers un littéral, ex. `coutParPersonne`. |
| **Protocole** | Ensemble de règles orchestrant les rounds : proposition, vote, veto, décision. |
| **Relâchement** | Baisse progressive des seuils d'acceptation à chaque round sans consensus. |
| **Round** | Cycle complet : proposition GA → votes → vetos → décision → relâchement éventuel. |
| **Satisfaction** | Score `[0, 1]` mesurant l'adéquation d'un candidat pour une personne. |
| **Seuil d'acceptation** | Satisfaction minimale pour qu'une personne approuve un candidat. |
| **Seuil de veto** | Satisfaction en dessous de laquelle une personne peut vetoter (`0.35`). |
| **SPARQL** | Langage de requête pour interroger des graphes RDF. |
| **Stratégie** | Combinaison interchangeable de bien-être, critère, mode de vote et mode de veto. |
| **Triplet RDF** | Assertion atomique `(sujet, prédicat, objet)`. |
| **Veto payant** | Mécanisme de blocage d'un candidat au prix d'une ressource limitée. |
| **Vote asynchrone** | Les personnes votent une à une, dans un ordre aléatoire. |
| **Vote binaire** | Approuver (True) ou rejeter (False). |
| **Vote par score** | Noter de 0 à 10. |

---

## Acronymes

| Acronyme | Signification |
|---|---|
| GA | Genetic Algorithm (algorithme génétique) |
| KR | Knowledge Representation (représentation des connaissances) |
| OWL | Web Ontology Language |
| RDF | Resource Description Framework |
| RDFS | RDF Schema |
| SPARQL | SPARQL Protocol and RDF Query Language |
| TTL | Turtle (syntaxe RDF) |

---

## Voir aussi

- [00 — Index](00_INDEX.md)
- [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md)
