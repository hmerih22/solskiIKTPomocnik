"""Testi preverjanja razpoložljivosti (US-02)."""

from datetime import timedelta

import pytest

from app.cas import v_lokalni
from app.napake import PoslovnaNapaka
from app.services.rezervacije import preveri_razpolozljivost
from conftest import (jutri_ob, prijavi, stevilo_vrstic, ustvari_opremo, ustvari_rezervacijo,
                      ustvari_uporabnika)


@pytest.fixture
def oprema_z_rezervacijo(app):
    """Projektor z obstoječo rezervacijo jutri 9.00–10.00."""
    id_u = ustvari_uporabnika("ucitelj@sola.si")
    id_o = ustvari_opremo()
    ustvari_rezervacijo(id_u, id_o, jutri_ob(9), jutri_ob(10))
    return id_o


@pytest.mark.parametrize("zacetek, konec, prosta", [
    ((9, 30), (10, 30), False),   # delno prekrivanje
    ((8, 30), (9, 30), False),    # prekrivanje na začetku
    ((9, 0), (10, 0), False),     # enak termin
    ((8, 0), (11, 0), False),     # nova rezervacija obsega obstoječo
    ((10, 0), (11, 0), True),     # začne se natanko ob koncu obstoječe
    ((8, 0), (9, 0), True),       # konča se natanko ob začetku obstoječe
])
def test_prekrivanje_terminov(oprema_z_rezervacijo, zacetek, konec, prosta):
    rezultat = preveri_razpolozljivost(oprema_z_rezervacijo, jutri_ob(*zacetek), jutri_ob(*konec))
    assert rezultat["prosta"] is prosta


def test_preklicana_rezervacija_ne_zaseda_termina(app):
    id_u = ustvari_uporabnika("ucitelj@sola.si")
    id_o = ustvari_opremo()
    ustvari_rezervacijo(id_u, id_o, jutri_ob(9), jutri_ob(10), preklicana=True)
    assert preveri_razpolozljivost(id_o, jutri_ob(9), jutri_ob(10))["prosta"]


def test_rezervacija_druge_opreme_ne_vpliva(app):
    id_u = ustvari_uporabnika("ucitelj@sola.si")
    ustvari_rezervacijo(id_u, ustvari_opremo("INV-1"), jutri_ob(9), jutri_ob(10))
    assert preveri_razpolozljivost(ustvari_opremo("INV-2"), jutri_ob(9), jutri_ob(10))["prosta"]


def test_nedelujoca_oprema(app):
    id_o = ustvari_opremo(stanje="nedelujoca")
    rezultat = preveri_razpolozljivost(id_o, jutri_ob(9), jutri_ob(10))
    assert not rezultat["prosta"]
    assert "nedelujoča" in rezultat["razlog"]


def test_neveljaven_termin(app):
    id_o = ustvari_opremo()
    with pytest.raises(PoslovnaNapaka, match="pred koncem"):
        preveri_razpolozljivost(id_o, jutri_ob(10), jutri_ob(9))
    vceraj = jutri_ob(9) - timedelta(days=2)
    with pytest.raises(PoslovnaNapaka, match="v prihodnosti"):
        preveri_razpolozljivost(id_o, vceraj, vceraj + timedelta(hours=1))


# --- Preko spletne strani ------------------------------------------------------

def _lokalno(utc):
    """Vrednost za polje datetime-local (lokalni čas Ljubljane)."""
    return v_lokalni(utc).strftime("%Y-%m-%dT%H:%M")


def test_stran_prikaze_zaseden_termin_in_ne_ustvari_rezervacije(odjemalec, oprema_z_rezervacijo):
    prijavi(odjemalec, "ucitelj@sola.si")
    url = f"/rezervacije/nova/{oprema_z_rezervacijo}"

    stran = odjemalec.post(url, data={"zacetek": _lokalno(jutri_ob(9, 30)),
                                      "konec": _lokalno(jutri_ob(10, 30))}).get_data(as_text=True)
    assert "že rezervirana" in stran

    stran = odjemalec.post(url, data={"zacetek": _lokalno(jutri_ob(10)),
                                      "konec": _lokalno(jutri_ob(11))}).get_data(as_text=True)
    assert "je v izbranem terminu prosta" in stran
    assert stevilo_vrstic("rezervacija") == 1


def test_stran_prikaze_napako_neveljavnega_termina(odjemalec, oprema_z_rezervacijo):
    prijavi(odjemalec, "ucitelj@sola.si")
    stran = odjemalec.post(f"/rezervacije/nova/{oprema_z_rezervacijo}", data={
        "zacetek": _lokalno(jutri_ob(11)), "konec": _lokalno(jutri_ob(10))}).get_data(as_text=True)
    assert "Začetek mora biti pred koncem" in stran


def test_stran_prikaze_zasedene_termine_v_lokalnem_casu(odjemalec, oprema_z_rezervacijo):
    prijavi(odjemalec, "ucitelj@sola.si")
    stran = odjemalec.get(f"/rezervacije/nova/{oprema_z_rezervacijo}").get_data(as_text=True)
    assert v_lokalni(jutri_ob(9)).strftime("%H:%M") in stran


def test_neobstojeca_oprema(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/rezervacije/nova/9999").status_code == 404
