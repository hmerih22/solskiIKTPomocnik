"""Testi, ki ne potrebujejo baze: nastavitve in vloge."""

import pytest

from app import create_app
from app.auth import Uporabnik
from app.config import ManjkajocaNastavitev, nalozi_nastavitve


def test_aplikacija_se_ustvari():
    app = create_app({"SECRET_KEY": "test", "TESTING": True})
    odgovor = app.test_client().get("/zdravje")
    assert odgovor.status_code == 200
    assert odgovor.json == {"stanje": "ok"}


def test_manjkajoce_nastavitve_sprozijo_jasno_napako(monkeypatch):
    monkeypatch.setattr("app.config.load_dotenv", lambda: None)
    for ime in ["SECRET_KEY", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]:
        monkeypatch.delenv(ime, raising=False)
    with pytest.raises(ManjkajocaNastavitev, match="SECRET_KEY"):
        nalozi_nastavitve()


def _uporabnik(vloga):
    return Uporabnik({"id": 1, "ime": "A", "priimek": "B", "email": "a@sola.si",
                      "vloga": vloga, "aktiven": True})


@pytest.mark.parametrize("vloga, skrbnik, administrator", [
    ("ucitelj", False, False),
    ("ikt_skrbnik", True, False),
    ("administrator", True, True),
])
def test_dedovanje_vlog(vloga, skrbnik, administrator):
    u = _uporabnik(vloga)
    assert u.ima_vlogo("ucitelj")
    assert u.je_skrbnik is skrbnik
    assert u.je_administrator is administrator
