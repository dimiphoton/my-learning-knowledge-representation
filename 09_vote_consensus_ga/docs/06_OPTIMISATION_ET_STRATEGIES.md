# 06 — Optimisation et stratégies

## Deux moteurs de recherche

Le projet propose **deux approches** pour trouver le « meilleur » candidat :

| Moteur | Quand l'utiliser | Complexité |
|---|---|---|
| **Algorithme génétique (GA)** | Espace grand, temps réel, intégré au protocole | O(pop × gen × rounds) |
| **Exhaustif** | Espace petit (~88 candidats), vérité-terrain | O(n candidats) |

Dans ce prototype, l'espace est petit → l'exhaustif sert de **référence** pour vérifier que le GA ne se trompe pas.

---

## Algorithme génétique

### Représentation

Un **individu** = un candidat `(destination_id, semaine)`.

### Population

Taille par défaut : 40 individus, initialisés aléatoirement dans l'espace des candidats.

### Fitness

```
fitness(c) = bien_être([sat(p, c) for p in personnes]) − PENALITE_VETO × |vetos[c]|
```

### Opérateurs

| Opérateur | Description |
|---|---|
| **Sélection tournoi** | Tire 3 individus au hasard, garde le meilleur |
| **Croisement** | Enfant = destination du parent1 + semaine du parent2 (corrigée si invalide) |
| **Mutation** (taux 30 %) | Change la destination OU la semaine |
| **Élitisme** | Les 2 meilleurs passent intacts à la génération suivante |

### Intégration au protocole

Le GA ne tourne **pas une seule fois** : à chaque round sans consensus, il ré-évolue la population en tenant compte des vetos accumulés. C'est une **recherche guidée par le protocole**.

---

## Fonctions de bien-être

Définies dans `strategies.py`. Chacune prend un `np.ndarray` de satisfactions et renvoie un float.

### Utilitariste — `bien_etre_moyenne`

```python
return np.mean(sats)
```

Maximise le bonheur total. Risque : sacrifier une personne pour le bien du groupe.

### Égalitariste — `bien_etre_min`

```python
return np.min(sats)
```

Ne regarde que le plus malheureux (maximin / Rawls).

### Compromis — `bien_etre_mixte` (défaut)

```python
return 0.5 * np.mean(sats) + 0.5 * np.min(sats)
```

Équilibre efficacité et équité.

### Nash — `bien_etre_nash`

```python
return exp(mean(log(sats)))
```

Moyenne géométrique : pénalise fortement quand une personne est proche de 0.

### Leximin — `bien_etre_leximin`

```python
triees = np.sort(sats)  # la pire satisfaction en premier
poids = 0.5 ** np.arange(len(triees))
return sum(poids * triees) / sum(poids)
```

Priorité lexicographique au plus malheureux.

### Choisir une stratégie

```python
from strategies import bien_etre_nash, BIENS_ETRE

# Par nom
fonction = BIENS_ETRE["nash"]

# Dans le protocole
rechercher_consensus(catalogue, personnes, bien_etre=bien_etre_nash)
```

---

## Critères de consensus

Fabriques dans `strategies.py`. Chacune renvoie une fonction `(approbations, sats, h_votes) → bool`.

| Fabrique | Philosophie |
|---|---|
| `critere_unanimite()` | Démocratique strict |
| `critere_supermajorite(0.75)` | Consensus fort |
| `critere_majorite()` | Démocratique classique |
| `critere_plancher(0.4)` | Équité minimale garantie |
| `critere_entropie(0.2)` | Désaccord suffisamment faible |
| `critere_score_moyen(0.6)` | Pour le vote par note |

**Combiner librement** bien-être et critère :

```python
rechercher_consensus(
    catalogue, personnes,
    bien_etre=bien_etre_min,           # cherche l'équité
    critere_consensus=critere_majorite(),  # mais accepte la majorité
)
```

---

## Moteur exhaustif

```python
from strategies import meilleur_exhaustif, bien_etre_mixte

resultat = meilleur_exhaustif(catalogue, personnes, bien_etre_mixte)
# → {candidat, attrs, valeur, satisfactions}
```

Évalue **tous** les candidats. Utile pour :

- vérifier la qualité du GA ;
- comparer les stratégies de bien-être (notebook `comparaison_strategies.ipynb`) ;
- servir de baseline dans un produit (Phase 1).

---

## Modes de vote et de veto

### Vote

| Mode | Valeurs | Approbation si… |
|---|---|---|
| `binaire` | True / False | satisfaction ≥ seuil |
| `score` | 0–10 | score ≥ 6 |

### Veto

| Mode | Mécanisme |
|---|---|
| `simple` | 1 crédit par veto |
| `quadratique` | Coût croissant (1, 2, 3…) |
| `coalition` | Veto effectif seulement si ≥ k personnes |

---

## Comparer les stratégies

Le notebook `comparaison_strategies.ipynb` exécute systématiquement :

1. Toutes les fonctions de bien-être (exhaustif).
2. GA vs exhaustif (écart de qualité).
3. Tous les critères de consensus (rounds, consensus atteint).
4. Binaire vs score.
5. Les trois modes de veto.

Résultats en tableaux pandas + graphiques matplotlib.

---

## GA-lite (mode manuel)

Dans `negociation_manuelle.py`, le GA est simplifié :

- population de 30, 4 générations par round ;
- fitness basée sur les **votes humains** (pas de satisfaction simulée) ;
- candidat jamais voté = 0.5 (hypothèse optimiste).

C'est le même algorithme, mais la fitness est **apprenante** : elle s'enrichit à chaque round.

---

## Prochaine lecture

→ [07 — Mesure et visualisation](07_MESURE_ET_VISUALISATION.md).
