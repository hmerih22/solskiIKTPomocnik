"""Testi prijave težave (US-05)."""

import pytest

from conftest import (preberi_prijavo, prijavi, stevilo_vrstic, ustvari_opremo, ustvari_prijavo,
                      ustvari_ucilnico, ustvari_uporabnika)


@pytest.fixture
def ucitelj(odjemalec):
    id_u = ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    prijavi(odjemalec, "ucitelj@sola.si")
    return id_u


def _oddaj(odjemalec, **podatki):
    vrednosti = {"naslov": "Projektor ne prižge", "opis": "Lučka utripa rdeče.",
                 "oprema_id": 0, "ucilnica_id": 0}
    vrednosti.update(podatki)
    return odjemalec.post("/prijave/nova", data=vrednosti, follow_redirects=True)


def _edina_prijava():
    from app.db import transakcija
    with transakcija() as k:
        k.execute("SELECT * FROM prijava_tezave")
        return k.fetchone()


def test_prijava_samo_na_ucilnico(odjemalec, ucitelj):
    id_ucilnice = ustvari_ucilnico("12")
    stran = _oddaj(odjemalec, naslov="Ni interneta", ucilnica_id=id_ucilnice).get_data(as_text=True)
    assert "Prijava je oddana" in stran
    p = _edina_prijava()
    assert (p["ucilnica_id"], p["oprema_id"]) == (id_ucilnice, None)
    assert p["status"] == "nova" and p["skrbnik_id"] is None
    assert p["prijavitelj_id"] == ucitelj


def test_prijava_samo_na_opremo(odjemalec, ucitelj):
    id_opreme = ustvari_opremo()
    _oddaj(odjemalec, oprema_id=id_opreme)
    p = _edina_prijava()
    assert (p["oprema_id"], p["ucilnica_id"]) == (id_opreme, None)


def test_prijava_na_opremo_in_ucilnico(odjemalec, ucitelj):
    id_ucilnice = ustvari_ucilnico("12")
    id_opreme = ustvari_opremo(ucilnica_id=id_ucilnice)
    _oddaj(odjemalec, oprema_id=id_opreme, ucilnica_id=id_ucilnice)
    p = _edina_prijava()
    assert (p["oprema_id"], p["ucilnica_id"]) == (id_opreme, id_ucilnice)


def test_prijava_brez_opreme_in_ucilnice_je_zavrnjena(odjemalec, ucitelj):
    stran = _oddaj(odjemalec).get_data(as_text=True)
    assert "Izberi opremo, učilnico ali oboje" in stran
    assert stevilo_vrstic("prijava_tezave") == 0


@pytest.mark.parametrize("polje", ["naslov", "opis"])
def test_prijava_brez_naslova_ali_opisa(odjemalec, ucitelj, polje):
    _oddaj(odjemalec, ucilnica_id=ustvari_ucilnico("12"), **{polje: "   "})
    assert stevilo_vrstic("prijava_tezave") == 0


def test_predizbrana_oprema_s_seznama(odjemalec, ucitelj):
    id_opreme = ustvari_opremo()
    stran = odjemalec.get(f"/prijave/nova?oprema_id={id_opreme}").get_data(as_text=True)
    assert f'<option selected value="{id_opreme}">' in stran


def test_moje_prijave_in_podrobnosti(odjemalec, ucitelj):
    id_p = ustvari_prijavo(ucitelj, ucilnica_id=ustvari_ucilnico("12"), naslov="Ni interneta")
    tuja = ustvari_prijavo(ustvari_uporabnika("drugi@sola.si"), ucilnica_id=ustvari_ucilnico("13"),
                           naslov="Tuja težava")

    seznam = odjemalec.get("/prijave/moje").get_data(as_text=True)
    assert "Ni interneta" in seznam and "Nova" in seznam
    assert "Tuja težava" not in seznam

    stran = odjemalec.get(f"/prijave/{id_p}").get_data(as_text=True)
    assert "Opis težave" in stran and "še ni določen" in stran
    assert tuja


def test_tuja_prijava_ni_dostopna(odjemalec, ucitelj):
    tuja = ustvari_prijavo(ustvari_uporabnika("drugi@sola.si"), ucilnica_id=ustvari_ucilnico("12"))
    assert odjemalec.get(f"/prijave/{tuja}").status_code == 403


def test_skrbnik_vidi_tujo_prijavo(odjemalec):
    id_p = ustvari_prijavo(ustvari_uporabnika("ucitelj@sola.si"), ucilnica_id=ustvari_ucilnico("12"))
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    assert odjemalec.get(f"/prijave/{id_p}").status_code == 200


def test_neobstojeca_prijava(odjemalec, ucitelj):
    assert odjemalec.get("/prijave/9999").status_code == 404


def test_podrobnosti_resene_prijave(odjemalec, ucitelj):
    id_s = ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik", ime="Sara")
    id_p = ustvari_prijavo(ucitelj, ucilnica_id=ustvari_ucilnico("12"))
    from app.db import transakcija
    with transakcija() as k:
        k.execute("UPDATE prijava_tezave SET status = 'resena', skrbnik_id = %s,"
                  " prevzeta_ob = UTC_TIMESTAMP(), resitev = 'Zamenjan kabel',"
                  " resena_ob = UTC_TIMESTAMP() WHERE id = %s", (id_s, id_p))
    stran = odjemalec.get(f"/prijave/{id_p}").get_data(as_text=True)
    assert "Zamenjan kabel" in stran and "Sara" in stran and "Zaključeno" in stran
    assert preberi_prijavo(id_p)["status"] == "resena"
