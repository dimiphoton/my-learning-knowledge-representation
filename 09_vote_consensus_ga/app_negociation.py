"""Interface Streamlit : simuler soi-meme une negociation a plusieurs.

Lancement :
    streamlit run 09_vote_consensus_ga/app_negociation.py

Colonne gauche  : lire la question, voter, changer de personne (fleches).
Colonne droite  : arbre de negociation + courbe d'entropie.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

from negociation_manuelle import (
    attrs_leader,
    demarrer,
    enregistrer_vote,
    tous_ont_vote,
    valider_round,
)
from simulateur import charger_catalogue
from strategies import (
    critere_majorite,
    critere_plancher,
    critere_score_moyen,
    critere_supermajorite,
    critere_unanimite,
)
from visualisation import tracer_arbre_negociation, tracer_entropie

PRENOMS = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Gina", "Hugo"]

CRITERES = {
    "Unanimite (tous approuvent)": critere_unanimite(),
    "Supermajorite (75 %)": critere_supermajorite(0.75),
    "Majorite simple (> 50 %)": critere_majorite(),
    "Plancher (personne < 40 %)": critere_plancher(0.4),
    "Score moyen >= 6/10": critere_score_moyen(0.6),
}


def _init_negociation(
    nb: int,
    mode_vote: str,
    critere_nom: str,
    veto_actif: bool,
) -> None:
    """Cree ou reinitialise l'etat dans session_state."""
    noms = PRENOMS[:nb]
    catalogue = charger_catalogue()
    etat = demarrer(
        catalogue,
        noms,
        mode_vote=mode_vote,
        critere=CRITERES[critere_nom],
        veto_actif=veto_actif,
    )
    st.session_state["etat"] = etat


def _afficher_question(attrs: dict) -> None:
    """Affiche la carte du candidat propose (la 'question')."""
    st.subheader(f"{attrs['nom']} — semaine {attrs['semaine']}")
    col1, col2 = st.columns(2)
    col1.metric("Type", attrs["type"])
    col1.metric("Localisation", attrs["localisation"])
    col2.metric("Cout / pers.", f"{attrs['cout']} €")
    col2.metric("Animation", f"{attrs['animation']}/10")


def _afficher_votes(etat) -> None:
    """Panneau de vote pour la personne courante."""
    nom = etat.noms[etat.idx_personne]
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
        score = st.slider("Note (0 = refuse, 10 = parfait)", 0, 10, 5,
                          key=f"score_{nom}_{etat.num_round}")
        if st.button("Enregistrer ma note",
                     key=f"save_{nom}_{etat.num_round}"):
            enregistrer_vote(etat, nom, score)
            st.rerun()


def _afficher_navigation(etat) -> None:
    """Fleches gauche/droite pour changer de personne."""
    nb = len(etat.noms)
    col_g, col_mid, col_d = st.columns([1, 3, 1])
    with col_g:
        if st.button("◀", key="prev_personne"):
            etat.idx_personne = (etat.idx_personne - 1) % nb
            st.rerun()
    with col_mid:
        st.markdown(
            f"<div style='text-align:center'>"
            f"{etat.noms[etat.idx_personne]} "
            f"({etat.idx_personne + 1}/{nb})</div>",
            unsafe_allow_html=True,
        )
    with col_d:
        if st.button("▶", key="next_personne"):
            etat.idx_personne = (etat.idx_personne + 1) % nb
            st.rerun()

    nb_votes = len(etat.votes_round)
    st.caption(f"{nb_votes}/{nb} personnes ont vote pour ce round.")


def _afficher_visualisations(historique: list[dict]) -> None:
    """Arbre + entropie dans la colonne droite."""
    if not historique:
        st.info("Les graphiques apparaitront apres le premier round valide.")
        return

    fig_arbre = tracer_arbre_negociation(historique)
    st.pyplot(fig_arbre)
    plt.close(fig_arbre)

    fig_ent = tracer_entropie(historique)
    st.pyplot(fig_ent)
    plt.close(fig_ent)


def main() -> None:
    st.set_page_config(
        page_title="Negociation manuelle",
        layout="wide",
    )
    st.title("Negociation de vacances — mode manuel")

    # --- Barre laterale : configuration ---
    with st.sidebar:
        st.header("Configuration")
        nb = st.number_input("Nombre de personnes", 2, 8, 3)
        mode_vote = st.selectbox("Mode de vote", ["binaire", "score"])
        critere_nom = st.selectbox("Critere de consensus",
                                   list(CRITERES.keys()))
        veto_actif = st.checkbox("Activer le veto payant", value=False)

        if st.button("Nouvelle negociation", type="primary"):
            _init_negociation(nb, mode_vote, critere_nom, veto_actif)

    # Initialisation au premier chargement.
    if "etat" not in st.session_state:
        _init_negociation(nb, mode_vote, critere_nom, veto_actif)

    etat = st.session_state["etat"]

    # --- Layout principal : vote a gauche, visualisation a droite ---
    col_vote, col_visu = st.columns([1, 1])

    with col_vote:
        st.header("Panneau de vote")

        if etat.consensus_atteint:
            attrs = attrs_leader(etat)
            st.success(
                f"Consensus atteint : **{attrs['nom']}** "
                f"(semaine {attrs['semaine']})"
            )
        else:
            attrs = attrs_leader(etat)
            st.markdown(f"**Round {etat.num_round + 1}** — "
                        "Lisez la proposition ci-dessous, puis votez "
                        "pour chaque personne.")
            _afficher_question(attrs)
            st.divider()
            _afficher_navigation(etat)
            _afficher_votes(etat)

            if tous_ont_vote(etat):
                if st.button("Valider le round", type="primary"):
                    consensus = valider_round(etat)
                    st.session_state["etat"] = etat
                    if consensus:
                        st.rerun()
                    else:
                        st.toast(
                            "Pas de consensus — nouveau candidat propose."
                        )
                        st.rerun()

    with col_visu:
        st.header("Parcours et entropie")
        _afficher_visualisations(etat.historique)


if __name__ == "__main__":
    main()
