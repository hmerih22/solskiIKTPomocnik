"""Skupne nastavitve testov (pytest fixtures).

Testi, ki potrebujejo bazo, uporabljajo ločeno testno bazo solski_ikt_test
(nikoli glavne baze). Shema se na začetku testiranja ustvari na novo iz
backend/sql/001-schema.sql, pred vsakim testom pa se tabele izpraznijo.
Če baza ni dosegljiva, se ti testi preskočijo.
"""

import contextvars
from pathlib import Path

import mysql.connector
import pytest
from flask.testing import FlaskClient
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import ManjkajocaNastavitev, nalozi_nastavitve
from app.db import transakcija

TESTNA_BAZA = "solski_ikt_test"
SKRIPTA_SHEME = Path(__file__).resolve().parents[1] / "sql" / "001-schema.sql"
TABELE = ["prijava_tezave", "rezervacija", "oprema", "ucilnica", "uporabnik"]
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
    for ukaz in _ukazi_iz_skripte(SKRIPTA_SHEME):
        kazalec.execute(ukaz)
    kazalec.close()
    povezava.close()
    return nastavitve


@pytest.fixture
def app(nastavitve_baze):
    nastavitve = dict(nastavitve_baze)
    nastavitve.update({
        "TESTING": True,
        # V testih CSRF izklopimo, sicer bi morali žeton brati iz HTML.
        "WTF_CSRF_ENABLED": False,
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

    Brez tega bi zahteve odjemalca delile kontekst testa (isti g in isto
    povezavo), kar se v pravi aplikaciji ne zgodi.
    """

    def open(self, *args, **kwargs):
        return contextvars.Context().run(super().open, *args, **kwargs)


@pytest.fixture
def odjemalec(app):
    app.test_client_class = CistOdjemalec
    return app.test_client()


# --- Pomočniki za pripravo podatkov ------------------------------------------

def ustvari_uporabnika(email, vloga="ucitelj", aktiven=True, ime="Test"):
    """Vstavi uporabnika neposredno v bazo in vrne njegov id."""
    with transakcija() as k:
        k.execute(
            "INSERT INTO uporabnik (ime, priimek, email, geslo_hash, vloga, aktiven)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (ime, "Testni", email, generate_password_hash(GESLO), vloga, aktiven),
        )
        return k.lastrowid


def spremeni_uporabnika(id_uporabnika, **stolpci):
    """Spremeni stolpce uporabnika (npr. vloga='ucitelj', aktiven=False)."""
    nastavi = ", ".join(f"{ime} = %s" for ime in stolpci)
    with transakcija() as k:
        k.execute(f"UPDATE uporabnik SET {nastavi} WHERE id = %s", (*stolpci.values(), id_uporabnika))


def prijavi(odjemalec, email, geslo=GESLO):
    return odjemalec.post("/prijava", data={"email": email, "geslo": geslo})


def ustvari_ucilnico(oznaka="12", naziv="Učilnica 12"):
    with transakcija() as k:
        k.execute("INSERT INTO ucilnica (oznaka, naziv) VALUES (%s, %s)", (oznaka, naziv))
        return k.lastrowid


def ustvari_opremo(inventarna="INV-1", naziv="Projektor 1", stanje="uporabna", ucilnica_id=None):
    if ucilnica_id is None:
        ucilnica_id = ustvari_ucilnico(oznaka=f"U-{inventarna}")
    with transakcija() as k:
        k.execute(
            "INSERT INTO oprema (naziv, inventarna_stevilka, vrsta, stanje, ucilnica_id)"
            " VALUES (%s, %s, 'projektor', %s, %s)",
            (naziv, inventarna, stanje, ucilnica_id),
        )
        return k.lastrowid


def ustvari_prevzeto_prijavo(prijavitelj_id, skrbnik_id, ucilnica_id):
    """Prijava v obravnavi, ki jo je prevzel podani skrbnik."""
    with transakcija() as k:
        k.execute(
            "INSERT INTO prijava_tezave (prijavitelj_id, ucilnica_id, naslov, opis, status,"
            " skrbnik_id, prevzeta_ob)"
            " VALUES (%s, %s, 'Ne dela', 'Opis', 'v_obravnavi', %s, UTC_TIMESTAMP())",
            (prijavitelj_id, ucilnica_id, skrbnik_id),
        )
        return k.lastrowid


def stevilo_vrstic(tabela):
    with transakcija() as k:
        k.execute(f"SELECT COUNT(*) AS n FROM {tabela}")
        return k.fetchone()["n"]


def ustvari_rezervacijo(uporabnik_id, oprema_id, zacetek, konec, preklicana=False):
    """Vstavi rezervacijo neposredno v bazo (časi v UTC) in vrne njen id."""
    with transakcija() as k:
        if preklicana:
            k.execute(
                "INSERT INTO rezervacija (uporabnik_id, oprema_id, zacetek, konec, status,"
                " preklicana_ob, preklical_id) VALUES (%s, %s, %s, %s, 'preklicana',"
                " UTC_TIMESTAMP(), %s)",
                (uporabnik_id, oprema_id, zacetek, konec, uporabnik_id),
            )
        else:
            k.execute(
                "INSERT INTO rezervacija (uporabnik_id, oprema_id, zacetek, konec)"
                " VALUES (%s, %s, %s, %s)",
                (uporabnik_id, oprema_id, zacetek, konec),
            )
        return k.lastrowid


def jutri_ob(ura, minuta=0):
    """Jutrišnji dan ob podani uri (UTC, naiven datetime kot v bazi)."""
    from datetime import timedelta

    from app.cas import zdaj_utc

    jutri = zdaj_utc() + timedelta(days=1)
    return jutri.replace(hour=ura, minute=minuta, second=0, microsecond=0)


def ustvari_prijavo(prijavitelj_id, oprema_id=None, ucilnica_id=None, naslov="Ne dela"):
    """Nova prijava (status 'nova', brez skrbnika). Vrne id."""
    with transakcija() as k:
        k.execute(
            "INSERT INTO prijava_tezave (prijavitelj_id, oprema_id, ucilnica_id, naslov, opis)"
            " VALUES (%s, %s, %s, %s, 'Opis težave')",
            (prijavitelj_id, oprema_id, ucilnica_id, naslov),
        )
        return k.lastrowid


def preberi_prijavo(id_prijave):
    with transakcija() as k:
        k.execute("SELECT * FROM prijava_tezave WHERE id = %s", (id_prijave,))
        return k.fetchone()
