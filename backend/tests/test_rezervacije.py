"""Testi ustvarjanja rezervacij (US-03)."""

import pytest

from app.auth import Uporabnik
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import uporabniki as repo_uporabniki
from app.services import rezervacije as storitev
from conftest import (jutri_ob, prijavi, stevilo_vrstic, ustvari_opremo, ustvari_rezervacijo,
                      ustvari_uporabnika)


@pytest.fixture
def ucitelj(app):
    with transakcija() as k:
        return Uporabnik(repo_uporabniki.najdi(k, ustvari_uporabnika("ucitelj@sola.si")))


def test_uspesna_rezervacija(ucitelj):
    id_o = ustvari_opremo()
    id_r = storitev.ustvari(ucitelj, id_o, jutri_ob(9), jutri_ob(10))
    with transakcija() as k:
        k.execute("SELECT uporabnik_id, oprema_id, zacetek, konec, status"
                  " FROM rezervacija WHERE id = %s", (id_r,))
        r = k.fetchone()
    assert r == {"uporabnik_id": ucitelj.id, "oprema_id": id_o, "zacetek": jutri_ob(9),
                 "konec": jutri_ob(10), "status": "aktivna"}


def test_prekrivanje_je_zavrnjeno_brez_zapisa(ucitelj):
    id_o = ustvari_opremo()
    ustvari_rezervacijo(ucitelj.id, id_o, jutri_ob(9), jutri_ob(10))
    with pytest.raises(PoslovnaNapaka, match="zaseden"):
        storitev.ustvari(ucitelj, id_o, jutri_ob(9, 30), jutri_ob(10, 30))
    assert stevilo_vrstic("rezervacija") == 1


def test_zaporedni_termin_je_dovoljen(ucitelj):
    id_o = ustvari_opremo()
    ustvari_rezervacijo(ucitelj.id, id_o, jutri_ob(9), jutri_ob(10))
    storitev.ustvari(ucitelj, id_o, jutri_ob(10), jutri_ob(11))
    assert stevilo_vrstic("rezervacija") == 2


def test_nedelujoca_oprema_je_zavrnjena(ucitelj):
    with pytest.raises(PoslovnaNapaka, match="nedelujoča"):
        storitev.ustvari(ucitelj, ustvari_opremo(stanje="nedelujoca"), jutri_ob(9), jutri_ob(10))
    assert stevilo_vrstic("rezervacija") == 0


def test_neobstojeca_oprema(ucitelj):
    with pytest.raises(PoslovnaNapaka, match="ne obstaja"):
        storitev.ustvari(ucitelj, 9999, jutri_ob(9), jutri_ob(10))


def test_neveljaven_termin_brez_zapisa(ucitelj):
    with pytest.raises(PoslovnaNapaka):
        storitev.ustvari(ucitelj, ustvari_opremo(), jutri_ob(10), jutri_ob(9))
    assert stevilo_vrstic("rezervacija") == 0


# --- Obrazec Potrdi rezervacijo (#28) -----------------------------------------

def _lokalno(utc):
    from app.cas import v_lokalni
    return v_lokalni(utc).strftime("%Y-%m-%dT%H:%M")


def _potrdi(odjemalec, id_o, zacetek, konec):
    return odjemalec.post(f"/rezervacije/nova/{id_o}", data={
        "zacetek": _lokalno(zacetek), "konec": _lokalno(konec), "potrdi": "Potrdi rezervacijo",
    }, follow_redirects=True).get_data(as_text=True)


def test_potrditev_prek_obrazca(odjemalec, ucitelj):
    prijavi(odjemalec, "ucitelj@sola.si")
    id_o = ustvari_opremo()
    stran = _potrdi(odjemalec, id_o, jutri_ob(9), jutri_ob(10))
    assert "Rezervacija je potrjena" in stran
    with transakcija() as k:
        k.execute("SELECT zacetek, konec FROM rezervacija")
        assert k.fetchone() == {"zacetek": jutri_ob(9), "konec": jutri_ob(10)}


def test_konflikt_ob_oddaji(odjemalec, ucitelj):
    """Termin je bil prost ob preverjanju, ob oddaji pa ga je že zasedel drug."""
    prijavi(odjemalec, "ucitelj@sola.si")
    id_o = ustvari_opremo()
    drugi = ustvari_uporabnika("drugi@sola.si")
    ustvari_rezervacijo(drugi, id_o, jutri_ob(9), jutri_ob(10))

    stran = _potrdi(odjemalec, id_o, jutri_ob(9), jutri_ob(10))
    assert "Termin je že zaseden" in stran
    assert stevilo_vrstic("rezervacija") == 1


def test_gumb_preveri_ne_ustvari_rezervacije(odjemalec, ucitelj):
    prijavi(odjemalec, "ucitelj@sola.si")
    id_o = ustvari_opremo()
    odjemalec.post(f"/rezervacije/nova/{id_o}", data={
        "zacetek": _lokalno(jutri_ob(9)), "konec": _lokalno(jutri_ob(10)),
        "preveri": "Preveri termin"})
    assert stevilo_vrstic("rezervacija") == 0


# --- Sočasne rezervacije (#29) ------------------------------------------------

def test_socasni_prekrivajoci_rezervaciji_uspe_natanko_ena(app, monkeypatch):
    """Dva uporabnika hkrati rezervirata isto opremo v prekrivajočem terminu.

    Vsaka nit ima svojo povezavo z bazo (svojo transakcijo). Med preverjanjem
    prekrivanja in vpisom umetno počakamo, da bi brez zaklepanja obe niti
    videli prost termin. Zaradi SELECT ... FOR UPDATE na opremi druga nit
    počaka prvo in nato vidi njeno rezervacijo, zato uspe natanko ena.
    """
    import threading
    import time

    from app.repositories import rezervacije as repo_rezervacije

    id_o = ustvari_opremo()
    uporabnika = []
    for email in ("prvi@sola.si", "drugi@sola.si"):
        with transakcija() as k:
            uporabnika.append(Uporabnik(repo_uporabniki.najdi(k, ustvari_uporabnika(email))))

    originalna = repo_rezervacije.prekrivajoce

    def pocasna_prekrivajoce(*args, **kwargs):
        rezultat = originalna(*args, **kwargs)
        time.sleep(0.5)
        return rezultat

    monkeypatch.setattr(repo_rezervacije, "prekrivajoce", pocasna_prekrivajoce)

    start = threading.Barrier(2)
    rezultati = []

    def rezerviraj(uporabnik, zacetek, konec):
        with app.app_context():
            start.wait(timeout=10)
            try:
                storitev.ustvari(uporabnik, id_o, zacetek, konec)
                rezultati.append("uspeh")
            except PoslovnaNapaka:
                rezultati.append("zavrnjena")

    niti = [
        threading.Thread(target=rezerviraj, args=(uporabnika[0], jutri_ob(9), jutri_ob(10))),
        threading.Thread(target=rezerviraj, args=(uporabnika[1], jutri_ob(9, 30), jutri_ob(10, 30))),
    ]
    for nit in niti:
        nit.start()
    for nit in niti:
        nit.join(timeout=30)

    assert sorted(rezultati) == ["uspeh", "zavrnjena"]
    assert stevilo_vrstic("rezervacija") == 1


# --- Moje rezervacije (#30) ---------------------------------------------------

def test_moje_rezervacije(odjemalec, ucitelj):
    from datetime import timedelta

    from app.cas import v_lokalni

    prijavi(odjemalec, "ucitelj@sola.si")
    projektor = ustvari_opremo("INV-1", "Projektor")
    prenosnik = ustvari_opremo("INV-2", "Prenosnik")
    tablica = ustvari_opremo("INV-3", "Tablica")
    tuja = ustvari_opremo("INV-4", "Tuja oprema")
    vceraj = jutri_ob(9) - timedelta(days=2)

    ustvari_rezervacijo(ucitelj.id, projektor, jutri_ob(9), jutri_ob(10))
    ustvari_rezervacijo(ucitelj.id, prenosnik, vceraj, vceraj + timedelta(hours=1))
    id_p = ustvari_rezervacijo(ucitelj.id, tablica, jutri_ob(11), jutri_ob(12), preklicana=True)
    with transakcija() as k:
        k.execute("UPDATE rezervacija SET razlog_preklica = 'Odpadla ura' WHERE id = %s", (id_p,))
    ustvari_rezervacijo(ustvari_uporabnika("drugi@sola.si"), tuja, jutri_ob(9), jutri_ob(10))

    stran = odjemalec.get("/rezervacije/moje").get_data(as_text=True)
    prihodnje, ostalo = stran.split("<h2>Pretekle</h2>")
    pretekle, preklicane = ostalo.split("<h2>Preklicane</h2>")

    assert "Projektor" in prihodnje and "Prihodnja" in prihodnje
    assert v_lokalni(jutri_ob(9)).strftime("%H:%M") in prihodnje
    assert "Prenosnik" in pretekle and "Pretekla" in pretekle
    assert "Tablica" in preklicane and "Odpadla ura" in preklicane
    assert "Tuja oprema" not in stran


def test_moje_rezervacije_brez_rezervacij(odjemalec, ucitelj):
    prijavi(odjemalec, "ucitelj@sola.si")
    assert "Nimaš prihodnjih rezervacij" in odjemalec.get("/rezervacije/moje").get_data(as_text=True)


def test_po_potrditvi_preusmeri_na_moje_rezervacije(odjemalec, ucitelj):
    prijavi(odjemalec, "ucitelj@sola.si")
    id_o = ustvari_opremo()
    odgovor = odjemalec.post(f"/rezervacije/nova/{id_o}", data={
        "zacetek": _lokalno(jutri_ob(9)), "konec": _lokalno(jutri_ob(10)), "potrdi": "1"})
    assert odgovor.headers["Location"].endswith("/rezervacije/moje")
