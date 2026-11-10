"""Testi nedelujoče opreme (US-07)."""

import pytest

from app.cas import v_lokalni
from app.db import transakcija
from conftest import (jutri_ob, prijavi, stevilo_vrstic, ustvari_opremo, ustvari_prijavo,
                      ustvari_rezervacijo, ustvari_uporabnika)


def _stanje(id_opreme):
    with transakcija() as k:
        k.execute("SELECT stanje FROM oprema WHERE id = %s", (id_opreme,))
        return k.fetchone()["stanje"]


def _oznaci(odjemalec, id_opreme, stanje, **dodatno):
    return odjemalec.post(f"/oprema/{id_opreme}/stanje", data={"stanje": stanje, **dodatno},
                          follow_redirects=True)


def _lokalno(utc):
    return v_lokalni(utc).strftime("%Y-%m-%dT%H:%M")


@pytest.fixture
def oprema(app):
    return ustvari_opremo()


def test_skrbnik_oznaci_opremo(odjemalec, oprema):
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    stran = _oznaci(odjemalec, oprema, "nedelujoca").get_data(as_text=True)
    assert "označena kot nedelujoča" in stran
    assert _stanje(oprema) == "nedelujoca"

    _oznaci(odjemalec, oprema, "uporabna")
    assert _stanje(oprema) == "uporabna"


@pytest.mark.parametrize("stanje", ["pokvarjena", ""])
def test_neveljavno_stanje(odjemalec, oprema, stanje):
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    _oznaci(odjemalec, oprema, stanje)
    assert _stanje(oprema) == "uporabna"


def test_ucitelj_ne_more_oznaciti(odjemalec, oprema):
    ustvari_uporabnika("ucitelj@sola.si")
    prijavi(odjemalec, "ucitelj@sola.si")
    odgovor = odjemalec.post(f"/oprema/{oprema}/stanje", data={"stanje": "nedelujoca"})
    assert odgovor.status_code == 403
    assert _stanje(oprema) == "uporabna"


def test_rezervacija_z_obrazcem_odprtim_pred_spremembo_je_zavrnjena(odjemalec, oprema):
    """Učitelj odpre obrazec, ko je oprema še uporabna, skrbnik jo vmes označi
    kot nedelujočo, učitelj nato odda obrazec – rezervacija je zavrnjena."""
    ustvari_uporabnika("ucitelj@sola.si")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert "Potrdi rezervacijo" in odjemalec.get(f"/rezervacije/nova/{oprema}").get_data(as_text=True)

    with transakcija() as k:
        k.execute("UPDATE oprema SET stanje = 'nedelujoca' WHERE id = %s", (oprema,))

    stran = odjemalec.post(f"/rezervacije/nova/{oprema}", data={
        "zacetek": _lokalno(jutri_ob(9)), "konec": _lokalno(jutri_ob(10)), "potrdi": "1",
    }, follow_redirects=True).get_data(as_text=True)
    assert "nedelujoča" in stran
    assert stevilo_vrstic("rezervacija") == 0


def test_obstojece_rezervacije_ostanejo_z_opozorilom(odjemalec, oprema):
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si")
    id_r = ustvari_rezervacijo(id_ucitelja, oprema, jutri_ob(9), jutri_ob(10))
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")

    stran = _oznaci(odjemalec, oprema, "nedelujoca").get_data(as_text=True)
    assert "prihodnje rezervacije (1)" in stran
    with transakcija() as k:
        k.execute("SELECT status FROM rezervacija WHERE id = %s", (id_r,))
        assert k.fetchone()["status"] == "aktivna"
    assert "⚠ Oprema je nedelujoča" in odjemalec.get("/rezervacije/vse").get_data(as_text=True)

    odjemalec.post("/odjava")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert "⚠ Oprema je označena kot nedelujoča" in odjemalec.get(
        "/rezervacije/moje").get_data(as_text=True)


def test_opozorilo_izgine_po_ponovni_oznacitvi(odjemalec, oprema):
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si")
    ustvari_rezervacijo(id_ucitelja, oprema, jutri_ob(9), jutri_ob(10))
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")

    _oznaci(odjemalec, oprema, "nedelujoca")
    assert "⚠" in odjemalec.get("/rezervacije/vse").get_data(as_text=True)
    _oznaci(odjemalec, oprema, "uporabna")
    assert "⚠" not in odjemalec.get("/rezervacije/vse").get_data(as_text=True)


def test_zakljucek_prijave_ne_spremeni_stanja_opreme(odjemalec, oprema):
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si")
    id_p = ustvari_prijavo(id_ucitelja, oprema_id=oprema)
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")

    _oznaci(odjemalec, oprema, "nedelujoca", naprej=f"/prijave/{id_p}")
    odjemalec.post(f"/prijave/{id_p}/prevzem")
    odjemalec.post(f"/prijave/{id_p}/zakljucek", data={"resitev": "Naročen nov projektor"})
    assert _stanje(oprema) == "nedelujoca"


def test_oznacitev_s_prijave_vrne_na_prijavo(odjemalec, oprema):
    id_p = ustvari_prijavo(ustvari_uporabnika("ucitelj@sola.si"), oprema_id=oprema)
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    odgovor = odjemalec.post(f"/oprema/{oprema}/stanje",
                             data={"stanje": "nedelujoca", "naprej": f"/prijave/{id_p}"})
    assert odgovor.headers["Location"].endswith(f"/prijave/{id_p}")
