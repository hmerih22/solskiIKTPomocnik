"""Testi osnovnih evidenc: učilnice in oprema (US-15)."""

import pytest

from app.auth import Uporabnik
from app.db import transakcija
from app.napake import PoslovnaNapaka, Prepovedano
from app.repositories import uporabniki as repo_uporabniki
from app.services import evidence
from conftest import prijavi, stevilo_vrstic, ustvari_ucilnico, ustvari_uporabnika


def _prijavi_admina(odjemalec):
    ustvari_uporabnika("admin@sola.si", "administrator")
    prijavi(odjemalec, "admin@sola.si")


def _oprema(**spremembe):
    podatki = {"naziv": "Projektor 1", "inventarna_stevilka": "INV-1", "vrsta": "projektor",
               "opis": "", "stanje": "uporabna"}
    podatki.update(spremembe)
    return podatki


# --- Učilnice ----------------------------------------------------------------

def test_dodajanje_in_urejanje_ucilnice(odjemalec):
    _prijavi_admina(odjemalec)
    stran = odjemalec.post("/admin/ucilnice/nova", data={
        "oznaka": "12", "naziv": "Matematika", "opis": ""}, follow_redirects=True
    ).get_data(as_text=True)
    assert "Učilnica je dodana" in stran

    with transakcija() as k:
        k.execute("SELECT id, oznaka, naziv, opis FROM ucilnica")
        u = k.fetchone()
    assert (u["oznaka"], u["naziv"], u["opis"]) == ("12", "Matematika", None)

    # Poskus spremembe oznake se prezre, naziv in opis se spremenita.
    odjemalec.post(f"/admin/ucilnice/{u['id']}", data={
        "oznaka": "99", "naziv": "Računalniška", "opis": "20 računalnikov"})
    with transakcija() as k:
        k.execute("SELECT oznaka, naziv, opis FROM ucilnica WHERE id = %s", (u["id"],))
        assert k.fetchone() == {"oznaka": "12", "naziv": "Računalniška",
                                "opis": "20 računalnikov"}


def test_podvojena_oznaka_ucilnice(odjemalec):
    _prijavi_admina(odjemalec)
    ustvari_ucilnico("12")
    stran = odjemalec.post("/admin/ucilnice/nova", data={
        "oznaka": " 12 ", "naziv": "Druga"}).get_data(as_text=True)
    assert "že obstaja" in stran
    assert stevilo_vrstic("ucilnica") == 1


@pytest.mark.parametrize("podatki", [
    {"oznaka": "", "naziv": "Matematika"},
    {"oznaka": "13", "naziv": "   "},
])
def test_manjkajoci_podatki_ucilnice_brez_zapisa(odjemalec, podatki):
    _prijavi_admina(odjemalec)
    odjemalec.post("/admin/ucilnice/nova", data=podatki)
    assert stevilo_vrstic("ucilnica") == 0


# --- Oprema ------------------------------------------------------------------

def test_dodajanje_in_urejanje_opreme(odjemalec):
    _prijavi_admina(odjemalec)
    id_ucilnice = ustvari_ucilnico("12")
    stran = odjemalec.post("/admin/oprema/nova", data=_oprema(ucilnica_id=id_ucilnice),
                           follow_redirects=True).get_data(as_text=True)
    assert "Oprema je shranjena" in stran
    assert "INV-1" in stran

    with transakcija() as k:
        k.execute("SELECT id FROM oprema")
        id_opreme = k.fetchone()["id"]
    odjemalec.post(f"/admin/oprema/{id_opreme}", data=_oprema(
        naziv="Projektor Epson", stanje="nedelujoca", ucilnica_id=id_ucilnice))
    with transakcija() as k:
        k.execute("SELECT naziv, stanje FROM oprema WHERE id = %s", (id_opreme,))
        assert k.fetchone() == {"naziv": "Projektor Epson", "stanje": "nedelujoca"}


def test_podvojena_inventarna_stevilka(odjemalec):
    _prijavi_admina(odjemalec)
    id_ucilnice = ustvari_ucilnico("12")
    odjemalec.post("/admin/oprema/nova", data=_oprema(ucilnica_id=id_ucilnice))
    stran = odjemalec.post("/admin/oprema/nova", data=_oprema(
        naziv="Drug projektor", ucilnica_id=id_ucilnice)).get_data(as_text=True)
    assert "že obstaja" in stran
    assert stevilo_vrstic("oprema") == 1


@pytest.mark.parametrize("polje", ["naziv", "inventarna_stevilka", "vrsta"])
def test_manjkajoci_podatki_opreme_brez_zapisa(odjemalec, polje):
    _prijavi_admina(odjemalec)
    id_ucilnice = ustvari_ucilnico("12")
    odjemalec.post("/admin/oprema/nova", data=_oprema(ucilnica_id=id_ucilnice, **{polje: " "}))
    assert stevilo_vrstic("oprema") == 0


def test_neobstojeca_ucilnica_brez_zapisa(app):
    admin = _uporabnik(ustvari_uporabnika("admin@sola.si", "administrator"))
    with pytest.raises(PoslovnaNapaka):
        evidence.shrani_opremo(admin, None, "Projektor", "INV-1", "projektor", None,
                               "uporabna", 9999)
    assert stevilo_vrstic("oprema") == 0


def test_oprema_brez_ucilnic_preusmeri_na_novo_ucilnico(odjemalec):
    _prijavi_admina(odjemalec)
    odgovor = odjemalec.get("/admin/oprema/nova")
    assert odgovor.status_code == 302
    assert "/admin/ucilnice/nova" in odgovor.headers["Location"]


# --- Pravice -----------------------------------------------------------------

def _uporabnik(id_u):
    with transakcija() as k:
        return Uporabnik(repo_uporabniki.najdi(k, id_u))


@pytest.mark.parametrize("vloga", ["ucitelj", "ikt_skrbnik"])
def test_zavrnitev_za_ucitelja_in_skrbnika(odjemalec, vloga):
    id_ucilnice = ustvari_ucilnico("12")
    ustvari_uporabnika("jaz@sola.si", vloga)
    prijavi(odjemalec, "jaz@sola.si")

    assert odjemalec.get("/admin/ucilnice").status_code == 403
    assert odjemalec.post("/admin/ucilnice/nova",
                          data={"oznaka": "13", "naziv": "X"}).status_code == 403
    assert odjemalec.post(f"/admin/ucilnice/{id_ucilnice}",
                          data={"naziv": "Spremenjeno"}).status_code == 403
    assert odjemalec.post("/admin/oprema/nova",
                          data=_oprema(ucilnica_id=id_ucilnice)).status_code == 403
    assert stevilo_vrstic("ucilnica") == 1
    assert stevilo_vrstic("oprema") == 0


@pytest.mark.parametrize("vloga", ["ucitelj", "ikt_skrbnik"])
def test_storitev_zavrne_brez_pravic(app, vloga):
    jaz = _uporabnik(ustvari_uporabnika("jaz@sola.si", vloga))
    with pytest.raises(Prepovedano):
        evidence.dodaj_ucilnico(jaz, "12", "Matematika")
    with pytest.raises(Prepovedano):
        evidence.shrani_opremo(jaz, None, "Projektor", "INV-1", "projektor", None,
                               "uporabna", ustvari_ucilnico("12"))
