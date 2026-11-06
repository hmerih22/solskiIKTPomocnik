"""Osnovni testi ogrodja aplikacije (#7)."""

import pytest

from app import create_app
from app.config import ManjkajocaNastavitev, nalozi_nastavitve


def test_domaca_stran_se_odpre():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    odgovor = app.test_client().get("/")

    assert odgovor.status_code == 200
    assert "Šolski IKT pomočnik" in odgovor.get_data(as_text=True)


def test_manjkajoca_nastavitev_sprozi_jasno_napako(monkeypatch):
    # Prepreči branje prave datoteke .env in odstrani SECRET_KEY iz okolja.
    monkeypatch.setattr("app.config.load_dotenv", lambda: None)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ManjkajocaNastavitev, match="SECRET_KEY"):
        nalozi_nastavitve()
