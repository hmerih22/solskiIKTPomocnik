"""Testi povezave z bazo (#9). Uporabljajo testno bazo iz conftest.py."""

import pytest
from flask import Flask

from app import create_app
from app.config import ManjkajocaNastavitev
from app.db import get_db, transakcija

TESTNA_TABELA = "test_db_povezava"


@pytest.fixture
def tabela(app):
    kazalec = get_db().cursor()
    kazalec.execute(f"DROP TABLE IF EXISTS {TESTNA_TABELA}")
    kazalec.execute(f"CREATE TABLE {TESTNA_TABELA} (vrednost INT NOT NULL)")
    kazalec.close()
    yield
    kazalec = get_db().cursor()
    kazalec.execute(f"DROP TABLE IF EXISTS {TESTNA_TABELA}")
    kazalec.close()


def _stevilo_vrstic(app):
    # Nov kontekst = nova povezava, ki vidi samo potrjene podatke.
    with app.app_context():
        with transakcija() as k:
            k.execute(f"SELECT COUNT(*) AS n FROM {TESTNA_TABELA}")
            return k.fetchone()["n"]


def test_povezava_se_odpre_enkrat_na_kontekst_in_zapre(app: Flask):
    with app.app_context():
        prva = get_db()
        assert get_db() is prva
        assert prva.is_connected()
    assert not prva.is_connected()


def test_povezava_uporablja_utc_in_utf8mb4(app):
    kazalec = get_db().cursor()
    kazalec.execute("SELECT @@session.time_zone, @@character_set_connection")
    assert kazalec.fetchone() == ("+00:00", "utf8mb4")
    kazalec.close()


def test_transakcija_potrdi_spremembe(app, tabela):
    with app.app_context():
        with transakcija() as k:
            k.execute(f"INSERT INTO {TESTNA_TABELA} (vrednost) VALUES (%s)", (1,))
    assert _stevilo_vrstic(app) == 1


def test_transakcija_ob_napaki_razveljavi_spremembe(app, tabela):
    with app.app_context():
        with pytest.raises(ZeroDivisionError):
            with transakcija() as k:
                k.execute(f"INSERT INTO {TESTNA_TABELA} (vrednost) VALUES (%s)", (1,))
                1 / 0
    assert _stevilo_vrstic(app) == 0


def test_nepotrjena_sprememba_se_ob_koncu_zahteve_razveljavi(app, tabela):
    with app.app_context():
        kazalec = get_db().cursor()
        kazalec.execute(f"INSERT INTO {TESTNA_TABELA} (vrednost) VALUES (%s)", (1,))
        kazalec.close()
        # Brez commit(): close_db mora spremembo razveljaviti.
    assert _stevilo_vrstic(app) == 0


def test_manjkajoca_nastavitev_baze_sprozi_jasno_napako():
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.app_context():
        with pytest.raises(ManjkajocaNastavitev, match="DB_HOST"):
            get_db()
