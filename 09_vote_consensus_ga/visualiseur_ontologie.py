"""Visualiseur d'ontologie generique (n'importe quel fichier .ttl).

Il lit une ontologie RDF/Turtle et en dessine le schema sous forme de graphe :

  - les CLASSES (bleu), avec leurs attributs (proprietes a valeur litterale
    comme prixParNuit, listees sous le nom de la classe) ;
  - les liens de SOUS-CLASSE (rdfs:subClassOf), fleches bleues ;
  - les PROPRIETES D'OBJET (domaine -> portee entre deux classes), fleches
    rouges en pointilles, etiquetees par le nom de la propriete ;
  - les INSTANCES (vert) reliees a leur classe par un lien "type".

Usage en ligne de commande :
    python visualiseur_ontologie.py ontologie_vacances.ttl
    python visualiseur_ontologie.py famille.ttl --sans-instances --sortie a.png

Il marche aussi sur les ontologies des tutoriels (films.ttl, famille.ttl...).
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from rdflib import RDF, RDFS, Graph
from rdflib.namespace import OWL, XSD

COULEURS = {"classe": "#aed6f1", "instance": "#a9dfbf"}


def _nom_court(uri) -> str:
    """Renvoie la partie lisible d'une URI (apres le dernier / ou #)."""
    texte = str(uri)
    return texte.split("/")[-1].split("#")[-1]


def _est_litteral(portee) -> bool:
    """Vrai si la portee d'une propriete est un type de donnee (xsd:...)."""
    return str(portee).startswith(str(XSD))


def _label(graphe: Graph, sujet) -> str:
    """rdfs:label si present, sinon le nom court de l'URI."""
    etiquette = graphe.value(sujet, RDFS.label)
    return str(etiquette) if etiquette else _nom_court(sujet)


def construire_graphe(graphe: Graph, inclure_instances: bool = True):
    """Construit le graphe networkx + les attributs par classe."""
    classes = set(graphe.subjects(RDF.type, RDFS.Class))
    classes |= set(graphe.subjects(RDF.type, OWL.Class))

    # Proprietes = sujets typés "propriete" OU ayant un domaine declare.
    proprietes = set(graphe.subjects(RDF.type, RDF.Property))
    proprietes |= set(graphe.subjects(RDF.type, OWL.ObjectProperty))
    proprietes |= set(graphe.subjects(RDF.type, OWL.DatatypeProperty))
    proprietes |= set(graphe.subjects(RDFS.domain, None))

    # On separe attributs (portee litterale) et proprietes d'objet.
    attributs = defaultdict(list)
    liens_objet = []  # (domaine, portee, nom)
    for prop in proprietes:
        nom = _nom_court(prop)
        domaines = list(graphe.objects(prop, RDFS.domain))
        portees = list(graphe.objects(prop, RDFS.range))
        for domaine in domaines:
            if not portees:
                attributs[domaine].append(nom)
                continue
            for portee in portees:
                if _est_litteral(portee):
                    attributs[domaine].append(nom)
                else:
                    liens_objet.append((domaine, portee, nom))

    arbre = nx.DiGraph()

    # Noeuds de classe (avec leurs attributs listes sous le nom).
    for classe in classes:
        nom = _label(graphe, classe)
        attrs = attributs.get(classe, [])
        etiquette = nom if not attrs else nom + "\n" + "\n".join(attrs)
        arbre.add_node(_nom_court(classe), label=etiquette, genre="classe")

    # Liens de sous-classe.
    for sous, _, sur in graphe.triples((None, RDFS.subClassOf, None)):
        if sous in classes and sur in classes:
            arbre.add_edge(_nom_court(sous), _nom_court(sur),
                           relation="subClassOf")

    # Liens de propriete d'objet entre classes.
    for domaine, portee, nom in liens_objet:
        if _nom_court(domaine) in arbre and _nom_court(portee) in arbre:
            arbre.add_edge(_nom_court(domaine), _nom_court(portee),
                           relation="propriete", nom=nom)

    # Instances : ?i a ?Classe (en excluant les classes elles-memes).
    if inclure_instances:
        for instance, _, classe in graphe.triples((None, RDF.type, None)):
            if classe in classes and instance not in classes:
                ident = _nom_court(instance)
                arbre.add_node(ident, label=_label(graphe, instance),
                               genre="instance")
                arbre.add_edge(ident, _nom_court(classe), relation="type")

    return arbre


def tracer_ontologie(chemin_ttl, inclure_instances: bool = True, sortie=None):
    """Dessine l'ontologie d'un fichier .ttl. Renvoie la figure matplotlib."""
    graphe = Graph()
    graphe.parse(chemin_ttl, format="turtle")
    arbre = construire_graphe(graphe, inclure_instances)

    positions = nx.spring_layout(arbre, seed=42, k=1.4)
    couleurs = [COULEURS[arbre.nodes[n]["genre"]] for n in arbre.nodes]
    tailles = [2600 if arbre.nodes[n]["genre"] == "classe" else 1400
               for n in arbre.nodes]
    etiquettes = {n: arbre.nodes[n]["label"] for n in arbre.nodes}

    # On separe les aretes par relation pour les styliser differemment.
    aretes_sous = [(u, v) for u, v, d in arbre.edges(data=True)
                   if d["relation"] == "subClassOf"]
    aretes_obj = [(u, v) for u, v, d in arbre.edges(data=True)
                  if d["relation"] == "propriete"]
    aretes_type = [(u, v) for u, v, d in arbre.edges(data=True)
                   if d["relation"] == "type"]
    labels_obj = {(u, v): d["nom"] for u, v, d in arbre.edges(data=True)
                  if d["relation"] == "propriete"}

    fig, ax = plt.subplots(figsize=(13, 9))
    nx.draw_networkx_nodes(arbre, positions, ax=ax, node_color=couleurs,
                           node_size=tailles)
    nx.draw_networkx_labels(arbre, positions, labels=etiquettes, ax=ax,
                            font_size=8)
    nx.draw_networkx_edges(arbre, positions, ax=ax, edgelist=aretes_sous,
                           edge_color="#1f77b4", width=2.2, arrows=True)
    nx.draw_networkx_edges(arbre, positions, ax=ax, edgelist=aretes_obj,
                           edge_color="#d62728", style="dashed", arrows=True)
    nx.draw_networkx_edges(arbre, positions, ax=ax, edgelist=aretes_type,
                           edge_color="#bbbbbb", style="dotted", arrows=True)
    nx.draw_networkx_edge_labels(arbre, positions, edge_labels=labels_obj,
                                 ax=ax, font_size=7, font_color="#d62728")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legende = [
        Patch(color=COULEURS["classe"], label="Classe (+ attributs)"),
        Patch(color=COULEURS["instance"], label="Instance"),
        Line2D([0], [0], color="#1f77b4", lw=2, label="sous-classe"),
        Line2D([0], [0], color="#d62728", lw=2, ls="--",
               label="propriete d'objet"),
        Line2D([0], [0], color="#bbbbbb", lw=2, ls=":", label="type"),
    ]
    ax.legend(handles=legende, loc="upper left", frameon=False, fontsize=8)
    ax.set_title(f"Ontologie : {Path(chemin_ttl).name}")
    ax.axis("off")
    fig.tight_layout()

    if sortie:
        fig.savefig(sortie, dpi=120)
        print(f"Image sauvegardee : {sortie}")
    return fig


def main() -> None:
    parseur = argparse.ArgumentParser(description="Visualiseur d'ontologie")
    parseur.add_argument("fichier", help="chemin du fichier .ttl a visualiser")
    parseur.add_argument("--sans-instances", action="store_true",
                         help="n'afficher que le schema (classes/proprietes)")
    parseur.add_argument("--sortie", default=None,
                         help="chemin du PNG de sortie (sinon affichage)")
    args = parseur.parse_args()

    fig = tracer_ontologie(
        args.fichier,
        inclure_instances=not args.sans_instances,
        sortie=args.sortie,
    )
    if not args.sortie:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    main()
