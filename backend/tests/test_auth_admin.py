"""Testi prijave v aplikacijo (US-13), upravljanja računov (US-14)
in osnovnih evidenc (US-15)."""

import pytest
from werkzeug.security import check_password_hash

from app.db import transakcija
from app.napake import PoslovnaNapaka, Prepovedano
from app.repositories import uporabniki as repo_uporabniki
from app.services import oprema as storitev_oprema
from app.services import prijave as storitev_prijave
from app.services import uporabniki as storitev

from conftest import GESLO, prijavi, ustvari_uporabnika


# --- US-13: prijava ------------------------------------------------------------

def test_uspesna_prijava_in_odjava(odjemalec, ucitelj):
    odgovor = prijavi(odjemalec, ucitelj.email)
    assert odgovor.status_code == 302
    assert odjemalec.get("/").status_code == 200

    odjemalec.post("/odjava")
    assert odjemalec.get("/").status_code == 302


@pytest.mark.parametrize("email, geslo", [
    ("ucitelj@sola.si", "napacno-geslo"),
    ("neobstaja@sola.si", GESLO),
])
def test_napacni_podatki_ne_prijavijo(odjemalec, ucitelj, email, geslo):
    odgovor = prijavi(odjemalec, email, geslo)
    assert "Napačen e-poštni naslov ali geslo" in odgovor.get_data(as_text=True)
    assert odjemalec.get("/").status_code == 302


def test_neaktiven_racun_se_ne_more_prijaviti(odjemalec, app):
    neaktiven = ustvari_uporabnika("ucitelj", "neaktiven@sola.si", aktiven=False)
    odgovor = prijavi(odjemalec, neaktiven.email)
    assert "deaktiviran" in odgovor.get_data(as_text=True)
    assert odjemalec.get("/").status_code == 302


def test_deaktivacija_in_sprememba_vloge_veljata_takoj(odjemalec, admin, skrbnik):
    prijavi(odjemalec, skrbnik.email)
    assert odjemalec.get("/prijave/vse").status_code == 200

    storitev.posodobi(admin, skrbnik.id, skrbnik.ime, skrbnik.priimek, skrbnik.email, "ucitelj", True)
    assert odjemalec.get("/prijave/vse").status_code == 403

    storitev.posodobi(admin, skrbnik.id, skrbnik.ime, skrbnik.priimek, skrbnik.email, "ucitelj", False)
    assert odjemalec.get("/").status_code == 302  # seja ni več veljavna


# --- US-14: računi -------------------------------------------------------------

def test_administrator_ustvari_racun_z_zgosceno_geslo(admin):
    id_novega = storitev.ustvari_kot_administrator(admin, "Nov", "Učitelj", " Nov@Sola.si ",
                                                   "zacetno123", "ucitelj")
    with transakcija() as k:
        nov = repo_uporabniki.najdi(k, id_novega)
    assert nov["email"] == "nov@sola.si"
    assert nov["geslo_hash"] != "zacetno123"
    assert check_password_hash(nov["geslo_hash"], "zacetno123")


def test_podvojen_email_in_neveljavna_vloga_sta_zavrnjena(admin, ucitelj):
    with pytest.raises(PoslovnaNapaka, match="že uporabljen"):
        storitev.ustvari_kot_administrator(admin, "X", "Y", "UCITELJ@sola.si", "geslo1234", "ucitelj")
    with pytest.raises(PoslovnaNapaka, match="vloga"):
        storitev.ustvari_kot_administrator(admin, "X", "Y", "x@sola.si", "geslo1234", "ravnatelj")


def test_ucitelj_in_skrbnik_ne_upravljata_racunov(odjemalec, ucitelj, skrbnik):
    for uporabnik in (ucitelj, skrbnik):
        with pytest.raises(Prepovedano):
            storitev.ustvari_kot_administrator(uporabnik, "X", "Y", "x@sola.si", "geslo1234", "ucitelj")
        prijavi(odjemalec, uporabnik.email)
        assert odjemalec.get("/admin/uporabniki").status_code == 403
        assert odjemalec.post("/admin/uporabniki/nov", data={
            "ime": "X", "priimek": "Y", "email": "x@sola.si", "vloga": "administrator",
            "geslo": "geslo1234"}).status_code == 403
        odjemalec.post("/odjava")


def test_skrbnika_z_odprtimi_prijavami_ni_mogoce_deaktivirati(admin, skrbnik, ucitelj, projektor):
    id_prijave = storitev_prijave.oddaj(ucitelj, projektor["id"], None, "Napaka", "Opis")
    storitev_prijave.prevzemi(skrbnik, id_prijave)

    for vloga, aktiven in [("ikt_skrbnik", False), ("ucitelj", True)]:
        with pytest.raises(PoslovnaNapaka, match="prerazporedi"):
            storitev.posodobi(admin, skrbnik.id, skrbnik.ime, skrbnik.priimek, skrbnik.email,
                              vloga, aktiven)


def test_zadnjega_administratorja_ni_mogoce_odstraniti(admin):
    with pytest.raises(PoslovnaNapaka, match="vsaj en aktiven administrator"):
        storitev.posodobi(admin, admin.id, admin.ime, admin.priimek, admin.email, "ucitelj", True)


def test_ukaz_create_admin(app):
    rezultat = app.test_cli_runner().invoke(args=[
        "create-admin", "--ime", "Prvi", "--priimek", "Admin", "--email", "prvi@sola.si",
        "--geslo", "varnogeslo1"])
    assert rezultat.exit_code == 0, rezultat.output
    with transakcija() as k:
        assert repo_uporabniki.najdi_po_emailu(k, "prvi@sola.si")["vloga"] == "administrator"


# --- US-15: učilnice in oprema ---------------------------------------------------

def test_podvojena_oznaka_in_inventarna_stevilka_sta_zavrnjeni(admin, ucilnica, projektor):
    with pytest.raises(PoslovnaNapaka, match="že obstaja"):
        storitev_oprema.shrani_ucilnico(admin, None, ucilnica["oznaka"], "Druga", None)
    with pytest.raises(PoslovnaNapaka, match="že obstaja"):
        storitev_oprema.shrani_opremo(admin, None, "Drug", projektor["inventarna_stevilka"],
                                      "projektor", None, "uporabna", ucilnica["id"])


def test_urejanje_opreme_ohrani_identifikator(admin, ucilnica, projektor):
    id_opreme = storitev_oprema.shrani_opremo(admin, projektor["id"], "Projektor A", "INV-1",
                                              "projektor", "Nov opis", "uporabna", ucilnica["id"])
    assert id_opreme == projektor["id"]


def test_skrbnik_ne_ureja_evidenc(skrbnik, ucilnica):
    with pytest.raises(Prepovedano):
        storitev_oprema.shrani_ucilnico(skrbnik, None, "99", "Nova", None)
    with pytest.raises(Prepovedano):
        storitev_oprema.shrani_opremo(skrbnik, None, "X", "INV-9", "x", None, "uporabna", ucilnica["id"])


def test_strani_se_prikazejo_vsem_vlogam(odjemalec, ucitelj, skrbnik, projektor, ucilnica, jutri_ob_9):
    """Dimni test z rezervacijo in odprto prijavo: začetna stran in seznami za vse vloge."""
    from app.services import rezervacije as storitev_rezervacije
    storitev_rezervacije.ustvari(ucitelj, projektor["id"], jutri_ob_9, jutri_ob_9.replace(hour=10))
    id_prijave = storitev_prijave.oddaj(ucitelj, projektor["id"], ucilnica["id"], "Napaka", "Opis")
    storitev_prijave.dodaj_komentar(ucitelj, id_prijave, "Komentar")

    for uporabnik in (ucitelj, skrbnik):
        prijavi(odjemalec, uporabnik.email)
        for pot in ["/", "/oprema/", "/rezervacije/moje", "/prijave/moje", f"/prijave/{id_prijave}"]:
            assert odjemalec.get(pot).status_code == 200, (uporabnik.email, pot)
        odjemalec.post("/odjava")


def test_vse_strani_se_prikazejo_administratorju(odjemalec, admin, ucitelj, projektor, ucilnica):
    """Dimni test: vsaka glavna stran se brez napake izriše."""
    id_prijave = storitev_prijave.oddaj(ucitelj, projektor["id"], ucilnica["id"], "Napaka", "Opis")
    prijavi(odjemalec, admin.email)
    for pot in ["/", "/oprema/", f"/rezervacije/nova/{projektor['id']}", "/rezervacije/moje",
                "/rezervacije/vse", "/rezervacije/vse?prikaz=vse", "/rezervacije/izposoja",
                "/prijave/nova", "/prijave/moje", "/prijave/vse", "/prijave/vse?status=nova",
                f"/prijave/{id_prijave}", "/admin/uporabniki", "/admin/uporabniki/nov",
                f"/admin/uporabniki/{admin.id}", "/admin/ucilnice", "/admin/ucilnice/nova",
                f"/admin/ucilnice/{ucilnica['id']}", "/admin/oprema/nova",
                f"/admin/oprema/{projektor['id']}", "/admin/obvestila", "/statistika/"]:
        assert odjemalec.get(pot).status_code == 200, pot
