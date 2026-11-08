"""Testi prijave in dostopa (US-13). Potrebujejo testno bazo."""

from flask import Blueprint

from app.auth import zahteva_vlogo
from conftest import prijavi, spremeni_uporabnika, ustvari_uporabnika


def test_uspesna_prijava(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si", ime="Uroš")
    odgovor = prijavi(odjemalec, "ucitelj@sola.si")
    assert odgovor.status_code == 302
    stran = odjemalec.get("/").get_data(as_text=True)
    assert "Pozdravljen, Uroš" in stran


def test_prijava_ne_loci_velikih_crk_v_emailu(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si")
    assert prijavi(odjemalec, "  UCITELJ@sola.si ").status_code == 302


def test_napacno_geslo(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si")
    odgovor = prijavi(odjemalec, "ucitelj@sola.si", "napacno")
    assert odgovor.status_code == 200
    assert "Napačen e-poštni naslov ali geslo." in odgovor.get_data(as_text=True)
    assert odjemalec.get("/").status_code == 302


def test_neznan_email_da_isto_sporocilo(odjemalec):
    odgovor = prijavi(odjemalec, "nihce@sola.si")
    assert "Napačen e-poštni naslov ali geslo." in odgovor.get_data(as_text=True)


def test_neaktiven_racun_se_ne_more_prijaviti(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si", aktiven=False)
    odgovor = prijavi(odjemalec, "ucitelj@sola.si")
    assert "Račun je deaktiviran" in odgovor.get_data(as_text=True)
    assert odjemalec.get("/").status_code == 302


def test_dostop_brez_prijave_preusmeri_na_prijavo(odjemalec):
    odgovor = odjemalec.get("/")
    assert odgovor.status_code == 302
    assert "/prijava" in odgovor.headers["Location"]


def test_odjava(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.post("/odjava").status_code == 302
    assert odjemalec.get("/").status_code == 302


def test_deaktivacija_odjavi_ze_prijavljenega(odjemalec):
    id_u = ustvari_uporabnika("ucitelj@sola.si")
    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/").status_code == 200

    spremeni_uporabnika(id_u, aktiven=False)
    assert odjemalec.get("/").status_code == 302


def _app_s_testno_potjo(app):
    bp = Blueprint("test_vloge", __name__)

    @bp.get("/samo-admin")
    @zahteva_vlogo("administrator")
    def samo_admin():
        return "ok"

    @bp.get("/samo-skrbnik")
    @zahteva_vlogo("ikt_skrbnik")
    def samo_skrbnik():
        return "ok"

    app.register_blueprint(bp)


def test_vloge_in_dedovanje_pravic(app, odjemalec):
    _app_s_testno_potjo(app)
    ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    ustvari_uporabnika("skrbnik@sola.si", "ikt_skrbnik")
    ustvari_uporabnika("admin@sola.si", "administrator")

    prijavi(odjemalec, "ucitelj@sola.si")
    assert odjemalec.get("/samo-skrbnik").status_code == 403
    assert odjemalec.get("/samo-admin").status_code == 403
    odjemalec.post("/odjava")

    prijavi(odjemalec, "skrbnik@sola.si")
    assert odjemalec.get("/samo-skrbnik").status_code == 200
    assert odjemalec.get("/samo-admin").status_code == 403
    odjemalec.post("/odjava")

    prijavi(odjemalec, "admin@sola.si")
    assert odjemalec.get("/samo-skrbnik").status_code == 200
    assert odjemalec.get("/samo-admin").status_code == 200


def test_sprememba_vloge_ucinkuje_takoj(app, odjemalec):
    _app_s_testno_potjo(app)
    id_u = ustvari_uporabnika("admin@sola.si", "administrator")
    prijavi(odjemalec, "admin@sola.si")
    assert odjemalec.get("/samo-admin").status_code == 200

    spremeni_uporabnika(id_u, vloga="ucitelj")
    assert odjemalec.get("/samo-admin").status_code == 403


def test_preusmeritev_po_prijavi_samo_znotraj_aplikacije(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si")
    odgovor = odjemalec.post("/prijava?next=https://zlobna-stran.si",
                             data={"email": "ucitelj@sola.si", "geslo": "geslo1234"})
    assert "zlobna-stran" not in odgovor.headers["Location"]
