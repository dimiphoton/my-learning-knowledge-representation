# Projet — Pourquoi (et quand) une base de données simple ne suffit pas

## Objectif

Répondre clairement, **preuves à l'appui**, à une question d'entretien classique :

> « Pourquoi utiliser une ontologie alors qu'une base de données ferait l'affaire ? »

On prend **les mêmes données** (un petit organigramme d'entreprise) et on les traite de deux façons : une table SQL classique, puis une ontologie OWL. On observe là où la table coince.

## Les données

Un organigramme tout simple (`entreprise.csv`) :

```
Alice (Directrice)
 ├── Bob (Manager)
 │    ├── David (Ingenieur)
 │    └── Emma (Ingenieur)
 └── Carol (Manager)
      └── Frank (Ingenieur)
```

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `entreprise.csv` | Les données brutes, partagées par les deux approches. |
| `approche_sql.py` | L'approche « base simple » (SQLite) qui montre les blocages. |
| `entreprise.ttl` | Les mêmes données en ontologie OWL (avec le schéma logique). |
| `comparaison.ipynb` | Le notebook qui met les deux approches **côte à côte**. |

Lancement : `pip install -r requirements.txt`, puis `python 08_db_vs_ontologie/approche_sql.py` et/ou ouvre `comparaison.ipynb`.

---

## Le cœur du sujet : stocker n'est pas raisonner

Une base de données simple **stocke** des valeurs. Une ontologie stocke les valeurs **et leur sens** (le schéma logique), ce qui permet à un raisonneur d'en **déduire** de nouveaux faits. Voici deux démonstrations concrètes.

### Démonstration 1 — La hiérarchie de types

Dans la table, le rôle est une simple chaîne de texte (`"Manager"`, `"Ingenieur"`...). La base ne « sait » pas qu'un Manager **est une sorte d'**Employé.

- **SQL** : demander `WHERE role = 'Employe'` renvoie **rien**. Pour avoir tout le monde, il faut **énumérer tous les rôles à la main** — et penser à mettre à jour la requête dès qu'un nouveau rôle apparaît.
- **Ontologie** : on déclare une fois `Manager rdfs:subClassOf Employe`. La requête « tous les `Employe` » fonctionne directement et reste correcte même après l'ajout d'un nouveau rôle.

### Démonstration 2 — La relation transitive (chaîne hiérarchique)

- **SQL** : le supérieur **direct** est trivial (une colonne). Mais « tous les supérieurs, même indirects » impose une requête **récursive** (`WITH RECURSIVE`) : faisable, mais c'est de la logique à coder et maintenir soi-même.
- **Ontologie** : on déclare `aPourSuperieur` comme `owl:TransitiveProperty`. On n'écrit que les liens directs ; le raisonneur déduit toute la chaîne. Une requête plate suffit.

### Bonus — Les relations inverses gratuites

On déclare `supervise owl:inverseOf aPourSuperieur`. On n'écrit jamais `supervise`, mais on peut interroger « qui Bob supervise-t-il ? » : le raisonneur a généré la relation miroir tout seul.

---

## Quand l'ontologie apporte vraiment quelque chose

Privilégier une **ontologie / un graphe de connaissances** quand :

- les données sont **fortement reliées** (réseaux, hiérarchies, généalogies, dépendances) ;
- il y a des **règles métier riches** à formaliser (héritage, transitivité, équivalences) ;
- le **schéma évolue souvent** ou est partiellement inconnu à l'avance ;
- on doit **intégrer des sources hétérogènes** ou se relier à des données externes (Wikidata, etc.) ;
- on veut que la machine **déduise** des faits implicites, pas seulement les restituer.

## Quand une base de données simple reste le bon choix

Garder une base relationnelle / un simple tableau quand :

- les données sont **tabulaires et régulières**, avec un schéma stable ;
- on a besoin de **performance brute** sur de gros volumes et de **transactions** (ACID) ;
- les questions posées sont **simples et connues d'avance** (pas de raisonnement) ;
- l'équipe et l'outillage sont déjà 100 % SQL et le besoin sémantique est faible.

> En une phrase pour l'entretien : **« Une base de données répond aux questions que j'ai prévues ; une ontologie peut répondre à des questions que je n'ai pas écrites, parce qu'elle connaît le sens des données et sait raisonner. »**
