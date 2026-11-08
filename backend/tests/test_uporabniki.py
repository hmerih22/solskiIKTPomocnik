"""Testi ustvarjanja uporabniških računov (US-14)."""

import pytest
from werkzeug.security import check_password_hash

from app.cli import ukaz_create_admin
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import uporabniki as repo_uporabniki
from app.services import uporabniki as storitev


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
