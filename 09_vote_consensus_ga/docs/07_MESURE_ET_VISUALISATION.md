# 07 — Mesure et visualisation

## Pourquoi visualiser ?

Une négociation est un **processus dynamique**, pas un résultat statique. Les visualisations permettent de :

- **comprendre** pourquoi le consensus a pris N rounds ;
- **voir** quelles options ont été explorées et vetotées ;
- **mesurer** l'évolution du désaccord et de l'exploration ;
- **déboguer** le protocole (seuils trop stricts ? vetos bloquants ?).

---

## Entropie des votes (désaccord)

### Formule

Entropie de Shannon (base 2) du partage approuve/rejette, normalisée dans `[0, 1]` :

```
H = −p·log₂(p) − (1−p)·log₂(1−p)
```

où `p = nb_approuve / total`.

### Interprétation

| Valeur | Signification |
|---|---|
| `0.0` | Unanimité (100 % pour ou 100 % contre) |
| `0.5` | Désaccord modéré |
| `1.0` | Groupe parfaitement divisé (50/50) |

### Lecture de la courbe

La courbe **doit descendre** vers le consensus :

```
Entropie
  1.0 |  *
      |    *
  0.5 |       *  *
      |              *___
  0.0 |___________________
      1    2    3    4   Round
```

- Pics = rounds très divisés (souvent après un veto).
- Plateau bas = groupe converge.
- Les **bandes verticales rouges** marquent les rounds avec veto.

---

## Entropie d'exploration (diversité GA)

### Formule

Entropie de Shannon des destinations présentes dans la population GA, normalisée par `log₂(nb_destinations)`.

### Interprétation

| Valeur | Signification |
|---|---|
| Proche de `1.0` | Le GA explore encore beaucoup de destinations |
| Proche de `0.0` | La population est concentrée sur 1–2 destinations |

### Lecture conjointe

| H_votes | H_exploration | Interprétation |
|---|---|---|
| Haute | Haute | Début de négociation, beaucoup d'options |
| Haute | Basse | Désaccord sur une option déjà ciblée |
| Basse | Basse | Consensus proche ou atteint |
| Basse | Haute | Accord sur une option, mais le GA explore encore (rare) |

---

## Arbre de négociation

### Structure

Chaque **nœud** = un candidat testé à un round donné.

```
        [Départ]
           |
      [Nice s30]  ← exploré (bleu)
        /      \
  [Chamonix s32] [Barcelone s26]  ← vetoté (rouge)
                      |
                 [Annecy s31]  ← consensus (vert)
```

### Règle de construction

- Tant qu'un candidat est **vetoté**, on ne descend pas dans l'arbre (branche morte).
- Les alternatives testées ensuite sont des **frères** du dernier nœud stable.
- Le consensus final est en **vert**.

### Couleurs

| Couleur | Statut | Signification |
|---|---|---|
| Gris | Racine | Point de départ |
| Bleu | Exploré | Option testée puis abandonnée |
| Rouge | Vetoté | Branche morte (bloquée) |
| Vert | Consensus | Séjour retenu |

### Labels des arêtes

Chaque arête est étiquetée `rN` (numéro du round).

---

## Générer les visualisations

### En Python

```python
from visualisation import tracer_entropie, tracer_arbre_negociation

# historique = liste de dicts produite par rechercher_consensus() ou valider_round()
fig1 = tracer_entropie(historique, chemin="entropie.png")
fig2 = tracer_arbre_negociation(historique, chemin="arbre_negociation.png")
```

### Via script

```bash
python scenario_branches.py
# Produit entropie.png et arbre_negociation.png (scénario 3 camps)
```

### Via interface Streamlit

L'interface `app_negociation.py` affiche les deux graphiques en temps réel dans la colonne droite, mis à jour à chaque round validé.

---

## Scénario « branches multiples »

`scenario_branches.py` construit **trois camps inconciliables** :

- Camp plage (Nice, Espagne) ;
- Camp montagne (Chamonix, Suisse) ;
- Camp ville (Barcelone, Lisbonne).

Avec 3 crédits de veto chacun, le protocole est forcé d'**explorer plusieurs branches** avant de converger. Idéal pour tester les visualisations.

---

## Observabilité dans un produit

Dans un moteur de consensus production, ces métriques deviennent :

- **Dashboard temps réel** (WebSocket + graphiques) ;
- **Audit trail** (historique immuable des rounds) ;
- **Alertes** (entropie bloquée > N rounds → suggérer relâchement) ;
- **Export** (JSON/CSV de l'historique pour analyse).

→ Voir [PROMPT_PRODUIT.md](PROMPT_PRODUIT.md).

---

## Prochaine lecture

→ [08 — Guide pratique](08_GUIDE_PRATIQUE.md).
