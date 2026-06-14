"""Simulateur d'opinions pour le projet de vote de consensus.

Ce module s'occupe de :
  1. lire les ontologies vacances + activites via SPARQL pour construire le
     catalogue et l'espace des candidats (destination, activite, semaine) ;
  2. generer N personnes avec des preferences, des marges de negociation et des
     credits de veto ;
  3. calculer la satisfaction d'une personne pour un candidat donne.

Aucune logique de vote ou de genetique ici : tout cela est dans consensus_ga.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rdflib import Graph

DOSSIER = Path(__file__).parent
FICHIER_TTL = DOSSIER / "ontologie_vacances.ttl"
FICHIER_ACTIVITES = DOSSIER / "ontologie_activites.ttl"
FICHIER_TTL_V2 = DOSSIER / "ontologie_vacances2.ttl"

# Candidat = (id_destination, id_activite, semaine).
Candidat = tuple[str, str, int]

# Les 6 criteres de l'ontologie 1 (type/localisation/animation).
CRITERES = ("type", "localisation", "semaine", "budget", "animation", "activite")

# Les criteres de l'ontologie 2 "realiste" (zone/milieu, le sport = "activite").
CRITERES_V2 = ("zone", "milieu", "semaine", "budget", "activite")

# Catalogue global des activites (rempli par charger_catalogue).
ACTIVITES: dict[str, dict] = {}


# =============================================================================
# 1) Lecture des ontologies
# =============================================================================
def _charger_activites(graphe: Graph) -> dict[str, dict]:
    """Lit les activites depuis le graphe RDF deja parse."""
    requete = """
    PREFIX a:    <http://exemple.org/activites/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?act ?nom ?saisonNom ?intensite ?prix ?interieur
    WHERE {
        ?act rdfs:label ?nom ;
             a:seDeroulePendant ?saison ;
             a:intensite ?intensite ;
             a:prix ?prix ;
             a:enInterieur ?interieur .
        ?saison rdfs:label ?saisonNom .
    }
    """
    activites: dict[str, dict] = {}
    for ligne in graphe.query(requete):
        act_id = str(ligne.act).split("/")[-1]
        activites[act_id] = {
            "nom": str(ligne.nom),
            "saison": str(ligne.saisonNom),
            "intensite": int(ligne.intensite),
            "prix": int(ligne.prix),
            "en_interieur": bool(ligne.interieur),
        }
    return activites


def activite_valide_pour_semaine(act: dict, semaine: int) -> bool:
    """Filtre les activites selon la saison (semaines 26-35 = ete ici)."""
    saison = act["saison"]
    if saison == "Toute l'annee":
        return True
    if saison == "Ete":
        return 26 <= semaine <= 35
    if saison == "Hiver":
        return semaine < 26 or semaine > 35
    return True


def charger_catalogue(chemin_ttl: Path = FICHIER_TTL) -> dict[str, dict]:
    """Lit les ontologies vacances + activites et renvoie le catalogue.

    Chaque destination contient : nom, type, localisation, cout, animation,
    semaines (liste), activites (liste d'ids compatibles).
    """
    global ACTIVITES

    graphe = Graph()
    graphe.parse(chemin_ttl, format="turtle")
    graphe.parse(FICHIER_ACTIVITES, format="turtle")
    ACTIVITES = _charger_activites(graphe)

    requete_attrs = """
    PREFIX v:    <http://exemple.org/vacances/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

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
    """

    catalogue: dict[str, dict] = {}
    for ligne in graphe.query(requete_attrs):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id] = {
            "nom": str(ligne.nom),
            "type": str(ligne.typeNom),
            "localisation": str(ligne.locNom),
            "cout": int(ligne.cout),
            "animation": int(ligne.anim),
            "semaines": [],
            "activites": [],
        }

    requete_semaines = """
    PREFIX v: <http://exemple.org/vacances/>
    SELECT ?dest ?semaine WHERE { ?dest v:semaineDisponible ?semaine . }
    """
    for ligne in graphe.query(requete_semaines):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id]["semaines"].append(int(ligne.semaine))

    requete_activites = """
    PREFIX v: <http://exemple.org/vacances/>
    SELECT ?dest ?act
    WHERE { ?dest v:activitePossible ?act . }
    """
    for ligne in graphe.query(requete_activites):
        dest_id = str(ligne.dest).split("/")[-1]
        act_id = str(ligne.act).split("/")[-1]
        catalogue[dest_id]["activites"].append(act_id)

    for infos in catalogue.values():
        infos["semaines"].sort()
        infos["activites"] = sorted(set(infos["activites"]))
    return catalogue


def _charger_sports(graphe: Graph) -> dict[str, dict]:
    """Lit les sports (ontologie 2) depuis le graphe RDF deja parse.

    Renvoie la meme structure que les activites, pour que le moteur (qui lit
    le global ACTIVITES) fonctionne sans modification : le sport joue le role
    de l'activite dans le candidat (destination, sport, semaine).
    """
    requete = """
    PREFIX vt:   <http://exemple.org/vacances2/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?sport ?nom ?saison ?intensite ?prix
    WHERE {
        ?sport rdfs:label ?nom ;
               vt:saison ?saison ;
               vt:intensiteSport ?intensite ;
               vt:prixSport ?prix .
    }
    """
    sports: dict[str, dict] = {}
    for ligne in graphe.query(requete):
        sport_id = str(ligne.sport).split("/")[-1]
        sports[sport_id] = {
            "nom": str(ligne.nom),
            "saison": str(ligne.saison),
            "intensite": int(ligne.intensite),
            "prix": int(ligne.prix),
        }
    return sports


def charger_catalogue_v2(chemin_ttl: Path = FICHIER_TTL_V2) -> dict[str, dict]:
    """Lit l'ontologie 2 "realiste" (zone, milieu, sports) et renvoie le catalogue.

    Chaque destination contient : nom, zone, continent, milieu, cout, semaines
    (liste), activites (liste d'ids de sports compatibles). Le format est le
    meme que charger_catalogue : le moteur n'a pas besoin de le savoir.
    """
    global ACTIVITES

    graphe = Graph()
    graphe.parse(chemin_ttl, format="turtle")
    ACTIVITES = _charger_sports(graphe)

    requete_attrs = """
    PREFIX vt:   <http://exemple.org/vacances2/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?dest ?nom ?zoneNom ?milieuNom ?cout ?contNom
    WHERE {
        ?dest a vt:Destination ;
              rdfs:label ?nom ;
              vt:dansZone ?zone ;
              vt:milieu ?milieu ;
              vt:coutParPersonne ?cout .
        ?zone rdfs:label ?zoneNom .
        ?milieu rdfs:label ?milieuNom .
        OPTIONAL { ?zone rdfs:subClassOf ?cont . ?cont rdfs:label ?contNom . }
    }
    """
    catalogue: dict[str, dict] = {}
    for ligne in graphe.query(requete_attrs):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id] = {
            "nom": str(ligne.nom),
            "zone": str(ligne.zoneNom),
            "continent": str(ligne.contNom) if ligne.contNom else "",
            "milieu": str(ligne.milieuNom),
            "cout": int(ligne.cout),
            "semaines": [],
            "activites": [],
        }

    requete_semaines = """
    PREFIX vt: <http://exemple.org/vacances2/>
    SELECT ?dest ?semaine WHERE { ?dest vt:semaineDisponible ?semaine . }
    """
    for ligne in graphe.query(requete_semaines):
        dest_id = str(ligne.dest).split("/")[-1]
        catalogue[dest_id]["semaines"].append(int(ligne.semaine))

    requete_sports = """
    PREFIX vt: <http://exemple.org/vacances2/>
    SELECT ?dest ?sport WHERE { ?dest vt:sportPossible ?sport . }
    """
    for ligne in graphe.query(requete_sports):
        dest_id = str(ligne.dest).split("/")[-1]
        sport_id = str(ligne.sport).split("/")[-1]
        catalogue[dest_id]["activites"].append(sport_id)

    for infos in catalogue.values():
        infos["semaines"].sort()
        infos["activites"] = sorted(set(infos["activites"]))
    return catalogue


def est_candidat_valide(catalogue: dict[str, dict], candidat: Candidat) -> bool:
    """Verifie qu'un triplet (lieu, activite, semaine) est autorise."""
    dest_id, act_id, semaine = candidat
    if dest_id not in catalogue:
        return False
    infos = catalogue[dest_id]
    if semaine not in infos["semaines"]:
        return False
    if act_id not in infos["activites"]:
        return False
    act = ACTIVITES.get(act_id)
    if not act or not activite_valide_pour_semaine(act, semaine):
        return False
    return True


def lister_candidats(catalogue: dict[str, dict]) -> list[Candidat]:
    """Construit l'espace de recherche : (destination, activite, semaine)."""
    candidats: list[Candidat] = []
    for dest_id, infos in catalogue.items():
        for semaine in infos["semaines"]:
            for act_id in infos["activites"]:
                act = ACTIVITES.get(act_id)
                if act and activite_valide_pour_semaine(act, semaine):
                    candidats.append((dest_id, act_id, semaine))
    return candidats


# =============================================================================
# 2) Le modele d'une personne
# =============================================================================
@dataclass
class Personne:
    """Un votant avec ses preferences et ses marges de negociation."""

    nom: str
    type_prefere: str
    localisation_preferee: str
    activite_preferee: str
    semaines_dispo: set[int]
    budget_max: int
    animation_preferee: int            # 0 (calme) a 10 (festif)
    poids: dict[str, float]            # importance de chaque critere (somme = 1)
    marge: float                       # tolerance dans [0, 1] (1 = tres conciliant)
    credits_veto: int                  # nombre de vetos payants encore disponibles
    # Criteres optionnels (utilises par l'ontologie 2 "realiste") :
    zone_preferee: str = ""            # ex "Mediterranee", "Alpes"
    milieu_prefere: str = ""           # ex "Urbain", "Nature", "Mixte"


def generer_personnes(
    n: int,
    catalogue: dict[str, dict],
    credits_veto: int = 2,
    graine: int | None = 42,
) -> list[Personne]:
    """Genere n personnes aleatoires mais coherentes avec le catalogue."""
    rng = np.random.default_rng(graine)

    types = sorted({infos["type"] for infos in catalogue.values()})
    localisations = sorted({infos["localisation"] for infos in catalogue.values()})
    activites = sorted({a["nom"] for a in ACTIVITES.values()})
    toutes_semaines = sorted({s for infos in catalogue.values() for s in infos["semaines"]})

    prenoms = [
        "Alice", "Bob", "Carol", "David", "Emma", "Frank", "Gina", "Hugo",
        "Ines", "Jules", "Kira", "Leo", "Mia", "Noe", "Olga", "Paul",
    ]

    personnes: list[Personne] = []
    for i in range(n):
        poids_bruts = rng.uniform(0.5, 1.5, size=len(CRITERES))
        poids = dict(zip(CRITERES, (poids_bruts / poids_bruts.sum()).tolist()))

        debut = int(rng.choice(toutes_semaines[:-2]))
        largeur = int(rng.integers(3, 7))
        semaines_dispo = {s for s in toutes_semaines if debut <= s < debut + largeur}
        if not semaines_dispo:
            semaines_dispo = {debut}

        personnes.append(
            Personne(
                nom=prenoms[i % len(prenoms)] + ("" if i < len(prenoms) else f"_{i}"),
                type_prefere=str(rng.choice(types)),
                localisation_preferee=str(rng.choice(localisations)),
                activite_preferee=str(rng.choice(activites)),
                semaines_dispo=semaines_dispo,
                budget_max=int(rng.choice([500, 600, 700, 800, 1000])),
                animation_preferee=int(rng.integers(0, 11)),
                poids=poids,
                marge=float(rng.uniform(0.1, 0.6)),
                credits_veto=credits_veto,
            )
        )
    return personnes


# =============================================================================
# 3) La satisfaction (intrinseque, independante de la marge)
# =============================================================================
def satisfaction(personne: Personne, attrs: dict) -> float:
    """Score dans [0, 1] mesurant l'adequation d'un candidat pour une personne.

    Generique : chaque critere n'est calcule que si l'attribut existe dans
    'attrs', et la somme finale ne porte que sur les criteres reellement
    presents dans 'personne.poids'. On peut donc brancher des ontologies
    differentes (criteres en plus ou en moins) sans toucher au moteur.
    """
    # Budget (toujours present) : penalite proportionnelle au depassement.
    cout_total = attrs["cout_total"]
    if cout_total <= personne.budget_max:
        s_budget = 1.0
    else:
        depassement = (cout_total - personne.budget_max) / personne.budget_max
        s_budget = max(0.0, 1.0 - depassement)

    scores: dict[str, float] = {"budget": s_budget}

    # Criteres categoriels : match exact, sinon un plancher selon le critere.
    categoriels = {
        "type": (personne.type_prefere, 0.2),
        "localisation": (personne.localisation_preferee, 0.4),
        "activite": (personne.activite_preferee, 0.3),
        "zone": (personne.zone_preferee, 0.3),
        "milieu": (personne.milieu_prefere, 0.3),
    }
    for critere, (prefere, plancher) in categoriels.items():
        if critere in attrs:
            scores[critere] = 1.0 if attrs[critere] == prefere else plancher

    if "semaine" in attrs:
        scores["semaine"] = 1.0 if attrs["semaine"] in personne.semaines_dispo else 0.1
    if "animation" in attrs:
        scores["animation"] = 1.0 - abs(attrs["animation"] - personne.animation_preferee) / 10.0

    # On agrege uniquement les criteres pour lesquels la personne a un poids.
    return float(sum(p * scores[c] for c, p in personne.poids.items() if c in scores))


def attributs_candidat(catalogue: dict[str, dict], candidat: Candidat) -> dict:
    """Transforme un candidat (lieu, activite, semaine) en dict d'attributs.

    Seuls les attributs reellement presents dans le catalogue sont copies :
    une ontologie peut donc exposer 'type/localisation/animation' (vacances 1)
    ou bien 'zone/milieu' (vacances 2), sans casser le reste du code.
    """
    dest_id, act_id, semaine = candidat
    infos = catalogue[dest_id]
    act = ACTIVITES[act_id]
    cout_total = infos["cout"] + act["prix"]
    attrs = {
        "destination": dest_id,
        "activite_id": act_id,
        "nom": infos["nom"],
        "cout": infos["cout"],
        "cout_activite": act["prix"],
        "cout_total": cout_total,
        "activite": act["nom"],
        "intensite_activite": act.get("intensite", 0),
        "semaine": semaine,
    }
    # Attributs categoriels optionnels selon l'ontologie chargee.
    for cle in ("type", "localisation", "animation", "zone", "continent", "milieu"):
        if cle in infos:
            attrs[cle] = infos[cle]
    return attrs


def seuil_acceptation(personne: Personne, relachement: float = 0.0) -> float:
    """Seuil de satisfaction au-dessus duquel la personne approuve un candidat."""
    seuil = 0.82 - 0.4 * personne.marge - relachement
    return max(0.25, seuil)


# =============================================================================
# 4) Profils de NPC (votants automatiques aux preferences predefinies)
# =============================================================================
def _poids(criteres: tuple[str, ...] = CRITERES, **accents: float) -> dict[str, float]:
    """Construit des poids normalises : 1.0 par defaut, releve les criteres cites.

    Exemple : _poids(type=3, animation=2) rend le type et l'animation plus
    importants que les autres criteres (qui restent a 1.0), puis normalise.
    On peut passer un autre jeu de criteres (ex CRITERES_V2) en 1er argument.
    """
    base = {critere: 1.0 for critere in criteres}
    base.update({c: v for c, v in accents.items() if c in base})
    total = sum(base.values())
    return {critere: base[critere] / total for critere in criteres}


# Chaque profil = tous les champs d'une Personne SAUF 'nom' et 'credits_veto'.
PROFILS_NPC: dict[str, dict] = {
    "Fetard plage": dict(
        type_prefere="Plage", localisation_preferee="Espagne",
        activite_preferee="Plongee", semaines_dispo={30, 31, 32, 33, 34},
        budget_max=800, animation_preferee=9, marge=0.20,
        poids=_poids(type=3, animation=2, activite=1.5),
    ),
    "Montagnard calme": dict(
        type_prefere="Montagne", localisation_preferee="Suisse",
        activite_preferee="Randonnee", semaines_dispo={27, 28, 29, 30},
        budget_max=1000, animation_preferee=3, marge=0.15,
        poids=_poids(type=3, activite=2),
    ),
    "Citadin culturel": dict(
        type_prefere="Ville", localisation_preferee="Italie",
        activite_preferee="Musee", semaines_dispo={28, 29, 30, 31, 32, 33},
        budget_max=700, animation_preferee=6, marge=0.25,
        poids=_poids(type=2.5, activite=2, localisation=1.5),
    ),
    "Econome flexible": dict(
        type_prefere="Campagne", localisation_preferee="France",
        activite_preferee="Randonnee",
        semaines_dispo={27, 28, 29, 30, 31, 32, 33},
        budget_max=450, animation_preferee=4, marge=0.40,
        poids=_poids(budget=4),
    ),
    "Routard conciliant": dict(
        type_prefere="Plage", localisation_preferee="Portugal",
        activite_preferee="Yoga",
        semaines_dispo={26, 27, 28, 29, 30, 31, 32, 33, 34, 35},
        budget_max=600, animation_preferee=5, marge=0.60,
        poids=_poids(),
    ),
    "Aventurier sportif": dict(
        type_prefere="Montagne", localisation_preferee="France",
        activite_preferee="Randonnee", semaines_dispo={27, 28, 29, 30, 31, 32},
        budget_max=700, animation_preferee=6, marge=0.30,
        poids=_poids(activite=3, type=2),
    ),
}


# Profils NPC pour l'ontologie 2 : preferences sur zone / milieu / sport.
# (type_prefere et localisation_preferee sont laisses vides car non utilises ;
#  ils n'ont aucun poids et ne comptent donc pas dans la satisfaction.)
PROFILS_NPC_V2: dict[str, dict] = {
    "Surfeur atlantique": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Atlantique", milieu_prefere="Nature",
        activite_preferee="Surf", semaines_dispo={28, 29, 30, 31, 32},
        budget_max=700, animation_preferee=5, marge=0.20,
        poids=_poids(CRITERES_V2, activite=3, zone=2),
    ),
    "Skieur alpin": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Alpes", milieu_prefere="Nature",
        activite_preferee="Ski", semaines_dispo={3, 4, 5, 6, 7},
        budget_max=1100, animation_preferee=5, marge=0.15,
        poids=_poids(CRITERES_V2, activite=3, zone=2),
    ),
    "Citadin sportif": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Mediterranee", milieu_prefere="Urbain",
        activite_preferee="Skateboard", semaines_dispo={27, 28, 29, 30, 31},
        budget_max=600, animation_preferee=7, marge=0.30,
        poids=_poids(CRITERES_V2, milieu=3, activite=2),
    ),
    "Voyageur nature": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Alpes", milieu_prefere="Nature",
        activite_preferee="Randonnee", semaines_dispo={28, 29, 30, 31, 32},
        budget_max=650, animation_preferee=3, marge=0.50,
        poids=_poids(CRITERES_V2, milieu=2, activite=1.5),
    ),
    "Plongeur tropical": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Caraibes", milieu_prefere="Mixte",
        activite_preferee="Plongee", semaines_dispo={30, 31, 32, 33},
        budget_max=1000, animation_preferee=6, marge=0.25,
        poids=_poids(CRITERES_V2, zone=3, activite=2),
    ),
    "Cavalier econome": dict(
        type_prefere="", localisation_preferee="",
        zone_preferee="Atlas", milieu_prefere="Nature",
        activite_preferee="Equitation", semaines_dispo={28, 29, 30, 31},
        budget_max=520, animation_preferee=4, marge=0.35,
        poids=_poids(CRITERES_V2, budget=3, activite=2),
    ),
}


def creer_npc(
    nom: str,
    profil: str,
    credits_veto: int = 2,
    profils: dict[str, dict] = PROFILS_NPC,
) -> Personne:
    """Cree un votant automatique (NPC) a partir d'un profil predefini.

    'profils' permet de choisir le jeu de profils (PROFILS_NPC ou
    PROFILS_NPC_V2 selon l'ontologie active).
    """
    if profil not in profils:
        raise ValueError(
            f"Profil inconnu : {profil}. Choix possibles : {list(profils)}"
        )
    return Personne(nom=nom, credits_veto=credits_veto, **profils[profil])
