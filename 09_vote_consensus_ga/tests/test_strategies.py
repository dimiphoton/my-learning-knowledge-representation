"""Tests unitaires — strategies.py (bien-être, critères, exhaustif)."""
from __future__ import annotations

import numpy as np
import pytest

from strategies import (
    bien_etre_leximin,
    bien_etre_min,
    bien_etre_mixte,
    bien_etre_moyenne,
    bien_etre_nash,
    critere_majorite,
    critere_plancher,
    critere_supermajorite,
    critere_unanimite,
    meilleur_exhaustif,
)


def test_bien_etre_moyenne():
    sats = np.array([0.8, 0.6])
    assert bien_etre_moyenne(sats) == pytest.approx(0.7)


def test_bien_etre_min():
    sats = np.array([0.8, 0.6])
    assert bien_etre_min(sats) == pytest.approx(0.6)


def test_bien_etre_mixte():
    sats = np.array([0.8, 0.6])
    assert bien_etre_mixte(sats) == pytest.approx(0.65)


def test_bien_etre_nash_positif():
    sats = np.array([0.8, 0.6, 0.4])
    assert bien_etre_nash(sats) > 0


def test_bien_etre_leximin():
    sats = np.array([0.9, 0.3, 0.7])
    assert 0 < bien_etre_leximin(sats) < 1


def test_critere_unanimite_ok():
    crit = critere_unanimite()
    assert crit([True, True], np.array([0.8, 0.9]), 0.0) is True


def test_critere_unanimite_ko():
    crit = critere_unanimite()
    assert crit([True, False], np.array([0.8, 0.3]), 0.5) is False


def test_critere_supermajorite_75():
    crit = critere_supermajorite(0.75)
    assert crit([True, True, True, False], np.zeros(4), 0.5) is True
    assert crit([True, True, False, False], np.zeros(4), 0.5) is False


def test_critere_majorite():
    crit = critere_majorite()
    assert crit([True, True, False], np.zeros(3), 0.5) is True


def test_critere_plancher():
    crit = critere_plancher(0.4)
    assert crit([True, True], np.array([0.8, 0.5]), 0.0) is True
    assert crit([True, True], np.array([0.8, 0.2]), 0.0) is False


def test_meilleur_exhaustif_coherent(catalogue_v1):
    from simulateur import generer_personnes

    personnes = generer_personnes(3, catalogue_v1, graine=1)
    res = meilleur_exhaustif(catalogue_v1, personnes)
    assert "candidat" in res
    assert "valeur" in res
    assert 0 <= res["valeur"] <= 1
