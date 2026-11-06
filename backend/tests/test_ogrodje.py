"""Osnovni testi ogrodja aplikacije (#7) in pretvorbe časa. Ne potrebujejo baze."""

from datetime import datetime

import pytest

from app import create_app
from app.cas import oblikuj, v_utc
from app.config import ManjkajocaNastavitev, nalozi_nastavitve
from app.pomocniki import je_lokalna_pot


@pytest.fixture
def odjemalec_brez_baze():
    return create_app({"TESTING": True, "SECRET_KEY": "test"}).test_client()


def test_stran_za_prijavo_se_odpre(odjemalec_brez_baze):
    odgovor = odjemalec_brez_baze.get("/prijava")
    assert odgovor.status_code == 200
    assert "Šolski IKT pomočnik" in odgovor.get_data(as_text=True)


def test_neprijavljen_uporabnik_je_preusmerjen_na_prijavo(odjemalec_brez_baze):
    for pot in ["/", "/oprema/", "/rezervacije/moje", "/prijave/vse", "/admin/uporabniki"]:
        odgovor = odjemalec_brez_baze.get(pot)
        assert odgovor.status_code == 302, pot
        assert "/prijava" in odgovor.headers["Location"]


def test_manjkajoca_nastavitev_sprozi_jasno_napako(monkeypatch):
    # Prepreči branje prave datoteke .env in odstrani SECRET_KEY iz okolja.
    monkeypatch.setattr("app.config.load_dotenv", lambda: None)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ManjkajocaNastavitev, match="SECRET_KEY"):
        nalozi_nastavitve()


def test_pretvorba_lokalnega_casa_v_utc_poleti_in_pozimi():
    # Poleti je Ljubljana UTC+2, pozimi UTC+1.
    assert v_utc(datetime(2026, 7, 1, 9, 0)) == datetime(2026, 7, 1, 7, 0)
    assert v_utc(datetime(2026, 12, 1, 9, 0)) == datetime(2026, 12, 1, 8, 0)
    assert oblikuj(datetime(2026, 12, 1, 8, 0)) == "01. 12. 2026 09:00"


def test_preusmeritev_samo_na_lokalno_pot():
    assert je_lokalna_pot("/rezervacije/moje")
    assert not je_lokalna_pot("https://napad.si")
    assert not je_lokalna_pot("//napad.si")
    assert not je_lokalna_pot("/\\napad.si")
    assert not je_lokalna_pot(None)
