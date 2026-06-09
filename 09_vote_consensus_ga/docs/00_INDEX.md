# Documentation — Moteur de recherche de consensus

> Projet pédagogique : ontologie + algorithme génétique + protocole de vote.
> Ce dossier documente les **concepts**, l'**architecture** et la **feuille de route produit**.

---

## Par où commencer ?

| Profil | Commencer par |
|---|---|
| Découvrir l'idée en 10 min | [01 — Problème et vision](01_PROBLEME_ET_VISION.md) |
| Comprendre les concepts | [02 — Concepts clés](02_CONCEPTS_CLEFS.md) |
| Voir comment c'est câblé | [03 — Architecture](03_ARCHITECTURE.md) |
| Lancer le projet | [08 — Guide pratique](08_GUIDE_PRATIQUE.md) |
| Construire un vrai produit | [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md) |

---

## Sommaire

### Fondations

1. **[Problème et vision](01_PROBLEME_ET_VISION.md)**
   Pourquoi un moteur de consensus ? Cas d'usage, limites du vote classique, positionnement de ce prototype.

2. **[Concepts clés](02_CONCEPTS_CLEFS.md)**
   Espace de recherche, candidat, satisfaction, bien-être collectif, critère de consensus, veto payant, entropie, négociation.

3. **[Architecture](03_ARCHITECTURE.md)**
   Les cinq couches du système, flux de données, modules Python et leurs responsabilités.

### Couches du système

4. **[Ontologie](04_ONTOLOGIE.md)**
   Rôle de la couche de connaissance : schéma, catalogue, SPARQL, ontologies voisines, visualisation.

5. **[Protocole de négociation](05_PROTOCOLE_NEGOCIATION.md)**
   Rounds, votes asynchrones, assouplissement, modes binaire/score, négociation manuelle.

6. **[Optimisation et stratégies](06_OPTIMISATION_ET_STRATEGIES.md)**
   Algorithme génétique, fonctions de bien-être, critères interchangeables, moteur exhaustif.

7. **[Mesure et visualisation](07_MESURE_ET_VISUALISATION.md)**
   Entropie des votes, entropie d'exploration, arbre de négociation, lecture des graphiques.

### Mise en pratique et produit

8. **[Guide pratique](08_GUIDE_PRATIQUE.md)**
   Installation, scripts, notebooks, interface Streamlit, paramètres, extension du domaine.

9. **[Glossaire](09_GLOSSAIRE.md)**
   Définitions courtes de tous les termes utilisés dans le projet.

10. **[Prompt produit — Consensus Engine + Blockchain](PROMPT_PRODUIT.md)**
    Prompt complet pour transformer ce prototype en produit réel, en deux phases (moteur puis blockchain).

---

## Fichiers du projet (rappel rapide)

| Fichier | Couche conceptuelle |
|---|---|
| `ontologie_*.ttl` | Connaissance (schéma + données) |
| `simulateur.py` | Modèle des préférences |
| `consensus_ga.py` | Optimisation + protocole |
| `strategies.py` | Politiques interchangeables |
| `visualisation.py` | Observabilité |
| `negociation_manuelle.py` | Mode humain |
| `app_negociation.py` | Interface interactive |

Le [README](../README.md) à la racine du dossier reste l'entrée rapide (commandes, tableau des fichiers).
