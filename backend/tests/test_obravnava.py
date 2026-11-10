"""Testi obravnave prijav (US-06)."""

import threading

import pytest

from app.auth import Uporabnik
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import uporabniki as repo_uporabniki
from app.services import prijave as storitev
from conftest import (preberi_prijavo, prijavi, ustvari_prijavo, ustvari_ucilnico,
                      ustvari_uporabnika)


def _uporabnik(id_u):
    with transakcija() as k:
        return Uporabnik(repo_uporabniki.najdi(k, id_u))


@pytest.fixture
def podatki(app):
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    return {
        "ucitelj": id_ucitelja,
        "skrbnik": ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik", ime="Sara"),
        "skrbnik2": ustvari_uporabnika("skrbnik2@sola.si", "ikt_skrbnik", ime="Tim"),
        "admin": ustvari_uporabnika("admin@sola.si", "administrator"),
        "prijava": ustvari_prijavo(id_ucitelja, ucilnica_id=ustvari_ucilnico("12")),
    }


# --- Seznam in prevzem ------------------------------------------------------------

def test_vse_prijave_vidi_samo_skrbnik(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/prijave/vse").status_code == 403
    odjemalec.post("/odjava")
    prijavi(odjemalec, "skrbnik@sola.si")
    stran = odjemalec.get("/prijave/vse").get_data(as_text=True)
    assert "Ne dela" in stran
    assert "Ne dela" not in odjemalec.get("/prijave/vse?status=resena").get_data(as_text=True)


def test_prevzem(odjemalec, podatki):
    prijavi(odjemalec, "skrbnik@sola.si")
    stran = odjemalec.post(f"/prijave/{podatki['prijava']}/prevzem",
                           follow_redirects=True).get_data(as_text=True)
    assert "Prijavo si prevzel" in stran
    p = preberi_prijavo(podatki["prijava"])
    assert p["status"] == "v_obravnavi"
    assert p["skrbnik_id"] == podatki["skrbnik"]
    assert p["prevzeta_ob"] is not None


def test_ze_prevzete_prijave_ni_mogoce_prevzeti(odjemalec, podatki):
    storitev.prevzemi(_uporabnik(podatki["skrbnik"]), podatki["prijava"])
    prijavi(odjemalec, "skrbnik2@sola.si")
    stran = odjemalec.post(f"/prijave/{podatki['prijava']}/prevzem",
                           follow_redirects=True).get_data(as_text=True)
    assert "že prevzel drug skrbnik" in stran
    assert preberi_prijavo(podatki["prijava"])["skrbnik_id"] == podatki["skrbnik"]


def test_socasni_prevzem_uspe_samo_enemu(app, podatki):
    """Dva skrbnika hkrati prevzameta isto prijavo: pogojna posodobitev
    (WHERE status = 'nova') dovoli samo enega."""
    skrbnika = [_uporabnik(podatki["skrbnik"]), _uporabnik(podatki["skrbnik2"])]
    start = threading.Barrier(2)
    rezultati = []

    def prevzemi(skrbnik):
        with app.app_context():
            start.wait(timeout=10)
            try:
                storitev.prevzemi(skrbnik, podatki["prijava"])
                rezultati.append(skrbnik.id)
            except PoslovnaNapaka:
                rezultati.append("zavrnjen")

    niti = [threading.Thread(target=prevzemi, args=(s,)) for s in skrbnika]
    for nit in niti:
        nit.start()
    for nit in niti:
        nit.join(timeout=30)

    uspesni = [r for r in rezultati if r != "zavrnjen"]
    assert len(uspesni) == 1 and rezultati.count("zavrnjen") == 1
    assert preberi_prijavo(podatki["prijava"])["skrbnik_id"] == uspesni[0]


# --- Zaključek ----------------------------------------------------------------------

def _prevzeta(podatki):
    storitev.prevzemi(_uporabnik(podatki["skrbnik"]), podatki["prijava"])


def test_zakljucek_z_resitvijo(odjemalec, podatki):
    _prevzeta(podatki)
    prijavi(odjemalec, "skrbnik@sola.si")
    odjemalec.post(f"/prijave/{podatki['prijava']}/zakljucek", data={"resitev": "Zamenjan kabel"})
    p = preberi_prijavo(podatki["prijava"])
    assert p["status"] == "resena"
    assert p["resitev"] == "Zamenjan kabel"
    assert p["resena_ob"] is not None


def test_zakljucek_brez_resitve_je_zavrnjen(odjemalec, podatki):
    _prevzeta(podatki)
    prijavi(odjemalec, "skrbnik@sola.si")
    stran = odjemalec.post(f"/prijave/{podatki['prijava']}/zakljucek", data={"resitev": "   "},
                           follow_redirects=True).get_data(as_text=True)
    assert "vnesi opis rešitve" in stran
    assert preberi_prijavo(podatki["prijava"])["status"] == "v_obravnavi"


def test_drug_skrbnik_ne_more_zakljuciti(odjemalec, podatki):
    _prevzeta(podatki)
    prijavi(odjemalec, "skrbnik2@sola.si")
    odgovor = odjemalec.post(f"/prijave/{podatki['prijava']}/zakljucek", data={"resitev": "X"})
    assert odgovor.status_code == 403
    assert preberi_prijavo(podatki["prijava"])["status"] == "v_obravnavi"


def test_nove_prijave_ni_mogoce_zakljuciti(podatki):
    with pytest.raises(PoslovnaNapaka, match="samo prijavo v obravnavi"):
        storitev.zakljuci(_uporabnik(podatki["admin"]), podatki["prijava"], "Rešeno")


def test_administrator_lahko_zakljuci(podatki):
    _prevzeta(podatki)
    storitev.zakljuci(_uporabnik(podatki["admin"]), podatki["prijava"], "Rešil administrator")
    assert preberi_prijavo(podatki["prijava"])["status"] == "resena"


# --- Prerazporeditev ------------------------------------------------------------------

def test_prerazporeditev_ohrani_cas_prevzema(odjemalec, podatki):
    _prevzeta(podatki)
    prevzeta_ob = preberi_prijavo(podatki["prijava"])["prevzeta_ob"]
    prijavi(odjemalec, "admin@sola.si")
    odjemalec.post(f"/prijave/{podatki['prijava']}/prerazporeditev",
                   data={"skrbnik_id": podatki["skrbnik2"]})
    p = preberi_prijavo(podatki["prijava"])
    assert p["skrbnik_id"] == podatki["skrbnik2"]
    assert p["prevzeta_ob"] == prevzeta_ob


@pytest.mark.parametrize("kdo", ["ucitelj", "neaktiven"])
def test_prerazporeditev_le_aktivnemu_skrbniku(podatki, kdo):
    _prevzeta(podatki)
    if kdo == "neaktiven":
        with transakcija() as k:
            k.execute("UPDATE uporabnik SET aktiven = FALSE WHERE id = %s", (podatki["skrbnik2"],))
        cilj = podatki["skrbnik2"]
    else:
        cilj = podatki["ucitelj"]
    with pytest.raises(PoslovnaNapaka, match="aktivnemu IKT skrbniku"):
        storitev.prerazporedi(_uporabnik(podatki["admin"]), podatki["prijava"], cilj)
    assert preberi_prijavo(podatki["prijava"])["skrbnik_id"] == podatki["skrbnik"]


def test_skrbnik_ne_more_prerazporediti(odjemalec, podatki):
    _prevzeta(podatki)
    prijavi(odjemalec, "skrbnik@sola.si")
    odgovor = odjemalec.post(f"/prijave/{podatki['prijava']}/prerazporeditev",
                             data={"skrbnik_id": podatki["skrbnik2"]})
    assert odgovor.status_code == 403


# --- Učitelj --------------------------------------------------------------------------

def test_ucitelj_nima_dostopa_do_obravnave(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    id_p = podatki["prijava"]
    assert odjemalec.post(f"/prijave/{id_p}/prevzem").status_code == 403
    assert odjemalec.post(f"/prijave/{id_p}/zakljucek", data={"resitev": "X"}).status_code == 403
    assert odjemalec.post(f"/prijave/{id_p}/prerazporeditev",
                          data={"skrbnik_id": podatki["ucitelj"]}).status_code == 403
    assert preberi_prijavo(id_p)["status"] == "nova"


def test_storitev_zavrne_ucitelja(podatki):
    from app.napake import Prepovedano
    with pytest.raises(Prepovedano):
        storitev.prevzemi(_uporabnik(podatki["ucitelj"]), podatki["prijava"])


def test_deaktivacija_skrbnika_z_odprto_prijavo_je_zavrnjena(odjemalec, podatki):
    """Povezava z #17: skrbnika s prevzeto prijavo ni mogoče deaktivirati."""
    _prevzeta(podatki)
    prijavi(odjemalec, "admin@sola.si")
    stran = odjemalec.post(f"/admin/uporabniki/{podatki['skrbnik']}", data={
        "ime": "Sara", "priimek": "Testni", "email": "skrbnik@sola.si", "vloga": "ikt_skrbnik",
    }).get_data(as_text=True)
    assert "Najprej jih prerazporedi" in stran
