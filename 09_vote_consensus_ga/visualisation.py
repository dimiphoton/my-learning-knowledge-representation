"""Visualisations de la negociation : courbe d'entropie et arbre d'exploration.

Deux fonctions principales :
  - tracer_entropie(historique)        : l'entropie (desaccord + exploration) round par round ;
  - tracer_arbre_negociation(historique): l'arbre des candidats explores, avec les
                                          vetos (branches mortes) et le consensus.

Les deux acceptent un parametre 'chemin' optionnel pour sauvegarder en PNG.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx

# Couleurs par statut d'un noeud de l'arbre.
COULEURS = {
    "racine": "#9e9e9e",      # gris
    "explore": "#1f77b4",     # bleu : candidat envisage puis abandonne au profit d'un autre
    "veto": "#d62728",        # rouge : candidat vetote (branche morte)
    "consensus": "#2ca02c",   # vert : sejour finalement choisi
}


# =============================================================================
# 1) Courbe d'entropie
# =============================================================================
def tracer_entropie(historique: list[dict], chemin: str | None = None):
    """Trace l'entropie des votes et l'entropie d'exploration au fil des rounds."""
    rounds = [h["round"] for h in historique]
    h_votes = [h["entropie_votes"] for h in historique]
    h_explo = [h["entropie_exploration"] for h in historique]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(rounds, h_votes, "o-", color="#d62728", label="Entropie des votes (desaccord)")
    ax.plot(rounds, h_explo, "s-", color="#1f77b4", label="Entropie d'exploration (diversite GA)")

    # On marque les rounds ou un veto a ete pose.
    rounds_veto = [h["round"] for h in historique if h["vetos_du_round"]]
    for r in rounds_veto:
        ax.axvline(r, color="#d62728", alpha=0.15, linewidth=6)

    ax.set_xlabel("Round de negociation")
    ax.set_ylabel("Entropie (0 = ordre, 1 = desordre max)")
    ax.set_title("Compteur d'entropie : la negociation se 'refroidit' vers le consensus")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()

    if chemin:
        fig.savefig(chemin, dpi=120)
        print(f"Courbe d'entropie sauvegardee : {chemin}")
    return fig


# =============================================================================
# 2) Arbre de negociation
# =============================================================================
def construire_arbre(historique: list[dict]) -> "nx.DiGraph":
    """Construit l'arbre des candidats explores a partir de l'historique.

    Regle : tant qu'un candidat est vetote, on ne 'descend' pas dans l'arbre ;
    les alternatives essayees restent donc des freres (branches) du dernier
    candidat stable. On voit ainsi clairement les options ecartees.
    """
    arbre = nx.DiGraph()
    arbre.add_node("racine", label="Depart", statut="racine")

    parent = "racine"
    noeuds: dict[tuple, str] = {}  # candidat -> identifiant de noeud

    for infos in historique:
        candidat = tuple(infos["leader"])
        vetote = bool(infos["vetos_du_round"])
        consensus = infos["consensus"]

        if candidat not in noeuds:
            etiquette = f"{infos['nom']}\n(s{infos['semaine']})"
            identifiant = etiquette
            # Evite une collision de nom (meme libelle deja present).
            if identifiant in arbre:
                identifiant = f"{etiquette} #{infos['round']}"
            noeuds[candidat] = identifiant

            statut = "consensus" if consensus else ("veto" if vetote else "explore")
            arbre.add_node(identifiant, label=etiquette, statut=statut)
            arbre.add_edge(parent, identifiant, round=infos["round"])
        else:
            identifiant = noeuds[candidat]
            if consensus:
                arbre.nodes[identifiant]["statut"] = "consensus"

        # On n'avance dans l'arbre que si le candidat tient (ni vetote, ni final).
        if not vetote and not consensus:
            parent = identifiant
        if consensus:
            break

    return arbre


def _layout_arbre(arbre: "nx.DiGraph", racine: str = "racine") -> dict:
    """Positionne les noeuds en arbre (racine en haut), sans dependance externe."""
    positions: dict[str, tuple[float, float]] = {}
    curseur_x = [0.0]

    def parcours(noeud: str, profondeur: int) -> float:
        enfants = list(arbre.successors(noeud))
        if not enfants:
            x = curseur_x[0]
            curseur_x[0] += 1.0
        else:
            xs = [parcours(enfant, profondeur + 1) for enfant in enfants]
            x = sum(xs) / len(xs)
        positions[noeud] = (x, -float(profondeur))
        return x

    parcours(racine, 0)
    return positions


def tracer_arbre_negociation(historique: list[dict], chemin: str | None = None):
    """Dessine l'arbre des candidats explores pendant la negociation."""
    arbre = construire_arbre(historique)
    positions = _layout_arbre(arbre)

    couleurs = [COULEURS[arbre.nodes[n]["statut"]] for n in arbre.nodes]
    etiquettes = {n: arbre.nodes[n]["label"] for n in arbre.nodes}
    etiquettes_aretes = {(u, v): f"r{d['round']}" for u, v, d in arbre.edges(data=True)}

    fig, ax = plt.subplots(figsize=(11, 6))
    nx.draw_networkx_edges(arbre, positions, ax=ax, edge_color="#888888", arrows=True)
    nx.draw_networkx_nodes(arbre, positions, ax=ax, node_color=couleurs, node_size=2200)
    nx.draw_networkx_labels(arbre, positions, labels=etiquettes, ax=ax, font_size=8)
    nx.draw_networkx_edge_labels(arbre, positions, edge_labels=etiquettes_aretes, ax=ax, font_size=7)

    # Legende manuelle (placee en haut a gauche, zone vide de l'arbre).
    from matplotlib.patches import Patch
    legende = [
        Patch(color=COULEURS["explore"], label="Option envisagee"),
        Patch(color=COULEURS["veto"], label="Option vetotee (branche morte)"),
        Patch(color=COULEURS["consensus"], label="Consensus final"),
    ]
    ax.legend(handles=legende, loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False)
    ax.set_title("Arbre de negociation : branches explorees et vetos")
    ax.margins(x=0.08, y=0.18)
    ax.axis("off")
    fig.tight_layout()

    if chemin:
        fig.savefig(chemin, dpi=120)
        print(f"Arbre de negociation sauvegarde : {chemin}")
    return fig
