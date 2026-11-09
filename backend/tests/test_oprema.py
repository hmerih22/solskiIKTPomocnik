"""Testi pregleda opreme (US-01)."""

from conftest import prijavi, ustvari_opremo, ustvari_uporabnika


def _prijavi_ucitelja(odjemalec):
    ustvari_uporabnika("ucitelj@sola.si", "ucitelj")
    prijavi(odjemalec, "ucitelj@sola.si")


def test_seznam_opreme_zahteva_prijavo(odjemalec):
    assert odjemalec.get("/oprema/").status_code == 302


def test_seznam_prikaze_podatke_opreme(odjemalec):
    ustvari_opremo("INV-001", "Projektor Epson")
    _prijavi_ucitelja(odjemalec)
    stran = odjemalec.get("/oprema/").get_data(as_text=True)
    for besedilo in ("Projektor Epson", "INV-001", "projektor", "Uporabna"):
        assert besedilo in stran


def test_nedelujoca_oprema_ostane_vidna_z_oznako(odjemalec):
    ustvari_opremo("INV-002", "Pokvarjen prenosnik", stanje="nedelujoca")
    _prijavi_ucitelja(odjemalec)
    stran = odjemalec.get("/oprema/").get_data(as_text=True)
    assert "Pokvarjen prenosnik" in stran
    assert "Nedelujoča" in stran
    assert "Rezervacija ni mogoča" in stran


def test_prazen_seznam(odjemalec):
    _prijavi_ucitelja(odjemalec)
    assert "Ni evidentirane opreme" in odjemalec.get("/oprema/").get_data(as_text=True)
