"""Testi upravljanja uporabniških računov (US-14)."""

import pytest
from werkzeug.security import check_password_hash

from app.cli import ukaz_create_admin
from app.db import transakcija
from app.napake import PoslovnaNapaka
from app.repositories import uporabniki as repo_uporabniki
from app.services import uporabniki as storitev
from conftest import prijavi, ustvari_prevzeto_prijavo, ustvari_ucilnico, ustvari_uporabnika


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



# --- Urejanje vloge in deaktivacija (#17, #18) --------------------------------

def _podatki(**spremembe):
    podatki = {"ime": "Maja", "priimek": "Novak", "email": "maja@sola.si",
               "vloga": "ikt_skrbnik", "aktiven": "y"}
    podatki.update(spremembe)
    # Neoznačeno potrditveno polje brskalnik sploh ne pošlje.
    return {kljuc: v for kljuc, v in podatki.items() if v is not None}


def _uporabnik(id_u):
    with transakcija() as k:
        return repo_uporabniki.najdi(k, id_u)


def test_sprememba_vloge(odjemalec):
    _prijavi_admina(odjemalec)
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    odgovor = odjemalec.post(f"/admin/uporabniki/{id_u}", data=_podatki(),
                             follow_redirects=True)
    assert "Podatki uporabnika so shranjeni" in odgovor.get_data(as_text=True)
    assert _uporabnik(id_u)["vloga"] == "ikt_skrbnik"


def test_deaktivacija_racuna(odjemalec):
    _prijavi_admina(odjemalec)
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    odjemalec.post(f"/admin/uporabniki/{id_u}", data=_podatki(vloga="ucitelj", aktiven=None))
    assert not _uporabnik(id_u)["aktiven"]


def test_deaktivacija_zavrnjena_ob_odprtih_prijavah(odjemalec):
    _prijavi_admina(odjemalec)
    id_skrbnika = ustvari_uporabnika("maja@sola.si", "ikt_skrbnik")
    id_ucitelja = ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    ustvari_prevzeto_prijavo(id_ucitelja, id_skrbnika, ustvari_ucilnico())

    for podatki in (_podatki(aktiven=None), _podatki(vloga="ucitelj")):
        stran = odjemalec.post(f"/admin/uporabniki/{id_skrbnika}",
                               data=podatki).get_data(as_text=True)
        assert "Najprej jih prerazporedi" in stran
    u = _uporabnik(id_skrbnika)
    assert u["aktiven"] and u["vloga"] == "ikt_skrbnik"


def test_zadnji_administrator_ostane(odjemalec):
    _prijavi_admina(odjemalec)
    with transakcija() as k:
        id_admina = repo_uporabniki.najdi_po_emailu(k, "admin@sola.si")["id"]
    stran = odjemalec.post(f"/admin/uporabniki/{id_admina}", data=_podatki(
        email="admin@sola.si", vloga="ucitelj")).get_data(as_text=True)
    assert "vsaj en aktiven administrator" in stran
    assert _uporabnik(id_admina)["vloga"] == "administrator"


def test_urejanje_zavrne_podvojeno_email(odjemalec):
    _prijavi_admina(odjemalec)
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    stran = odjemalec.post(f"/admin/uporabniki/{id_u}",
                           data=_podatki(email="admin@sola.si")).get_data(as_text=True)
    assert "že uporabljen" in stran
    assert _uporabnik(id_u)["email"] == "maja@sola.si"


@pytest.mark.parametrize("polje", ["ime", "priimek", "email"])
def test_urejanje_zavrne_manjkajoce_podatke(odjemalec, polje):
    _prijavi_admina(odjemalec)
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    odjemalec.post(f"/admin/uporabniki/{id_u}", data=_podatki(**{polje: "   "}))
    assert _uporabnik(id_u)["vloga"] == "ucitelj"


def test_urejanje_zavrne_neveljavno_vlogo(odjemalec):
    _prijavi_admina(odjemalec)
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    odjemalec.post(f"/admin/uporabniki/{id_u}", data=_podatki(vloga="ravnatelj"))
    assert _uporabnik(id_u)["vloga"] == "ucitelj"


@pytest.mark.parametrize("vloga", ["ucitelj", "ikt_skrbnik"])
def test_neposredna_zahteva_brez_pravic_je_zavrnjena(odjemalec, vloga):
    """Učitelj in IKT skrbnik ne moreta urejati računov niti z ročno poslano zahtevo."""
    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    ustvari_uporabnika("jaz@sola.si", vloga)
    prijavi(odjemalec, "jaz@sola.si")

    assert odjemalec.get(f"/admin/uporabniki/{id_u}").status_code == 403
    assert odjemalec.post(f"/admin/uporabniki/{id_u}",
                          data=_podatki(vloga="administrator")).status_code == 403
    assert odjemalec.post("/admin/uporabniki/nov", data={
        "ime": "X", "priimek": "Y", "email": "x@sola.si", "geslo": "geslo1234",
        "vloga": "administrator"}).status_code == 403
    assert _uporabnik(id_u)["vloga"] == "ucitelj"


def test_storitev_sama_preveri_pravice(app):
    """Tudi klic storitve mimo poti zavrne uporabnika, ki ni administrator."""
    from app.auth import Uporabnik
    from app.napake import Prepovedano

    id_u = ustvari_uporabnika("maja@sola.si", "ucitelj")
    skrbnik = Uporabnik(_uporabnik(ustvari_uporabnika("s@sola.si", "ikt_skrbnik")))
    with pytest.raises(Prepovedano):
        storitev.posodobi(skrbnik, id_u, "Maja", "Novak", "maja@sola.si", "administrator", True)
