"""Testi preklica rezervacij in lastništva (US-04)."""

from datetime import timedelta

import pytest

from app.cas import zdaj_utc
from app.db import transakcija
from app.services.rezervacije import preveri_razpolozljivost
from conftest import jutri_ob, prijavi, ustvari_opremo, ustvari_rezervacijo, ustvari_uporabnika


def _rezervacija(id_r):
    with transakcija() as k:
        k.execute("SELECT status, preklical_id, preklicana_ob, razlog_preklica"
                  " FROM rezervacija WHERE id = %s", (id_r,))
        return k.fetchone()


def _preklici(odjemalec, id_r, razlog=None):
    podatki = {"razlog": razlog} if razlog else {}
    return odjemalec.post(f"/rezervacije/{id_r}/preklic", data=podatki, follow_redirects=True)


@pytest.fixture
def podatki(app):
    """Učitelj z jutrišnjo rezervacijo uporabne opreme."""
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    id_opreme = ustvari_opremo()
    id_r = ustvari_rezervacijo(id_ucitelja, id_opreme, jutri_ob(9), jutri_ob(10))
    return {"ucitelj": id_ucitelja, "oprema": id_opreme, "rezervacija": id_r}


# --- Lastnik ------------------------------------------------------------------

def test_lastnik_preklice_rezervacijo(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    stran = _preklici(odjemalec, podatki["rezervacija"]).get_data(as_text=True)
    assert "Rezervacija je preklicana" in stran

    r = _rezervacija(podatki["rezervacija"])
    assert r["status"] == "preklicana"
    assert r["preklical_id"] == podatki["ucitelj"]
    assert r["preklicana_ob"] is not None


def test_preklic_sprosti_termin(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    assert not preveri_razpolozljivost(podatki["oprema"], jutri_ob(9), jutri_ob(10))["prosta"]
    _preklici(odjemalec, podatki["rezervacija"])
    assert preveri_razpolozljivost(podatki["oprema"], jutri_ob(9), jutri_ob(10))["prosta"]


def test_ze_preklicane_ni_mogoce_preklicati_znova(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    _preklici(odjemalec, podatki["rezervacija"])
    stran = _preklici(odjemalec, podatki["rezervacija"]).get_data(as_text=True)
    assert "že preklicana" in stran


def test_ze_zacete_ni_mogoce_preklicati(odjemalec, app):
    id_u = ustvari_uporabnika("ucitelj@sola.si")
    zacetek = zdaj_utc() - timedelta(minutes=30)
    id_r = ustvari_rezervacijo(id_u, ustvari_opremo(), zacetek, zacetek + timedelta(hours=1))
    prijavi(odjemalec, "ucitelj@sola.si")
    stran = _preklici(odjemalec, id_r).get_data(as_text=True)
    assert "že začela" in stran
    assert _rezervacija(id_r)["status"] == "aktivna"


def test_gumb_preklici_samo_pri_prihodnjih(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    stran = odjemalec.get("/rezervacije/moje").get_data(as_text=True)
    assert f"/rezervacije/{podatki['rezervacija']}/preklic" in stran


# --- Tuje rezervacije -----------------------------------------------------------

def test_ucitelj_ne_more_preklicati_tuje_niti_neposredno(odjemalec, podatki):
    ustvari_uporabnika("drugi@sola.si", "ucitelj")
    prijavi(odjemalec, "drugi@sola.si")
    odgovor = odjemalec.post(f"/rezervacije/{podatki['rezervacija']}/preklic",
                             data={"razlog": "Ker hočem"})
    assert odgovor.status_code == 403
    assert _rezervacija(podatki["rezervacija"])["status"] == "aktivna"


def test_skrbnik_ne_more_preklicati_rezervacije_uporabne_opreme(odjemalec, podatki):
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    odgovor = odjemalec.post(f"/rezervacije/{podatki['rezervacija']}/preklic",
                             data={"razlog": "Test"})
    assert odgovor.status_code == 403
    assert _rezervacija(podatki["rezervacija"])["status"] == "aktivna"


def test_skrbnik_preklice_rezervacijo_nedelujoce_opreme_z_razlogom(odjemalec, podatki):
    with transakcija() as k:
        k.execute("UPDATE oprema SET stanje = 'nedelujoca' WHERE id = %s", (podatki["oprema"],))
    id_skrbnika = ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")

    # Brez razloga ne gre.
    stran = _preklici(odjemalec, podatki["rezervacija"]).get_data(as_text=True)
    assert "razlog je obvezen" in stran
    assert _rezervacija(podatki["rezervacija"])["status"] == "aktivna"

    _preklici(odjemalec, podatki["rezervacija"], "Projektor je pokvarjen")
    r = _rezervacija(podatki["rezervacija"])
    assert r["status"] == "preklicana"
    assert r["preklical_id"] == id_skrbnika
    assert r["razlog_preklica"] == "Projektor je pokvarjen"


def test_administrator_preklice_katerokoli_z_razlogom(odjemalec, podatki):
    ustvari_uporabnika("admin@sola.si", "administrator")
    prijavi(odjemalec, "admin@sola.si")
    _preklici(odjemalec, podatki["rezervacija"], "Šolska prireditev")
    assert _rezervacija(podatki["rezervacija"])["razlog_preklica"] == "Šolska prireditev"


def test_stran_vse_rezervacije_samo_za_skrbnika(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/rezervacije/vse").status_code == 403
    odjemalec.post("/odjava")

    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "skrbnik@sola.si")
    stran = odjemalec.get("/rezervacije/vse").get_data(as_text=True)
    assert "Projektor 1" in stran


def test_preusmeritev_po_preklicu_ostane_v_aplikaciji(odjemalec, podatki):
    prijavi(odjemalec, "ucitelj@sola.si")
    odgovor = odjemalec.post(f"/rezervacije/{podatki['rezervacija']}/preklic",
                             data={"naprej": "https://zlobna-stran.si"})
    assert "zlobna-stran" not in odgovor.headers["Location"]
