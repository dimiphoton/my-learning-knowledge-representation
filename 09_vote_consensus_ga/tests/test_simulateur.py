"""Tests unitaires — simulateur.py (catalogue, candidats, satisfaction)."""
from __future__ import annotations

import pytest

from simulateur import (
    PROFILS_NPC,
    PROFILS_NPC_V2,
    Personne,
    activite_valide_pour_semaine,
    attributs_candidat,
    creer_npc,
    est_candidat_valide,
    generer_personnes,
    satisfaction,
    seuil_acceptation,
)


def test_charger_catalogue_non_vide(catalogue_v1):
    assert len(catalogue_v1) >= 10


def test_charger_catalogue_v2_non_vide(catalogue_v2):
    assert len(catalogue_v2) >= 8
    ex = next(iter(catalogue_v2.values()))
    assert "zone" in ex and "milieu" in ex


def test_lister_candidats_v1(candidats_v1):
    assert len(candidats_v1) > 0
    assert all(len(c) == 3 for c in candidats_v1)


def test_lister_candidats_v2(catalogue_v2):
    from simulateur import lister_candidats

    candidats = lister_candidats(catalogue_v2)
    assert len(candidats) > 0
    # Ski ne doit pas être proposé en plein été (semaine 30).
    for dest, act, sem in candidats:
        if act == "ski" and sem >= 26:
            pytest.fail(f"Ski en été interdit : {(dest, act, sem)}")


def test_est_candidat_valide_ok(catalogue_v1, candidats_v1):
    assert est_candidat_valide(catalogue_v1, candidats_v1[0])


def test_est_candidat_valide_ko_dest(catalogue_v1, candidats_v1):
    dest, act, sem = candidats_v1[0]
    assert not est_candidat_valide(catalogue_v1, ("inexistant", act, sem))


def test_activite_valide_pour_semaine_ete():
    act = {"saison": "Ete"}
    assert activite_valide_pour_semaine(act, 30) is True
    assert activite_valide_pour_semaine(act, 5) is False


def test_activite_valide_pour_semaine_toute_annee():
    act = {"saison": "Toute l'annee"}
    assert activite_valide_pour_semaine(act, 5) is True
    assert activite_valide_pour_semaine(act, 30) is True


def test_satisfaction_match_parfait(catalogue_v1, candidats_v1, personne_exemple):
    # On cherche un candidat Nice + Plongée si possible.
    candidat = next(
        (c for c in candidats_v1 if c[0] == "nice" and c[1] == "plongee"),
        candidats_v1[0],
    )
    attrs = attributs_candidat(catalogue_v1, candidat)
    score = satisfaction(personne_exemple, attrs)
    assert 0.0 <= score <= 1.0
    if attrs["type"] == "Plage" and attrs["activite"] == "Plongee":
        assert score >= 0.7


def test_satisfaction_budget_depasse(personne_exemple):
    attrs_ok = {
        "cout_total": personne_exemple.budget_max,
        "type": personne_exemple.type_prefere,
        "localisation": personne_exemple.localisation_preferee,
        "activite": personne_exemple.activite_preferee,
        "semaine": 30,
        "animation": personne_exemple.animation_preferee,
    }
    attrs_cher = {**attrs_ok, "cout_total": personne_exemple.budget_max * 5}
    score_ok = satisfaction(personne_exemple, attrs_ok)
    score_cher = satisfaction(personne_exemple, attrs_cher)
    assert score_cher < score_ok


def test_attributs_candidat_cles(catalogue_v1, candidats_v1):
    attrs = attributs_candidat(catalogue_v1, candidats_v1[0])
    for cle in ("nom", "cout_total", "semaine", "activite", "cout"):
        assert cle in attrs


def test_generer_personnes_taille(catalogue_v1):
    personnes = generer_personnes(5, catalogue_v1, graine=42)
    assert len(personnes) == 5
    noms = [p.nom for p in personnes]
    assert len(set(noms)) == len(noms)


def test_seuil_acceptation_marge(personne_exemple):
    conciliante = Personne(
        **{**personne_exemple.__dict__, "marge": 0.8}
    )
    rigide = Personne(
        **{**personne_exemple.__dict__, "marge": 0.1}
    )
    assert seuil_acceptation(conciliante) < seuil_acceptation(rigide)


def test_creer_npc_profil_inconnu():
    with pytest.raises(ValueError, match="Profil inconnu"):
        creer_npc("X", "Profil qui n existe pas")


def test_creer_npc_v2():
    nom_profil = next(iter(PROFILS_NPC_V2))
    npc = creer_npc("Nina", nom_profil, profils=PROFILS_NPC_V2)
    assert npc.zone_preferee != "" or npc.milieu_prefere != ""


def test_creer_npc_v1():
    nom_profil = next(iter(PROFILS_NPC))
    npc = creer_npc("Nina", nom_profil)
    assert npc.type_prefere != ""
