# 04 — Ontologie

## Pourquoi une ontologie ici ?

Sans ontologie, les destinations seraient des lignes dans un CSV ou un dict Python ad hoc. Avec une ontologie :

- le **vocabulaire est explicite** (classes, propriétés, types) ;
- les **données sont interrogeables** via SPARQL ;
- le **schéma est extensible** (ajouter une propriété = ajouter un triplet) ;
- le domaine est **réutilisable** par d'autres systèmes (API, blockchain, autre app).

L'ontologie n'est pas décorative : c'est la **source de vérité** pour construire l'espace de recherche.

---

## Structure de `ontologie_vacances.ttl`

### Schéma (classes)

```turtle
v:Destination  a rdfs:Class .
v:TypeSejour   a rdfs:Class .
v:Localisation a rdfs:Class .
```

Trois classes qui structurent le domaine « séjour de vacances ».

### Schéma (propriétés)

| Propriété | Domaine | Portée | Rôle |
|---|---|---|---|
| `aPourType` | Destination | TypeSejour | Lien objet (ex. Plage) |
| `aPourLocalisation` | Destination | Localisation | Lien objet (ex. France) |
| `semaineDisponible` | Destination | xsd:integer | Semaines possibles (multi-valué) |
| `coutParPersonne` | Destination | xsd:integer | Coût en euros |
| `niveauAnimation` | Destination | xsd:integer | 0 (calme) à 10 (festif) |

### Données (instances)

Chaque destination est une instance typée :

```turtle
v:nice a v:Destination ;
    rdfs:label "Nice" ;
    v:aPourType v:Plage ;
    v:aPourLocalisation v:France ;
    v:coutParPersonne 600 ;
    v:niveauAnimation 7 ;
    v:semaineDisponible 28 ;
    v:semaineDisponible 29 ;
    v:semaineDisponible 30 .
```

---

## Lecture SPARQL dans le simulateur

Le simulateur exécute deux requêtes :

**Requête 1** — attributs uniques par destination :

```sparql
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
```

**Requête 2** — semaines disponibles (multi-valuées) :

```sparql
SELECT ?dest ?semaine
WHERE { ?dest v:semaineDisponible ?semaine . }
```

Résultat : un dict Python `{id: {nom, type, localisation, cout, animation, semaines}}`.

---

## Ontologies voisines (exercices)

Deux ontologies complémentaires illustrent d'autres patterns RDF :

### `ontologie_hebergement.ttl`

- **Hiérarchie** : `Hotel`, `Camping`, `Gite`, `AubergeJeunesse` → `subClassOf Hebergement`.
- **Propriété d'objet** : `situeDans` (Hebergement → Localisation).
- **Attributs** : `prixParNuit`, `confort`, `capacite`, `accepteAnimaux`.

### `ontologie_activites.ttl`

- **Hiérarchie** : `ActiviteSportive`, `ActiviteCulturelle`, `ActiviteDetente` → `subClassOf Activite`.
- **Propriété d'objet** : `seDeroulePendant` (Activite → Saison).
- **Attributs** : `intensite`, `prix`, `enInterieur`.

Ces ontologies ne sont pas branchées au moteur de consensus actuellement, mais montrent comment **étendre le domaine** (hébergement + activités + destination = séjour complet).

---

## Visualiser une ontologie

```bash
python visualiseur_ontologie.py ontologie_vacances.ttl
python visualiseur_ontologie.py ontologie_hebergement.ttl --sortie apercu.png
python visualiseur_ontologie.py ontologie_activites.ttl --sans-instances
```

Le visualiseur dessine :

- classes (bleu) avec attributs littéraux listés ;
- sous-classes (`subClassOf`, flèche bleue) ;
- propriétés d'objet (flèche rouge pointillée) ;
- instances (vert).

---

## Étendre le domaine

Pour modéliser un **nouveau cas d'usage** (ex. budget d'équipe) :

1. **Définir les classes** : `PosteBudget`, `Categorie`, `Departement`.
2. **Définir les propriétés** : `aPourCategorie`, `montant`, `echeance`.
3. **Peupler les instances** : les postes concrets.
4. **Adapter `charger_catalogue()`** : nouvelles requêtes SPARQL.
5. **Adapter `satisfaction()`** : nouveaux critères de préférence.

L'ontologie reste le point de départ : **schéma d'abord, code ensuite**.

---

## Ontologie et blockchain (perspective produit)

Dans une version blockchain, l'ontologie servirait de :

- **schéma de validation** des propositions on-chain (SHACL) ;
- **référentiel partagé** entre participants (même IRI = même concept) ;
- **métadonnées** attachées aux transactions de vote (option = instance RDF signée).

→ Voir [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md), section Phase 2.

---

## Prochaine lecture

→ [05 — Protocole de négociation](05_PROTOCOLE_NEGOCIATION.md).
