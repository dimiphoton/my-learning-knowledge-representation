"""Fixtures partagées pour les tests du projet vote de consensus.

Les modules du projet (simulateur, consensus_ga…) s'importent sans préfixe
package : on ajoute le dossier parent au path Python.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

# Backend sans fenêtre (obligatoire en CI / terminal).
matplotlib.use("Agg")

DOSSIER_PROJET = Path(__file__).resolve().parent.parent
if str(DOSSIER_PROJET) not in sys.path:
    sys.path.insert(0, str(DOSSIER_PROJET))

import pytest  # noqa: E402

from simulateur import (  # noqa: E402
    Personne,
    charger_catalogue,
    charger_catalogue_v2,
    lister_candidats,
)


@pytest.fixture(scope="session")
def catalogue_v1():
    return charger_catalogue()


@pytest.fixture(scope="session")
def catalogue_v2():
    return charger_catalogue_v2()


@pytest.fixture(scope="session")
def candidats_v1(catalogue_v1):
    return lister_candidats(catalogue_v1)


@pytest.fixture
def personne_exemple() -> Personne:
    """Votante alignée sur Nice + Plongée (ontologie simple)."""
    return Personne(
        nom="TestAlice",
        type_prefere="Plage",
        localisation_preferee="France",
        activite_preferee="Plongee",
        semaines_dispo={28, 29, 30, 31},
        budget_max=800,
        animation_preferee=7,
        poids={
            "type": 0.2,
            "localisation": 0.15,
            "semaine": 0.15,
            "budget": 0.2,
            "animation": 0.15,
            "activite": 0.15,
        },
        marge=0.3,
        credits_veto=2,
    )
