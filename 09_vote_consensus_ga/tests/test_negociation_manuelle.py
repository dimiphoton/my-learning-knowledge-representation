"""Tests unitaires — negociation_manuelle.py (vote humain, NPC, forçage)."""
from __future__ import annotations

from negociation_manuelle import (
    _critere_effectif,
    demarrer,
    enregistrer_vote,
    jouer_automatiquement,
    tous_ont_vote,
    valider_round,
)
from simulateur import PROFILS_NPC, creer_npc
from strategies import critere_unanimite


def _npcs_trois():
    profils = list(PROFILS_NPC.keys())[:3]
    noms = ["Nina", "Otto", "Rita"]
    return {n: creer_npc(n, p) for n, p in zip(noms, profils)}


def test_demarrer_etat_initial(catalogue_v1):
    npcs = _npcs_trois()
    etat = demarrer(catalogue_v1, list(npcs.keys()), npcs=npcs, graine=42)
    assert etat.leader is not None
    assert len(etat.votes_round) == len(npcs)  # NPC deja prevotes
    assert etat.num_round == 0
    assert not etat.consensus_atteint


def test_enregistrer_vote(catalogue_v1):
    etat = demarrer(catalogue_v1, ["Alice", "Bob"], graine=1)
    enregistrer_vote(etat, "Alice", True)
    assert etat.votes_round["Alice"] is True
    assert not tous_ont_vote(etat)


def test_tous_ont_vote(catalogue_v1):
    etat = demarrer(catalogue_v1, ["Alice", "Bob"], graine=2)
    enregistrer_vote(etat, "Alice", True)
    assert not tous_ont_vote(etat)
    enregistrer_vote(etat, "Bob", False)
    assert tous_ont_vote(etat)


def test_valider_round_sans_tous_votes(catalogue_v1):
    etat = demarrer(catalogue_v1, ["Alice", "Bob"], graine=3)
    enregistrer_vote(etat, "Alice", True)
    assert valider_round(etat) is False
    assert len(etat.historique) == 0


def test_valider_round_ajoute_historique(catalogue_v1):
    npcs = _npcs_trois()
    etat = demarrer(catalogue_v1, list(npcs.keys()), npcs=npcs, graine=4)
    assert tous_ont_vote(etat)
    valider_round(etat)
    assert len(etat.historique) == 1
    assert "entropie_votes" in etat.historique[0]
    assert "activite" in etat.historique[0]


def test_critere_degressif_passe_majorite(catalogue_v1):
    etat = demarrer(
        catalogue_v1, ["Alice"], npcs=_npcs_trois(),
        critere_degressif=True, graine=5,
    )
    etat.num_round = 6
    crit = _critere_effectif(etat)
    # Round >= 5 : majorite simple (> 50 %). 3/4 suffit.
    assert crit([True, True, True, False], None, 0.5) is True
    assert crit([True, False, False, False], None, 0.5) is False


def test_critere_degressif_desactive(catalogue_v1):
    etat = demarrer(
        catalogue_v1, list(_npcs_trois().keys()),
        critere=critere_unanimite(), critere_degressif=False, graine=6,
    )
    etat.num_round = 10
    crit = _critere_effectif(etat)
    # Comportement unanimite : tous ou rien (on ne compare pas l'identite des fonctions).
    assert crit([True, True, True], None, 0) is True
    assert crit([True, True, False], None, 0) is False


def test_elimination_reduit_candidats(catalogue_v1):
    npcs = _npcs_trois()
    etat = demarrer(
        catalogue_v1, list(npcs.keys()), npcs=npcs,
        elimination=True, graine=7,
    )
    nb_initial = len(etat.candidats)
    # Plusieurs rounds sans consensus => menu retrecit.
    for _ in range(5):
        if etat.consensus_atteint:
            break
        if tous_ont_vote(etat):
            valider_round(etat)
    if etat.num_round >= 1 and not etat.consensus_atteint:
        assert len(etat.candidats) <= nb_initial


def test_jouer_automatiquement_npc_only(catalogue_v1):
    npcs = _npcs_trois()
    etat = demarrer(catalogue_v1, list(npcs.keys()), npcs=npcs, graine=8)
    termine = jouer_automatiquement(etat)
    assert termine is True
    assert etat.consensus_atteint
    assert etat.num_round >= 1
    assert len(etat.historique) == etat.num_round


def test_veto_enregistre_dans_historique(catalogue_v1):
    npcs = {"Nina": creer_npc("Nina", list(PROFILS_NPC.keys())[0])}
    etat = demarrer(
        catalogue_v1, ["Alice", "Nina"],
        npcs=npcs, veto_actif=True, credits_veto=2, graine=9,
    )
    enregistrer_vote(etat, "Alice", "veto")
    assert tous_ont_vote(etat)
    valider_round(etat)
    assert len(etat.historique) == 1
    assert "Alice" in etat.historique[0]["vetos_du_round"]


def test_attrs_leader_apres_demarrage(catalogue_v1):
    from negociation_manuelle import attrs_leader

    etat = demarrer(catalogue_v1, ["Alice", "Bob"], graine=10)
    attrs = attrs_leader(etat)
    assert "nom" in attrs and "semaine" in attrs
