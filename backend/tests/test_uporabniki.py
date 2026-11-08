"""Testi ustvarjanja uporabniških računov (US-14)."""

import pytest
from werkzeug.security import check_password_hash

from app.cli import ukaz_create_admin
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import uporabniki as repo_uporabniki
from app.services import uporabniki as storitev
from conftest import prijavi, ustvari_uporabnika


def test_create_admin_ustvari_administratorja(app):
    rezultat = app.test_cli_runner().invoke(
        ukaz_create_admin,
        ["--ime", "Ana", "--priimek", "Admin", "--email", " Admin@Sola.si ",
         "--geslo", "varnogeslo"],
    )
    assert rezultat.exit_code == 0, rezultat.output
    with transakcija() as k:
        u = repo_uporabniki.najdi_po_emailu(k, "admin@sola.si")
    assert u["vloga"] == "administrator"
    assert u["geslo_hash"] != "varnogeslo"
    assert check_password_hash(u["geslo_hash"], "varnogeslo")


def test_create_admin_zavrne_kratko_geslo(app):
    rezultat = app.test_cli_runner().invoke(
        ukaz_create_admin,
        ["--ime", "Ana", "--priimek", "Admin", "--email", "admin@sola.si", "--geslo", "kratko"],
    )
    assert rezultat.exit_code != 0
    assert "vsaj 8 znakov" in rezultat.output


def test_enolicen_email(app):
    storitev.ustvari("Ana", "Novak", "ana@sola.si", "geslo1234", "ucitelj")
    with pytest.raises(PoslovnaNapaka, match="že uporabljen"):
        storitev.ustvari("Ana", "Kos", "ANA@sola.si", "geslo1234", "ucitelj")


@pytest.mark.parametrize("ime, priimek, email, vloga", [
    ("", "Novak", "a@sola.si", "ucitelj"),
    ("Ana", "   ", "a@sola.si", "ucitelj"),
    ("Ana", "Novak", "", "ucitelj"),
    ("Ana", "Novak", "a@sola.si", "ravnatelj"),
])
def test_neveljavni_podatki(app, ime, priimek, email, vloga):
    with pytest.raises(PoslovnaNapaka):
        storitev.ustvari(ime, priimek, email, "geslo1234", vloga)


# --- Stran Uporabniki in obrazec za nov račun ---------------------------------

def _prijavi_admina(odjemalec):
    ustvari_uporabnika("admin@sola.si", "administrator", ime="Ana")
    prijavi(odjemalec, "admin@sola.si")


def test_seznam_uporabnikov_vidi_samo_administrator(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/admin/uporabniki").status_code == 403
    odjemalec.post("/odjava")
    prijavi(odjemalec, "skrbnik@sola.si")
    assert odjemalec.get("/admin/uporabniki").status_code == 403


def test_administrator_ustvari_racun(odjemalec):
    _prijavi_admina(odjemalec)
    odgovor = odjemalec.post("/admin/uporabniki/nov", data={
        "ime": "Maja", "priimek": "Novak", "email": "maja@sola.si",
        "geslo": "zacetno123", "vloga": "ikt_skrbnik",
    }, follow_redirects=True)
    stran = odgovor.get_data(as_text=True)
    assert "Račun je ustvarjen" in stran
    assert "maja@sola.si" in stran
    with transakcija() as k:
        u = repo_uporabniki.najdi_po_emailu(k, "maja@sola.si")
    assert u["vloga"] == "ikt_skrbnik"
    assert check_password_hash(u["geslo_hash"], "zacetno123")


def test_obrazec_zavrne_podvojeno_email_in_neveljavno_vlogo(odjemalec):
    _prijavi_admina(odjemalec)
    podatki = {"ime": "Ana", "priimek": "Kos", "email": "admin@sola.si",
               "geslo": "zacetno123", "vloga": "ucitelj"}
    stran = odjemalec.post("/admin/uporabniki/nov", data=podatki).get_data(as_text=True)
    assert "že uporabljen" in stran

    podatki.update(email="nov@sola.si", vloga="ravnatelj")
    odjemalec.post("/admin/uporabniki/nov", data=podatki)
    with transakcija() as k:
        assert repo_uporabniki.najdi_po_emailu(k, "nov@sola.si") is None
