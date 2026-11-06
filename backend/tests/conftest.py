"""Skupne nastavitve testov (pytest fixtures).

Testi, ki potrebujejo bazo, uporabljajo ločeno testno bazo solski_ikt_test
(nikoli glavne baze). Shema se na začetku testiranja ustvari na novo iz
backend/sql/*.sql, pred vsakim testom pa se tabele izpraznijo.
Če baza ni dosegljiva, se ti testi preskočijo.
"""

import contextvars
from datetime import timedelta
from pathlib import Path

import mysql.connector
import pytest
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

from app import create_app
from app.auth import Uporabnik
from app.cas import zdaj_utc
from app.config import ManjkajocaNastavitev, nalozi_nastavitve
from app.db import transakcija
from app.repositories import oprema as repo_oprema
from app.repositories import ucilnice as repo_ucilnice
from app.repositories import uporabniki as repo_uporabniki

TESTNA_BAZA = "solski_ikt_test"
MAPA_SQL = Path(__file__).resolve().parents[1] / "sql"
SKRIPTE_SHEME = ["001-schema.sql", "002-nadgradnje.sql"]
TABELE = ["obvestilo", "priponka_prijave", "komentar_prijave", "prijava_tezave",
          "rezervacija", "oprema", "ucilnica", "uporabnik"]
GESLO = "geslo1234"


def _ukazi_iz_skripte(pot):
    """Razdeli SQL skripto na posamezne ukaze (brez vrstic s komentarji)."""
    vrstice = [v for v in pot.read_text(encoding="utf-8").splitlines()
               if not v.strip().startswith("--")]
    return [u.strip() for u in "\n".join(vrstice).split(";") if u.strip()]


@pytest.fixture(scope="session")
def nastavitve_baze():
    try:
        nastavitve = nalozi_nastavitve()
    except ManjkajocaNastavitev as napaka:
        pytest.skip(f"Ni nastavitev za bazo: {napaka}")
    nastavitve["DB_NAME"] = TESTNA_BAZA

    try:
        povezava = mysql.connector.connect(
            host=nastavitve["DB_HOST"], port=nastavitve["DB_PORT"], user=nastavitve["DB_USER"],
            password=nastavitve["DB_PASSWORD"], database=TESTNA_BAZA,
        )
    except mysql.connector.Error as napaka:
        pytest.skip(f"Testna baza ni dosegljiva: {napaka}")

    # Shemo ustvarimo na novo, da testi vedno tečejo na zadnji različici.
    kazalec = povezava.cursor()
    kazalec.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tabela in TABELE:
        kazalec.execute(f"DROP TABLE IF EXISTS {tabela}")
    kazalec.execute("SET FOREIGN_KEY_CHECKS = 1")
    for skripta in SKRIPTE_SHEME:
        for ukaz in _ukazi_iz_skripte(MAPA_SQL / skripta):
            kazalec.execute(ukaz)
    kazalec.close()
    povezava.close()
    return nastavitve


@pytest.fixture
def app(nastavitve_baze, tmp_path):
    nastavitve = dict(nastavitve_baze)
    nastavitve.update({
        "TESTING": True,
        # V testih CSRF izklopimo, sicer bi morali žeton brati iz HTML.
        "WTF_CSRF_ENABLED": False,
        "PRIPONKE_MAPA": str(tmp_path / "priponke"),
        "MAIL_SERVER": "",
    })
    app = create_app(nastavitve)

    with app.app_context():
        with transakcija() as k:
            k.execute("SET FOREIGN_KEY_CHECKS = 0")
            for tabela in TABELE:
                k.execute(f"TRUNCATE TABLE {tabela}")
            k.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Vsak test teče v svojem kontekstu aplikacije (get_db, current_app).
    with app.app_context():
        yield app


class CistOdjemalec(FlaskClient):
    """Testni odjemalec, pri katerem vsaka zahteva dobi svoj kontekst aplikacije.

    Test sam teče v kontekstu aplikacije (da lahko kliče storitve). Brez tega
    bi zahteve odjemalca uporabile isti kontekst (isti g, isto povezavo in
    shranjenega prijavljenega uporabnika), kar se v pravi aplikaciji ne zgodi.
    Prazen contextvars.Context() poskrbi, da zahteva ne vidi konteksta testa.
    """

    def open(self, *args, **kwargs):
        return contextvars.Context().run(super().open, *args, **kwargs)


@pytest.fixture
def odjemalec(app):
    app.test_client_class = CistOdjemalec
    return app.test_client()


# --- Pomočniki za pripravo podatkov ------------------------------------------

def ustvari_uporabnika(vloga="ucitelj", email=None, aktiven=True, ime="Test"):
    email = email or f"{vloga}{zdaj_utc().timestamp()}@sola.si"
    with transakcija() as k:
        id_uporabnika = repo_uporabniki.ustvari(
            k, ime, vloga.capitalize(), email, generate_password_hash(GESLO), vloga
        )
        if not aktiven:
            k.execute("UPDATE uporabnik SET aktiven = FALSE WHERE id = %s", (id_uporabnika,))
        return Uporabnik(repo_uporabniki.najdi(k, id_uporabnika))


@pytest.fixture
def ucitelj(app):
    return ustvari_uporabnika("ucitelj", "ucitelj@sola.si", ime="Uroš")


@pytest.fixture
def ucitelj2(app):
    return ustvari_uporabnika("ucitelj", "ucitelj2@sola.si", ime="Maja")


@pytest.fixture
def skrbnik(app):
    return ustvari_uporabnika("ikt_skrbnik", "skrbnik@sola.si", ime="Igor")


@pytest.fixture
def skrbnik2(app):
    return ustvari_uporabnika("ikt_skrbnik", "skrbnik2@sola.si", ime="Iva")


@pytest.fixture
def admin(app):
    return ustvari_uporabnika("administrator", "admin@sola.si", ime="Ana")


@pytest.fixture
def ucilnica(app):
    with transakcija() as k:
        return repo_ucilnice.najdi(k, repo_ucilnice.ustvari(k, "12", "Računalniška učilnica", None))


@pytest.fixture
def projektor(app, ucilnica):
    with transakcija() as k:
        id_opreme = repo_oprema.ustvari(k, "Projektor 1", "INV-1", "projektor", None, "uporabna",
                                        ucilnica["id"])
        return repo_oprema.najdi(k, id_opreme)


@pytest.fixture
def jutri_ob_9():
    """Jutri ob 9.00 (UTC) – vedno v prihodnosti."""
    return (zdaj_utc() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)


def prijavi(odjemalec, email, geslo=GESLO):
    return odjemalec.post("/prijava", data={"email": email, "geslo": geslo})
