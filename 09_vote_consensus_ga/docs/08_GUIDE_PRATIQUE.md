# 08 — Guide pratique

## Installation

```bash
# Depuis la racine du dépôt
pip install -r requirements.txt
```

Dépendances principales : `rdflib`, `numpy`, `matplotlib`, `networkx`, `pandas`, `streamlit`, `notebook`.

---

## Lancer les démonstrations

### Simulation automatique complète

```bash
python 09_vote_consensus_ga/run.py
```

Affiche : personnes générées, meilleur candidat GA seul, déroulé round par round, résultat final.

### Scénario multi-branches (entropie + arbre)

```bash
python 09_vote_consensus_ga/scenario_branches.py
```

Produit `entropie.png` et `arbre_negociation.png` dans le dossier.

### Interface interactive (négociation manuelle)

```bash
streamlit run 09_vote_consensus_ga/app_negociation.py
```

Ouvre un navigateur : panneau de vote à gauche, visualisations à droite.

### Visualiser une ontologie

```bash
python 09_vote_consensus_ga/visualiseur_ontologie.py ontologie_activites.ttl
python 09_vote_consensus_ga/visualiseur_ontologie.py ontologie_vacances.ttl --sans-instances --sortie schema.png
```

---

## Notebooks pédagogiques

| Notebook | Contenu |
|---|---|
| `vote_consensus.ipynb` | Parcours complet : ontologie → opinions → GA → protocole → veto → entropie |
| `comparaison_strategies.ipynb` | Tableaux et graphiques comparant toutes les stratégies |

Ouvrir avec Jupyter ou VS Code, exécuter cellule par cellule.

---

## Utiliser le moteur en Python

### Protocole automatique

```python
from simulateur import charger_catalogue, generer_personnes
from consensus_ga import rechercher_consensus
from strategies import bien_etre_nash, critere_supermajorite

catalogue = charger_catalogue()
personnes = generer_personnes(6, catalogue, credits_veto=2, graine=42)

resultat = rechercher_consensus(
    catalogue, personnes,
    bien_etre=bien_etre_nash,
    critere_consensus=critere_supermajorite(0.75),
    mode_vote="score",
    mode_veto="coalition",
    k_coalition=2,
    verbeux=True,
)

print(resultat.candidat, resultat.consensus, resultat.nb_rounds)
```

### Négociation manuelle (programmatique)

```python
from simulateur import charger_catalogue
from negociation_manuelle import demarrer, enregistrer_vote, valider_round

catalogue = charger_catalogue()
etat = demarrer(catalogue, ["Alice", "Bob", "Carol"], mode_vote="binaire")

for nom in etat.noms:
    enregistrer_vote(etat, nom, True)

if valider_round(etat):
    print("Consensus !", etat.leader)
```

### Vérité-terrain (exhaustif)

```python
from strategies import meilleur_exhaustif, BIENS_ETRE

for nom, fonction in BIENS_ETRE.items():
    r = meilleur_exhaustif(catalogue, personnes, fonction)
    print(nom, "→", r["attrs"]["nom"], r["valeur"])
```

---

## Paramètres à régler

### Simulation (`run.py`)

| Variable | Défaut | Effet |
|---|---|---|
| `NB_PERSONNES` | 8 | Taille du groupe |
| `CREDITS_VETO` | 2 | Vetos par personne |
| `GRAINE` | 0 | Reproductibilité |

### Protocole (`consensus_ga.py`)

| Variable | Défaut | Effet |
|---|---|---|
| `SEUIL_VETO` | 0.35 | Seuil pour déclencher un veto |
| `PAS_RELACHEMENT` | 0.05 | Baisse des seuils par round |
| `PENALITE_VETO` | 1.0 | Pénalité fitness |
| `taille_pop` | 40 | Taille population GA |
| `generations_par_round` | 4 | Générations GA par round |
| `max_rounds` | 15 | Limite de rounds |

### Seuils d'acceptation (`simulateur.py`)

```python
seuil = 0.82 - 0.4 * personne.marge - relachement
return max(0.25, seuil)
```

Augmenter `0.82` → négociation plus longue. Diminuer → consensus plus rapide.

---

## Étendre le projet

### Ajouter une destination

Éditer `ontologie_vacances.ttl` :

```turtle
v:corse a v:Destination ;
    rdfs:label "Corse" ;
    v:aPourType v:Plage ;
    v:aPourLocalisation v:France ;
    v:coutParPersonne 550 ;
    v:niveauAnimation 6 ;
    v:semaineDisponible 30 ;
    v:semaineDisponible 31 .
```

Relancer — le catalogue est rechargé automatiquement.

### Ajouter une fonction de bien-être

Dans `strategies.py` :

```python
def bien_etre_median(sats: np.ndarray) -> float:
    return float(np.median(sats))

BIENS_ETRE["median"] = bien_etre_median
```

### Ajouter un critère de consensus

```python
def critere_quorum(min_votes: int):
    def critere(approbations, sats, h_votes):
        return sum(approbations) >= min_votes
    return critere
```

### Nouveau domaine

1. Créer `ontologie_mon_domaine.ttl`.
2. Écrire `charger_mon_catalogue()` avec les requêtes SPARQL adaptées.
3. Adapter `satisfaction()` aux nouveaux critères.
4. Réutiliser `consensus_ga.py` et `strategies.py` tels quels.

---

## Parcours d'apprentissage recommandé

1. Lire [02 — Concepts clés](02_CONCEPTS_CLEFS.md).
2. Exécuter `run.py` et observer la sortie console.
3. Ouvrir `vote_consensus.ipynb`, dérouler les sections une par une.
4. Lancer `scenario_branches.py`, étudier les PNG.
5. Jouer avec `app_negociation.py` (mode manuel).
6. Ouvrir `comparaison_strategies.ipynb` pour comparer les stratégies.
7. Lire [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md) pour la suite.

---

## Prochaine lecture

→ [09 — Glossaire](09_GLOSSAIRE.md) ou [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md).
