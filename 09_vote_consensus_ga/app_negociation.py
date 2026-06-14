"""Interface Streamlit : simuler soi-meme une negociation a plusieurs.

Lancement :
    streamlit run 09_vote_consensus_ga/app_negociation.py

Onglets :
  - Vote        : proposition courante, votes humains, validation du round
  - Entropie    : courbe de desaccord et diversite d'exploration
  - Chemins     : arbre des options explorees (vetos, consensus)
  - Historique  : tableau de tous les rounds + chronologie textuelle
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from negociation_manuelle import (
    attrs_leader,
    demarrer,
    enregistrer_vote,
    jouer_automatiquement,
    tous_ont_vote,
    valider_round,
)
from simulateur import (
    PROFILS_NPC,
    PROFILS_NPC_V2,
    charger_catalogue,
    charger_catalogue_v2,
    creer_npc,
)
from strategies import (
    critere_majorite,
    critere_plancher,
    critere_score_moyen,
    critere_supermajorite,
    critere_unanimite,
)
from visualisation import (
    construire_arbre,
    tracer_arbre_negociation,
    tracer_entropie,
)

PRENOMS = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Gina", "Hugo"]
PRENOMS_NPC = ["Nina", "Otto", "Rita", "Sami", "Tina", "Vito"]

ONTOLOGIES = {
    "Vacances (simple : type / localisation)": {
        "loader": charger_catalogue,
        "profils": PROFILS_NPC,
    },
    "Vacances (realiste : zone / milieu / sport)": {
        "loader": charger_catalogue_v2,
        "profils": PROFILS_NPC_V2,
    },
}

CRITERES = {
    "Unanimite (tous approuvent)": critere_unanimite(),
    "Supermajorite (75 %)": critere_supermajorite(0.75),
    "Majorite simple (> 50 %)": critere_majorite(),
    "Plancher (personne < 40 %)": critere_plancher(0.4),
    "Score moyen >= 6/10": critere_score_moyen(0.6),
}


# -----------------------------------------------------------------------------
# Initialisation
# -----------------------------------------------------------------------------
def _init_negociation(config: dict) -> None:
    """Cree ou reinitialise l'etat dans session_state a partir de la config."""
    ontologie = ONTOLOGIES[config["ontologie"]]
    profils_dispo = ontologie["profils"]
    catalogue = ontologie["loader"]()

    noms_humains = PRENOMS[: config["nb_humains"]]
    npcs = {}
    for i, profil in enumerate(config["profils_npc"]):
        nom = PRENOMS_NPC[i % len(PRENOMS_NPC)]
        npcs[nom] = creer_npc(nom, profil, credits_veto=2, profils=profils_dispo)
    noms = noms_humains + list(npcs.keys())

    if len(noms) < 2:
        nom = PRENOMS_NPC[len(npcs) % len(PRENOMS_NPC)]
        defaut = list(profils_dispo.keys())[0]
        npcs[nom] = creer_npc(nom, defaut, credits_veto=2, profils=profils_dispo)
        noms = noms_humains + list(npcs.keys())

    etat = demarrer(
        catalogue,
        noms,
        mode_vote=config["mode_vote"],
        critere=CRITERES[config["critere_nom"]],
        veto_actif=config["veto_actif"],
        npcs=npcs,
        critere_degressif=config["critere_degressif"],
        elimination=config["elimination"],
    )
    st.session_state["etat"] = etat
    st.session_state["config_snapshot"] = config["ontologie"]


# -----------------------------------------------------------------------------
# Barre de statut (toujours visible)
# -----------------------------------------------------------------------------
def _afficher_statut(etat) -> None:
    """Resume compact : round, consensus, dernieres metriques."""
    attrs = attrs_leader(etat)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Round", f"{etat.num_round + 1}" if not etat.consensus_atteint else etat.num_round)
    c2.metric("Proposition", f"{attrs['nom']} (s{attrs['semaine']})")
    c3.metric("Activite", attrs["activite"])

    if etat.historique:
        dernier = etat.historique[-1]
        c4.metric("Approbations", f"{dernier['nb_approbations']}/{len(etat.noms)}")
        c5.metric("Entropie votes", f"{dernier['entropie_votes']:.2f}")
    else:
        c4.metric("Approbations", "—")
        c5.metric("Entropie votes", "—")

    if etat.consensus_atteint:
        st.success(
            f"Decision finale : **{attrs['nom']}** + **{attrs['activite']}** "
            f"(semaine {attrs['semaine']}) — {etat.num_round} round(s)."
        )


# -----------------------------------------------------------------------------
# Onglet VOTE
# -----------------------------------------------------------------------------
def _afficher_question(attrs: dict) -> None:
    st.subheader(f"{attrs['nom']} — {attrs['activite']} — semaine {attrs['semaine']}")
    col1, col2 = st.columns(2)
    descriptifs = [
        ("Type", "type"),
        ("Localisation", "localisation"),
        ("Zone", "zone"),
        ("Continent", "continent"),
        ("Milieu", "milieu"),
        ("Animation", "animation"),
    ]
    for libelle, cle in descriptifs:
        if cle in attrs:
            col1.metric(libelle, str(attrs[cle]))
    col1.metric("Sport / activite", attrs["activite"])
    col2.metric("Cout sejour / pers.", f"{attrs['cout']} €")
    col2.metric("Cout activite", f"{attrs['cout_activite']} €")
    col2.metric("Total / pers.", f"{attrs['cout_total']} €")


def _afficher_votes(etat) -> None:
    nom = etat.noms_humains[etat.idx_personne]
    deja_vote = nom in etat.votes_round
    st.markdown(f"**Voter en tant que : {nom}**")
    if deja_vote:
        vote = etat.votes_round[nom]
        if vote == "veto":
            st.info("Vote enregistre : VETO")
        elif etat.mode_vote == "binaire":
            st.info(f"Vote enregistre : {'Approuve' if vote else 'Rejete'}")
        else:
            st.info(f"Vote enregistre : {vote}/10")

    if etat.mode_vote == "binaire":
        col_a, col_r = st.columns(2)
        if col_a.button("Approuver", key=f"app_{nom}_{etat.num_round}"):
            enregistrer_vote(etat, nom, True)
            st.rerun()
        if col_r.button("Rejeter", key=f"rej_{nom}_{etat.num_round}"):
            enregistrer_vote(etat, nom, False)
            st.rerun()
        if etat.veto_actif:
            if st.button("Veto (payant)", key=f"veto_{nom}_{etat.num_round}"):
                enregistrer_vote(etat, nom, "veto")
                st.rerun()
    else:
        score = st.slider(
            "Note (0 = refuse, 10 = parfait)", 0, 10, 5,
            key=f"score_{nom}_{etat.num_round}",
        )
        if st.button("Enregistrer ma note", key=f"save_{nom}_{etat.num_round}"):
            enregistrer_vote(etat, nom, score)
            st.rerun()


def _afficher_navigation(etat) -> None:
    nb = len(etat.noms_humains)
    col_g, col_mid, col_d = st.columns([1, 3, 1])
    with col_g:
        if st.button("◀", key="prev_personne"):
            etat.idx_personne = (etat.idx_personne - 1) % nb
            st.rerun()
    with col_mid:
        st.markdown(
            f"<div style='text-align:center'>"
            f"{etat.noms_humains[etat.idx_personne]} "
            f"({etat.idx_personne + 1}/{nb})</div>",
            unsafe_allow_html=True,
        )
    with col_d:
        if st.button("▶", key="next_personne"):
            etat.idx_personne = (etat.idx_personne + 1) % nb
            st.rerun()
    nb_votes = sum(1 for n in etat.noms_humains if n in etat.votes_round)
    st.caption(
        f"{nb_votes}/{nb} humains ont vote "
        f"({len(etat.npcs)} NPC votent automatiquement)."
    )


def _afficher_votes_du_round(etat, titre: str = "Votes du round") -> None:
    if not etat.votes_round:
        st.caption("Aucun vote enregistre pour ce round.")
        return
    lignes = []
    for nom in etat.noms:
        if nom not in etat.votes_round:
            valeur = "—"
        else:
            v = etat.votes_round[nom]
            if v == "veto":
                valeur = "VETO"
            elif etat.mode_vote == "score":
                valeur = f"{v}/10"
            else:
                valeur = "Approuve" if v else "Rejete"
        tag = " (NPC)" if nom in etat.npcs else ""
        lignes.append(f"- **{nom}**{tag} : {valeur}")
    with st.expander(titre, expanded=True):
        st.markdown("\n".join(lignes))


def _onglet_vote(etat) -> None:
    if etat.consensus_atteint:
        _afficher_votes_du_round(etat, "Derniers votes")
        return

    st.markdown(
        f"**Round {etat.num_round + 1}** — lisez la proposition, "
        "puis votez (les NPC ont deja vote)."
    )
    _afficher_question(attrs_leader(etat))
    st.divider()
    _afficher_votes_du_round(etat)

    if etat.noms_humains:
        _afficher_navigation(etat)
        _afficher_votes(etat)
    else:
        st.info("Aucun humain : lancez l'auto-negociation.")
        if st.button("Jouer automatiquement", type="primary", key="auto_run"):
            jouer_automatiquement(etat)
            st.session_state["etat"] = etat
            st.rerun()

    if etat.noms_humains and tous_ont_vote(etat):
        if st.button("Valider le round", type="primary", key="valider_round"):
            consensus = valider_round(etat)
            st.session_state["etat"] = etat
            if not consensus:
                st.toast("Pas de consensus — nouveau candidat propose.")
            st.rerun()


# -----------------------------------------------------------------------------
# Onglet ENTROPIE
# -----------------------------------------------------------------------------
def _onglet_entropie(etat) -> None:
    historique = etat.historique
    if not historique:
        st.info("Validez au moins un round pour voir la courbe d'entropie.")
        return

    st.markdown(
        "L'**entropie des votes** mesure le desaccord (0 = unanime). "
        "L'**entropie d'exploration** mesure la diversite des options "
        "testees par l'algorithme genetique."
    )
    fig = tracer_entropie(historique)
    st.pyplot(fig)
    plt.close(fig)

    # Tableau numerique sous le graphique.
    df = pd.DataFrame([
        {
            "Round": h["round"],
            "H votes": h["entropie_votes"],
            "H exploration": h["entropie_exploration"],
            "Approbations": h["nb_approbations"],
            "Vetos": ", ".join(h["vetos_du_round"]) or "—",
        }
        for h in historique
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# Onglet CHEMINS (arbre)
# -----------------------------------------------------------------------------
def _onglet_chemins(etat) -> None:
    historique = etat.historique
    if not historique:
        st.info("Validez au moins un round pour voir l'arbre de negociation.")
        return

    st.markdown(
        "Chaque noeud = une option testee. **Bleu** : abandonnee, "
        "**Rouge** : vetotee, **Vert** : consensus final."
    )
    fig = tracer_arbre_negociation(historique)
    st.pyplot(fig)
    plt.close(fig)

    # Chemin lineaire (frise chronologique).
    st.subheader("Frise des chemins explores")
    arbre = construire_arbre(historique)
    for h in historique:
        veto_txt = f" — VETO ({', '.join(h['vetos_du_round'])})" if h["vetos_du_round"] else ""
        statut = "CONSENSUS" if h["consensus"] else ("VETO" if h["vetos_du_round"] else "explore")
        icone = {"CONSENSUS": "✅", "VETO": "🚫"}.get(statut, "🔵")
        st.markdown(
            f"{icone} **Round {h['round']}** — {h['nom']} + {h['activite']} "
            f"(s{h['semaine']}) — {h['nb_approbations']}/{len(etat.noms)} "
            f"approuvent — H={h['entropie_votes']:.2f}{veto_txt}"
        )

    st.caption(f"Noeuds dans l'arbre : {arbre.number_of_nodes()} | "
               f"Branches : {arbre.number_of_edges()}")


# -----------------------------------------------------------------------------
# Onglet HISTORIQUE (tableau complet)
# -----------------------------------------------------------------------------
def _onglet_historique(etat) -> None:
    historique = etat.historique
    if not historique:
        st.info("Aucun round valide pour l'instant.")
        return

    lignes = []
    for h in historique:
        lignes.append({
            "Round": h["round"],
            "Destination": h["nom"],
            "Activite": h["activite"],
            "Semaine": h["semaine"],
            "Approbations": f"{h['nb_approbations']}/{len(etat.noms)}",
            "Fitness": h["fitness"],
            "H votes": round(h["entropie_votes"], 3),
            "H exploration": round(h["entropie_exploration"], 3),
            "Vetos": ", ".join(h["vetos_du_round"]) or "—",
            "Relachement": h["relachement"],
            "Consensus": "Oui" if h["consensus"] else "Non",
        })
    df = pd.DataFrame(lignes)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export CSV (pratique pour analyser dans un notebook).
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Telecharger l'historique (CSV)",
        csv,
        file_name="historique_negociation.csv",
        mime="text/csv",
    )


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
def _barre_laterale() -> dict:
    with st.sidebar:
        st.header("Ontologie")
        ontologie = st.selectbox("Catalogue de vacances", list(ONTOLOGIES.keys()))
        profils_dispo = list(ONTOLOGIES[ontologie]["profils"].keys())

        st.header("Participants")
        nb_humains = st.number_input("Humains (vous)", 0, 6, 1)
        nb_npc = st.number_input("NPC (votants auto)", 0, 6, 2)
        profils_npc = []
        for i in range(int(nb_npc)):
            profil = st.selectbox(
                f"Profil du NPC {i + 1}",
                profils_dispo,
                index=i % len(profils_dispo),
                key=f"profil_npc_{i}",
            )
            profils_npc.append(profil)

        st.header("Regles du vote")
        mode_vote = st.selectbox("Mode de vote", ["binaire", "score"])
        critere_nom = st.selectbox("Critere de consensus", list(CRITERES.keys()))
        veto_actif = st.checkbox("Activer le veto payant", value=False)

        st.header("Forcer la decision")
        critere_degressif = st.checkbox(
            "Critere degressif (unanimite -> majorite)", value=False,
        )
        elimination = st.checkbox(
            "Elimination progressive du menu", value=False,
        )
        lancer = st.button("Nouvelle negociation", type="primary")

    return {
        "ontologie": ontologie,
        "nb_humains": int(nb_humains),
        "profils_npc": profils_npc,
        "mode_vote": mode_vote,
        "critere_nom": critere_nom,
        "veto_actif": veto_actif,
        "critere_degressif": critere_degressif,
        "elimination": elimination,
        "lancer": lancer,
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Negociation de vacances",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("Negociation de vacances")
    st.caption("Simulez un vote de groupe — vote, entropie, chemins explores")

    config = _barre_laterale()
    if config["lancer"] or "etat" not in st.session_state:
        _init_negociation(config)

    etat = st.session_state["etat"]
    _afficher_statut(etat)

    tab_vote, tab_entropie, tab_chemins, tab_hist = st.tabs([
        "Vote",
        "Entropie",
        "Chemins explores",
        "Historique",
    ])

    with tab_vote:
        _onglet_vote(etat)
    with tab_entropie:
        _onglet_entropie(etat)
    with tab_chemins:
        _onglet_chemins(etat)
    with tab_hist:
        _onglet_historique(etat)


if __name__ == "__main__":
    main()
